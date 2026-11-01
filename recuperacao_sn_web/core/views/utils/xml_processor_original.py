import xml.etree.ElementTree as ET
from core.services.extracao import (
   extrair_valores_notas,
)

from core.services.processar_notas_cte import processar_cte_xml 
from core.models import (
    Empresa, NotaFiscal, ItemNotaFiscal,
    Participante, NotaParticipante,
    UploadLote, ApuracaoFiscal, Competencia, NcmUnico
)
from decimal import Decimal


def nota_foi_cancelada(root):
    for evento in root.findall('.//{*}evento'):
        tp_evento = evento.find('.//{*}tpEvento')
        if tp_evento is not None and tp_evento.text == '110111':
            return True
    return False

def processar_xml(xml_file, nome_arquivo, usuario, empresa_ativa, resultado):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {'ns': 'http://www.portalfiscal.inf.br/nfe'}

    # Se for CT-e, redireciona para o processador específico
    if 'procCTe' in root.tag or 'cteProc' in root.tag:
        processar_cte_xml(xml_file, nome_arquivo, usuario, empresa_ativa, resultado)
        return

    ide = root.find('.//ns:ide', ns)
    emit = root.find('.//ns:emit', ns)
    dest = root.find('.//ns:dest', ns)
    total = root.find('.//ns:ICMSTot', ns)
    infNFe = root.find('.//ns:infNFe', ns)

    chave = infNFe.attrib.get('Id', '').replace('NFe', '')
    if NotaFiscal.objects.filter(chave=chave).exists():
        resultado.append(f"Ignorado: nota {chave} já foi processada.")
        return

    numero = extrair_valores_notas(ide, 'nNF', '')
    serie = extrair_valores_notas(ide, 'serie', '')
    data_emissao = extrair_valores_notas(ide, 'dhEmi', '')[:10]
    tipo = extrair_valores_notas(ide, 'tpNF', '')
    tipo_str = 'saida' if tipo == '1' else 'entrada'
    valor_total = extrair_valores_notas(total, 'vNF', '0.00')

    status = 'CANCELADA' if nota_foi_cancelada(root) else 'AUTORIZADA'

    ano = int(data_emissao[:4])
    mes = int(data_emissao[5:7])
    competencia, _ = Competencia.objects.get_or_create(ano=ano, mes=mes)

    cnpj_emitente = extrair_valores_notas(emit, 'CNPJ', '').zfill(14)
    cnpj_destinatario = extrair_valores_notas(dest, 'CNPJ', '').zfill(14)

    if empresa_ativa.cnpj not in [cnpj_emitente, cnpj_destinatario]:
        resultado.append(f"Rejeitado: nota não pertence à empresa ativa ({empresa_ativa.razao_social})")
        return

    tipo_str = 'saida' if empresa_ativa.cnpj == cnpj_emitente else 'entrada'
    apuracao, _ = ApuracaoFiscal.objects.get_or_create(empresa=empresa_ativa, competencia=competencia)

    nota = NotaFiscal.objects.create(
        empresa=empresa_ativa,
        apuracao=apuracao,
        numero=numero,
        serie=serie,
        data_emissao=data_emissao,
        valor_total=valor_total,
        tipo=tipo_str,
        chave=chave,
        status=status,
        arquivo_xml=xml_file
    )

    for xml_elemento, papel in [(emit, 'emitente'), (dest, 'destinatario')]:
        cnpj_p = extrair_valores_notas(xml_elemento, 'CNPJ').zfill(14)
        nome_p = extrair_valores_notas(xml_elemento, 'xNome', 'Desconhecido')
        participante, _ = Participante.objects.get_or_create(cnpj=cnpj_p, defaults={'nome': nome_p})
        NotaParticipante.objects.get_or_create(nota=nota, participante=participante, tipo=papel)


    for det in root.findall('.//ns:det', ns):
        prod = det.find('ns:prod', ns)
        imposto = det.find('ns:imposto', ns)

        def get(tag): return extrair_valores_notas(prod, tag)
        def get_decimal(tag, default='0.00'): return Decimal(extrair_valores_notas(prod, tag, default).replace(',', '.'))

        codigo_produto = get('cProd')
        descricao = get('xProd')
        ean = get('cEAN')
        ean_trib = get('cEANTrib')
        unidade = get('uCom')
        unidade_trib = get('uTrib')
        quantidade = get_decimal('qCom')
        quantidade_trib = get_decimal('qTrib')
        vUnCom = get_decimal('vUnCom')
        vUnTrib = get_decimal('vUnTrib')
        valor_produto = get_decimal('vProd')
        ncm = get('NCM')
        cest = get('CEST')
        cfop = get('CFOP')
        vTotTrib = Decimal(extrair_valores_notas(imposto, 'vTotTrib', '0').replace(',', '.'))
        v_desc = get_decimal('vDesc')
        v_frete = get_decimal('vFrete')
        v_outro = get_decimal('vOutro')

        icms = imposto.find('.//ns:ICMS', ns)
        icms_cst = origem = icms_mod_bc = ''
        icms_vbc = icms_picms = icms_vicms = aliq_mva = bc_icms_st = aliq_icms_st = valor_icms_st = Decimal('0.00')

        if icms is not None and len(icms):
            icms_sn = list(icms)[0]
            icms_cst = extrair_valores_notas(icms_sn, 'CSOSN') or extrair_valores_notas(icms_sn, 'CST')
            origem = extrair_valores_notas(icms_sn, 'orig')
            icms_mod_bc = extrair_valores_notas(icms_sn, 'modBC')
            icms_vbc = Decimal(extrair_valores_notas(icms_sn, 'vBC', '0').replace(',', '.'))
            icms_picms = Decimal(extrair_valores_notas(icms_sn, 'pICMS', '0').replace(',', '.'))
            icms_vicms = Decimal(extrair_valores_notas(icms_sn, 'vICMS', '0').replace(',', '.'))
            aliq_mva = Decimal(extrair_valores_notas(icms_sn, 'pMVAST', '0').replace(',', '.'))
            bc_icms_st = Decimal(extrair_valores_notas(icms_sn, 'vBCST', '0').replace(',', '.'))
            aliq_icms_st = Decimal(extrair_valores_notas(icms_sn, 'pICMSST', '0').replace(',', '.'))
            valor_icms_st = Decimal(extrair_valores_notas(icms_sn, 'vICMSST', '0').replace(',', '.'))

        pis = imposto.find('./ns:PIS', ns)
        pis_cst = pis_vbc = pis_ppis = pis_vpis = Decimal('0.00')
        if pis is not None and len(pis):
            pis_sub = list(pis)[0]
            pis_cst = extrair_valores_notas(pis_sub, 'CST', '99')
            pis_vbc = Decimal(extrair_valores_notas(pis_sub, 'vBC', '0').replace(',', '.'))
            pis_ppis = Decimal(extrair_valores_notas(pis_sub, 'pPIS', '0').replace(',', '.'))
            pis_vpis = Decimal(extrair_valores_notas(pis_sub, 'vPIS', '0').replace(',', '.'))

        cofins = imposto.find('./ns:COFINS', ns)
        cofins_cst = cofins_vbc = cofins_pcofins = cofins_vcofins = Decimal('0.00')
        if cofins is not None and len(cofins):
            cofins_sub = list(cofins)[0]
            cofins_cst = extrair_valores_notas(cofins_sub, 'CST', '01')
            cofins_vbc = Decimal(extrair_valores_notas(cofins_sub, 'vBC', '0').replace(',', '.'))
            cofins_pcofins = Decimal(extrair_valores_notas(cofins_sub, 'pCOFINS', '0').replace(',', '.'))
            cofins_vcofins = Decimal(extrair_valores_notas(cofins_sub, 'vCOFINS', '0').replace(',', '.'))

        valor_base = valor_produto - v_desc + v_frete + v_outro
        
        item = ItemNotaFiscal.objects.create(
            nota=nota,
            codigo_produto=codigo_produto,
            descricao=descricao,
            ean=ean,
            ean_tributavel=ean_trib,
            unidade=unidade,
            unidade_tributavel=unidade_trib,
            quantidade=quantidade,
            quantidade_tributavel=quantidade_trib,
            valor_unitario=vUnCom,
            valor_unitario_tributavel=vUnTrib,
            valor_produto=valor_produto,
            ncm=ncm,
            cest=cest,
            cfop=cfop,
            vTotTrib=vTotTrib,
            cst_original=icms_cst,
            origem=origem,
            icms_cst=icms_cst,
            icms_mod_bc=icms_mod_bc,
            icms_vbc=icms_vbc,
            icms_picms=icms_picms,
            icms_vicms=icms_vicms,
            pis_cst=pis_cst,
            pis_vbc=pis_vbc,
            pis_ppis=pis_ppis,
            pis_vpis=pis_vpis,
            cofins_cst=cofins_cst,
            cofins_vbc=cofins_vbc,
            cofins_pcofins=cofins_pcofins,
            cofins_vcofins=cofins_vcofins,
            base_calculo=valor_base
        )

        if tipo_str == 'saida' and ncm:
            ncm_limpo = ncm.strip()
            nome = descricao.strip()
            if not NcmUnico.objects.filter(empresa=nota.empresa, ncm=ncm_limpo).exists():
                NcmUnico.objects.create(empresa=nota.empresa, ncm=ncm_limpo, nome_item=nome)

    resultado.append(f"Nota {numero} ({tipo_str}) salva com {nota.itens.count()} itens.")
