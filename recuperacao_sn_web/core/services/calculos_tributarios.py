from MODULES.config import faixas_anexo_I, reparticao_tributos_anexo_I
from MODULES.config import reparticao_tributos_anexo_I
from MODULES.relatorios import gerar_relatorio_fiscal
from MODULES.sped import gerar_arquivo_sped
from MODULES.extracao import extrair_dados_pgdas
from MODULES.gerar_planilha_segregacao import formatar_planilha
import os 
import pandas as pd

diretorio_atual = os.getcwd()
diretorio_pgdas = os.path.join(diretorio_atual, 'PGDAS')

def identificar_faixa_simples_nacional(rbt12):
    # Identificar a faixa com base na RBT12
    for faixa in faixas_anexo_I:
        if rbt12 <= faixa["limite_superior"]:
            aliquota_nominal = faixa["aliquota"]
            deducao = faixa["deducao"]
            faixa_numero = faixa["faixa"]  # Pegando o número da faixa
            return aliquota_nominal, deducao, faixa_numero
    else:
        print("Faturamento excede o limite do Simples Nacional.")
        # Se o faturamento ultrapassar 4,8 milhões, a empresa não se enquadra no Simples Nacional
        return "Faturamento excede o limite do Simples Nacional."
    
def calcular_aliquotas_tributos(faixa_numero, aliquota_efetiva):
    # Buscar a repartição de tributos correspondente na tabela de repartição
        for faixa in reparticao_tributos_anexo_I:
            if faixa["faixa"] == faixa_numero:
                aliquota_icms = aliquota_efetiva * (faixa["ICMS"] / 100)
                aliquota_pis = aliquota_efetiva * (faixa["PIS/Pasep"] / 100)
                aliquota_cofins = aliquota_efetiva * (faixa["Cofins"] / 100)
                aliquota_irpj = aliquota_efetiva * (faixa["IRPJ"] / 100)
                aliquota_csll = aliquota_efetiva * (faixa["CSLL"] / 100)
                aliquota_cpp = aliquota_efetiva * (faixa["CPP"] / 100)
                
                aliquotas = {
                    'aliquota_icms' : aliquota_icms,
                    'aliquota_pis' : aliquota_pis,
                    'aliquota_cofins' : aliquota_cofins,
                    'aliquota_irpj' : aliquota_irpj,
                    'aliquota_csll' : aliquota_csll,
                    'aliquota_cpp' : aliquota_cpp,
                }
                return aliquotas

def calcular_simples_nacional_anexo_I(dados_por_periodo):
    arquivos_diretorio_pgdas = [arquivo for arquivo in os.listdir(diretorio_pgdas) if arquivo.endswith('.pdf')]

    consolidado_total = []

    for pgdas in arquivos_diretorio_pgdas:
        dados_pgdas = extrair_dados_pgdas(diretorio_pgdas, pgdas)

        consolidado_pgdas = {
            'ARQUIVO PGDAS': pgdas,
            'PERÍODO': '',
            'VALORES PGDAS ORIGINAL': 0,
            'PIS PGDAS ORIGINAL': 0,
            'COFINS PGDAS ORIGINAL': 0,
            'ICMS PGDAS ORIGINAL': 0,
            'VALOR PGDAS RETIFICADO': 0,
            'PIS PGDAS RETIFICADO': 0,
            'COFINS PGDAS RETIFICADO': 0,
            'ICMS PGDAS RETIFICADO': 0,
            'CRÉDITO APÓS REAPURADO': 0
        }

        for cnpj, valores in dados_pgdas.items():

            diferenca_notas_pgdas = 0 
            periodo = dados_pgdas[cnpj]['periodo']
            
            valor_total_receita_nf  = dados_por_periodo[periodo][cnpj]['valor_total_nfe']
            valor_rbt12 = dados_pgdas[cnpj]['valor_rbt12']
            
            aliquota_nominal, deducao, faixa_numero = identificar_faixa_simples_nacional(valor_rbt12)
            
            aliquota_efetiva = (valor_rbt12 * aliquota_nominal - deducao) / valor_rbt12
            aliquotas = calcular_aliquotas_tributos(faixa_numero, aliquota_efetiva)
            
            aliquota_isenta_de_icms = aliquota_efetiva - aliquotas['aliquota_icms']
            aliquota_imposto_irrecuperavel_irpj_csll_cpp = aliquotas['aliquota_irpj'] + aliquotas['aliquota_csll'] + aliquotas['aliquota_cpp']

            valor_imposto_pagar_cheio = aliquota_efetiva * dados_pgdas[cnpj]['receita_bruta']
            valor_imposto_irrecuperavel_irpj_csll_cpp =  aliquota_imposto_irrecuperavel_irpj_csll_cpp * dados_pgdas[cnpj]['receita_bruta']
           
            if dados_pgdas[cnpj]['receita_bruta'] > valor_total_receita_nf:
                diferenca_notas_pgdas = dados_pgdas[cnpj]['receita_bruta'] - valor_total_receita_nf
                try:
                    dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['102'] += diferenca_notas_pgdas
                except :
                    dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['500'] = diferenca_notas_pgdas
            
            elif dados_pgdas[cnpj]['receita_bruta'] < valor_total_receita_nf:
                diferenca_notas_pgdas = valor_total_receita_nf - dados_pgdas[cnpj]['receita_bruta']
                if dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['102'] >= diferenca_notas_pgdas:
                    dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['102'] -= diferenca_notas_pgdas
                else:
                    valor_para_reduzir_do_st = diferenca_notas_pgdas - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['102']
                    dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['102'] = 0
                    dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos']['500'] -= valor_para_reduzir_do_st
                                
            icms_imune_ou_isento = dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('300 ou 400', 0) * aliquota_isenta_de_icms
            icms_tributado = dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('102', 0) * aliquota_efetiva
            icms_ST_e_pis_cofins_monofasico = dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0) * aliquota_imposto_irrecuperavel_irpj_csll_cpp
            icms_ST = (dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('500', 0) - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0)) * aliquota_isenta_de_icms
            das_total = icms_imune_ou_isento + icms_tributado + icms_ST_e_pis_cofins_monofasico + icms_ST

            valor_ICMS_novo = icms_tributado * (reparticao_tributos_anexo_I[faixa_numero-1]["ICMS"]/100)
            valor_PIS_novo = (dados_pgdas[cnpj]['receita_bruta'] - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0) - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('05 - Operação tributável por Substituição Tributária', 0)) * aliquotas['aliquota_pis']
            valor_COFINS_novo = (dados_pgdas[cnpj]['receita_bruta'] - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0) - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('05 - Operação tributável por Substituição Tributária', 0)) * aliquotas['aliquota_cofins']
            credito_total_apurado_no_mes = float(dados_pgdas[cnpj]['valor_DAS_pago_original'].replace('.','').replace(',','.')) - float(das_total)
            
            relatorio_planilha.append([
                periodo,
                float(dados_pgdas[cnpj]['valor_DAS_pago_original'].replace('.','').replace(',','.')),
                float(dados_pgdas[cnpj]['valor_PIS_pago_original'].replace('.','').replace(',','.')),
                float(dados_pgdas[cnpj]['valor_COFINS_pago_original'].replace('.','').replace(',','.')),
                float(dados_pgdas[cnpj]['valor_ICMS_pago_original'].replace('.','').replace(',','.')),
                float(round(das_total, 2)),  # Formata com duas casas decimais
                float(valor_PIS_novo),
                float(valor_COFINS_novo),
                float(valor_ICMS_novo),
                float(credito_total_apurado_no_mes)
            ])
            
            dados_relatorio = {
                "dados_pgdas": dados_pgdas,
                "cnpj": cnpj,
                "periodo": periodo,
                "valor_rbt12": valor_rbt12,
                "valor_imposto_pagar_cheio": valor_imposto_pagar_cheio,
                "valor_imposto_irrecuperavel_irpj_csll_cpp": valor_imposto_irrecuperavel_irpj_csll_cpp,
                "valor_total_receita_nf": valor_total_receita_nf,
                "diferenca_notas_pgdas": diferenca_notas_pgdas,
                "aliquota_efetiva": aliquota_efetiva,
                "aliquotas": aliquotas,
                "aliquota_isenta_de_icms": aliquota_isenta_de_icms,
                "dados_por_periodo": dados_por_periodo,
                "valor_ICMS_novo": valor_ICMS_novo,
                "valor_COFINS_novo": valor_COFINS_novo,
                "valor_PIS_novo": valor_PIS_novo,
                "das_total": das_total,
                "icms_imune_ou_isento": icms_imune_ou_isento,
                "icms_tributado": icms_tributado,
                "icms_ST_e_pis_cofins_monofasico": icms_ST_e_pis_cofins_monofasico,
                "icms_ST": icms_ST,
            }

            gerar_relatorio_fiscal(dados_relatorio)
            
            periodo = dados_pgdas[cnpj]['periodo']
            consolidado_pgdas['PERÍODO'] = periodo
            consolidado_pgdas['VALORES PGDAS ORIGINAL'] += float(dados_pgdas[cnpj]['valor_DAS_pago_original'].replace('.', '').replace(',', '.'))
            consolidado_pgdas['PIS PGDAS ORIGINAL'] += float(dados_pgdas[cnpj]['valor_PIS_pago_original'].replace('.', '').replace(',', '.'))
            consolidado_pgdas['COFINS PGDAS ORIGINAL'] += float(dados_pgdas[cnpj]['valor_COFINS_pago_original'].replace('.', '').replace(',', '.'))
            consolidado_pgdas['ICMS PGDAS ORIGINAL'] += float(dados_pgdas[cnpj]['valor_ICMS_pago_original'].replace('.', '').replace(',', '.'))
            # Adiciona valores calculados
            consolidado_pgdas['VALOR PGDAS RETIFICADO'] += round(das_total, 2)
            consolidado_pgdas['PIS PGDAS RETIFICADO'] += valor_PIS_novo
            consolidado_pgdas['COFINS PGDAS RETIFICADO'] += valor_COFINS_novo
            consolidado_pgdas['ICMS PGDAS RETIFICADO'] += valor_ICMS_novo
            consolidado_pgdas['CRÉDITO APÓS REAPURADO'] += credito_total_apurado_no_mes
            
        # Adiciona os dados consolidados deste PGDAS ao DataFrame total
        consolidado_total.append(consolidado_pgdas)
        
    gerar_arquivo_sped(dados_por_periodo)

    # Converte o consolidado total em DataFrame e salva em uma única planilha
    df_consolidado_total = pd.DataFrame(consolidado_total)
    df_consolidado_total.to_excel('relatorio_consolidado_todos_pgdas.xlsx', index=False)
    formatar_planilha('relatorio_consolidado_todos_pgdas.xlsx')