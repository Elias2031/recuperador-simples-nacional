from decimal import Decimal
from django.db.models import Sum
from core.models import (
    Empresa,
    Competencia,
    ApuracaoFiscal,
    NotaFiscal,
    ItemNotaFiscal,
    PgdasValorDeclarado
)
from core.services.config import faixas_anexo_I, reparticao_tributos_anexo_I

# Função utilitária para converter Decimals em floats
def serializar_decimais(dicionario):
    """
    Converte todos os Decimals do dicionário para float.
    """
    resultado = {}
    for chave, valor in dicionario.items():
        if isinstance(valor, Decimal):
            resultado[chave] = float(valor)  # ou str(valor) se preferir manter como texto
        else:
            resultado[chave] = valor
    return resultado

# Determina a faixa do Simples Nacional com base no RBT12
def identificar_faixa_simples_nacional(rbt12):
    for faixa in faixas_anexo_I:
        if rbt12 <= faixa["limite_superior"]:
            return faixa["aliquota"], faixa["deducao"], faixa["faixa"], faixa['limite_superior']
    return None, None, None, None

# Calcula a alíquota efetiva de cada tributo com base na faixa
def calcular_aliquotas_tributos(faixa_numero, aliquota_efetiva):
    aliquota_efetiva = Decimal(str(aliquota_efetiva))  # Garante precisão

    for faixa in reparticao_tributos_anexo_I:
        if faixa["faixa"] == faixa_numero:
            return {
                'aliquota_icms': aliquota_efetiva * Decimal(str(faixa["ICMS"])) / Decimal('100'),
                'aliquota_pis': aliquota_efetiva * Decimal(str(faixa["PIS/Pasep"])) / Decimal('100'),
                'aliquota_cofins': aliquota_efetiva * Decimal(str(faixa["Cofins"])) / Decimal('100'),
                'aliquota_irpj': aliquota_efetiva * Decimal(str(faixa["IRPJ"])) / Decimal('100'),
                'aliquota_csll': aliquota_efetiva * Decimal(str(faixa["CSLL"])) / Decimal('100'),
                'aliquota_cpp': aliquota_efetiva * Decimal(str(faixa["CPP"])) / Decimal('100'),
            }
    return {}

# Função principal de apuração do Simples Nacional
def apurar_empresa_simples(empresa_id, competencia_id):
    limite_simples = 4800000
    ultrapassa_limite = False
    empresa = Empresa.objects.get(id=empresa_id)
    competencia = Competencia.objects.get(id=competencia_id)

    pgdas = PgdasValorDeclarado.objects.filter(empresa=empresa, competencia=competencia).first()
    if not pgdas:
        print("PGDAS não encontrado para a empresa/competência.")
        return

    # Filtros de notas e itens
    itens = ItemNotaFiscal.objects.filter(
        nota__empresa=empresa,
        nota__apuracao__competencia=competencia,
        nota__tipo='saida',
        nota__status='AUTORIZADA'
    )

    notas = NotaFiscal.objects.filter(
        empresa=empresa,
        data_emissao__month=competencia.mes,
        data_emissao__year=competencia.ano,
        status='AUTORIZADA',
        tipo='saida'
    )

    # Valores base
    rbt12 = pgdas.valor_rbt12 or Decimal('0')
    receita_bruta = pgdas.receita_bruta or Decimal('0')

    if rbt12 == 0:
        print("RBT12 igual a 0, não é possível calcular alíquota efetiva.")
        return

    # Inicialização das bases segregadas
    base_icms_imune_ou_isento = Decimal('0')
    base_icms_tributado = Decimal('0')
    base_icms_ST_e_pis_cofins_monofasico = Decimal('0')
    base_icms_ST = Decimal('0')

    # Segregação das receitas com base nas CSTs
    try:
        for item in itens:
            valor = item.base_calculo or Decimal('0')

            cst_ICMS = (item.ncm_analisado.cst_icms or '').strip()
            opcoes_cst_ICMS = [c.strip() for c in cst_ICMS.split('ou') if c.strip()]

            cst_PIS_COFINS = (item.ncm_analisado.cst_simples_pis_cofins or '').strip()
            opcoes_cst_PIS_COFINS = [c.strip() for c in cst_PIS_COFINS.split('ou') if c.strip()]

            if any(c in ['300', '400', '103', '203'] for c in opcoes_cst_ICMS):
                base_icms_imune_ou_isento += valor

            elif any(c in ['101', '102', '000', '00'] for c in opcoes_cst_ICMS):
                base_icms_tributado += valor

            elif cst_PIS_COFINS != '49 - Outras Operações de Saída ou 99 - Outras Operações':
                base_icms_ST_e_pis_cofins_monofasico += valor

            elif any(c in ['201', '202', '500'] for c in opcoes_cst_ICMS):
                base_icms_ST += valor
    except Exception as e:
        print(e)

    # Determinação da alíquota efetiva
    aliquota_nominal, deducao, faixa_numero, limite_faixa = identificar_faixa_simples_nacional(rbt12)
    if not aliquota_nominal:
        print("Empresa excede o limite do Simples Nacional.")
        return
    
    if rbt12 > limite_simples:
        ultrapassa_limite = True

    aliquota_nominal = Decimal(str(aliquota_nominal))
    deducao = Decimal(str(deducao))
    aliquota_efetiva = (rbt12 * aliquota_nominal - deducao) / rbt12
    aliquotas = calcular_aliquotas_tributos(faixa_numero, aliquota_efetiva)

    # Cálculos de ICMS e tributos
    aliquota_isenta_de_icms = aliquota_efetiva - aliquotas['aliquota_icms']
    aliquota_irrecuperavel = (
        aliquotas['aliquota_irpj'] +
        aliquotas['aliquota_csll'] +
        aliquotas['aliquota_cpp']
    )

    icms_imune_ou_isento = base_icms_imune_ou_isento * aliquota_isenta_de_icms
    icms_tributado = base_icms_tributado * aliquota_efetiva
    icms_ST_e_pis_cofins_monofasico = base_icms_ST_e_pis_cofins_monofasico * aliquota_irrecuperavel
    icms_ST = base_icms_ST * aliquota_isenta_de_icms

    # Bloco sem ST
    base_sem_st = base_icms_imune_ou_isento + base_icms_tributado
    bloco_sem_st = {
        'base': base_sem_st,
        'irpj': base_sem_st * aliquotas['aliquota_irpj'],
        'csll': base_sem_st * aliquotas['aliquota_csll'],
        'cofins': base_sem_st * aliquotas['aliquota_cofins'],
        'pis': base_sem_st * aliquotas['aliquota_pis'],
        'cpp': base_sem_st * aliquotas['aliquota_cpp'],
        'icms': base_sem_st * aliquotas['aliquota_icms'],
        'parcela_1': icms_tributado,
        'parcela_2': icms_imune_ou_isento,
    }
    bloco_sem_st['total'] = (
        bloco_sem_st['irpj'] +
        bloco_sem_st['csll'] +
        bloco_sem_st['cofins'] +
        bloco_sem_st['pis'] +
        bloco_sem_st['cpp'] +
        bloco_sem_st['icms']
    )

    # Bloco com ST
    base_com_st = base_icms_ST + base_icms_ST_e_pis_cofins_monofasico
    bloco_com_st = {
        'base': base_com_st,
        'irpj': base_com_st * aliquotas['aliquota_irpj'],
        'csll': base_com_st * aliquotas['aliquota_csll'],
        'cofins': base_com_st * aliquotas['aliquota_cofins'],
        'pis': base_com_st * aliquotas['aliquota_pis'],
        'cpp': base_com_st * aliquotas['aliquota_cpp'],
        'icms': 0,
        'parcela_1': icms_tributado,
        'parcela_2': icms_imune_ou_isento,
    }
    bloco_com_st['total'] = (
        bloco_com_st['irpj'] +
        bloco_com_st['csll'] +
        bloco_com_st['cofins'] +
        bloco_com_st['pis'] +
        bloco_com_st['cpp'] +
        bloco_com_st['icms']
    )
    
    # Bloco total - soma dos valores de sem ST e com ST
    bloco_total_tributos = {
        'base': bloco_sem_st['base'] + bloco_com_st['base'],
        'irpj': bloco_sem_st['irpj'] + bloco_com_st['irpj'],
        'csll': bloco_sem_st['csll'] + bloco_com_st['csll'],
        'cofins': bloco_sem_st['cofins'] + bloco_com_st['cofins'],
        'pis': bloco_sem_st['pis'] + bloco_com_st['pis'],
        'cpp': bloco_sem_st['cpp'] + bloco_com_st['cpp'],
        'icms': bloco_sem_st['icms'] + bloco_com_st['icms'],
        'parcela_1': bloco_sem_st['parcela_1'] + bloco_com_st['parcela_1'],
        'parcela_2': bloco_sem_st['parcela_2'] + bloco_com_st['parcela_2'],
    }

    # Total dos tributos (soma dos tributos sem considerar as parcelas)
    bloco_total_tributos['total'] = (
        bloco_total_tributos['irpj'] +
        bloco_total_tributos['csll'] +
        bloco_total_tributos['cofins'] +
        bloco_total_tributos['pis'] +
        bloco_total_tributos['cpp'] +
        bloco_total_tributos['icms']
    )

    # Cálculos finais de valores e créditos
    # das_total = icms_imune_ou_isento + icms_tributado + icms_ST_e_pis_cofins_monofasico + icms_ST
    # das_total = icms_imune_ou_isento + icms_tributado + icms_ST_e_pis_cofins_monofasico + icms_ST
    valor_total_nfe = notas.aggregate(Sum('valor_total'))['valor_total__sum'] or Decimal('0')
    valor_imposto_pagar_cheio = receita_bruta * aliquota_efetiva
    valor_irrecuperavel = receita_bruta * aliquota_irrecuperavel

    valor_PIS_novo = receita_bruta * aliquotas['aliquota_pis']
    valor_COFINS_novo = receita_bruta * aliquotas['aliquota_cofins']
    valor_ICMS_novo = base_icms_tributado * aliquotas['aliquota_icms']

    imcs_recuperado = pgdas.valor_ICMS_pago_original - valor_ICMS_novo
    pis_recuperado = pgdas.valor_PIS_pago_original - valor_PIS_novo
    cofins_recuperado = pgdas.valor_COFINS_pago_original - valor_COFINS_novo
    credito_total_apurado = pgdas.valor_DAS_pago_original - bloco_total_tributos['total']

    # Criação ou atualização da apuração fiscal
    apuracao, _ = ApuracaoFiscal.objects.get_or_create(empresa=empresa, competencia=competencia)

    apuracao.valor_total_nfe = valor_total_nfe
    apuracao.valor_das_teorico = bloco_total_tributos['total']
    apuracao.valor_das_pago = pgdas.valor_DAS_pago_original
    apuracao.valor_imposto_cheio = valor_imposto_pagar_cheio
    apuracao.valor_irrecuperavel = valor_irrecuperavel
    apuracao.valor_pis_novo = valor_PIS_novo
    apuracao.valor_cofins_novo = valor_COFINS_novo
    apuracao.valor_icms_novo = valor_ICMS_novo
    apuracao.credito_total_apurado = credito_total_apurado

    # Bases segregadas
    apuracao.base_icms_imune_ou_isento = base_icms_imune_ou_isento
    apuracao.base_icms_tributado = base_icms_tributado
    apuracao.base_icms_ST_e_monofasico = base_icms_ST_e_pis_cofins_monofasico
    apuracao.base_icms_ST = base_icms_ST

    # Valores por segmento
    apuracao.icms_imune_ou_isento = icms_imune_ou_isento
    apuracao.icms_tributado = icms_tributado
    apuracao.icms_ST_e_pis_cofins_monofasico = icms_ST_e_pis_cofins_monofasico
    apuracao.icms_ST = icms_ST

    # Alíquotas em porcentagem
    apuracao.aliquota_efetiva = aliquota_efetiva * 100
    apuracao.aliquota_icms = aliquotas['aliquota_icms'] * 100
    apuracao.aliquota_pis = aliquotas['aliquota_pis'] * 100
    apuracao.aliquota_cofins = aliquotas['aliquota_cofins'] * 100
    apuracao.aliquota_irpj = aliquotas['aliquota_irpj'] * 100
    apuracao.aliquota_csll = aliquotas['aliquota_csll'] * 100
    apuracao.aliquota_cpp = aliquotas['aliquota_cpp'] * 100

    # Créditos recuperados
    apuracao.icms_recuperado = imcs_recuperado
    apuracao.pis_recuperado = pis_recuperado
    apuracao.cofins_recuperado = cofins_recuperado

    # Blocos detalhados
    apuracao.bloco_sem_st = serializar_decimais(bloco_sem_st)
    apuracao.bloco_com_st = serializar_decimais(bloco_com_st)
    apuracao.bloco_total_tributos = serializar_decimais(bloco_total_tributos)
    
    apuracao.faixa = faixa_numero
    apuracao.limite_superior_faixa = limite_faixa
    apuracao.aliquota_faixa = aliquota_nominal
    apuracao.deducao_faixa = deducao
    apuracao.ultrapassa_limite = ultrapassa_limite

    apuracao.save()
