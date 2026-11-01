import xml.etree.ElementTree as ET
from core.services.extracao import extrair_valores_notas
from core.services.processar_notas_cte import processar_cte_xml
from core.models import (
    Empresa, NotaFiscal, ItemNotaFiscal,
    Participante, NotaParticipante,
    UploadLote, ApuracaoFiscal, Competencia, NcmUnico
)
from decimal import Decimal
from django.db import transaction

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

    with transaction.atomic():
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

        itens_para_salvar = []
        ncm_vistos = set()

        for det in root.findall('.//ns:det', ns):
            prod = det.find('ns:prod', ns)
            imposto = det.find('ns:imposto', ns)

            def get(tag): return extrair_valores_notas(prod, tag)
            def get_decimal(tag, default='0.00'): return Decimal(extrair_valores_notas(prod, tag, default).replace(',', '.'))

            # Impostos
            icms = imposto.find('.//ns:ICMS', ns)
            icms_cst = origem = icms_mod_bc = ''
            icms_vbc = icms_picms = icms_vicms = aliq_mva = bc_icms_st = aliq_icms_st = valor_icms_st = Decimal('0.00')
            if icms is not None and len(icms):
                icms_sn = list(icms)[0]
                icms_cst = extrair_valores_notas(icms_sn, 'CSOSN') or extrair_valores_notas(icms_sn, 'CST')
                origem = extrair_valores_notas(icms_sn, 'orig')
                icms_mod_bc = extrair_valores_notas(icms_sn, 'modBC')
                icms_vbc = get_decimal('vBC')
                icms_picms = get_decimal('pICMS')
                icms_vicms = get_decimal('vICMS')
                aliq_mva = get_decimal('pMVAST')
                bc_icms_st = get_decimal('vBCST')
                aliq_icms_st = get_decimal('pICMSST')
                valor_icms_st = get_decimal('vICMSST')

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

            valor_base = get_decimal('vProd') - get_decimal('vDesc') + get_decimal('vFrete') + get_decimal('vOutro')

            item = ItemNotaFiscal(
                nota=nota,
                codigo_produto=get('cProd'),
                descricao=get('xProd'),
                ean=get('cEAN'),
                ean_tributavel=get('cEANTrib'),
                unidade=get('uCom'),
                unidade_tributavel=get('uTrib'),
                quantidade=get_decimal('qCom'),
                quantidade_tributavel=get_decimal('qTrib'),
                valor_unitario=get_decimal('vUnCom'),
                valor_unitario_tributavel=get_decimal('vUnTrib'),
                valor_produto=get_decimal('vProd'),
                ncm=get('NCM'),
                cest=get('CEST'),
                cfop=get('CFOP'),
                vTotTrib=get_decimal('vTotTrib', '0'),
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

            itens_para_salvar.append(item)

            if tipo_str == 'saida' and item.ncm and item.ncm not in ncm_vistos:
                ncm_vistos.add(item.ncm)
                if not NcmUnico.objects.filter(empresa=nota.empresa, ncm=item.ncm).exists():
                    NcmUnico.objects.create(empresa=nota.empresa, ncm=item.ncm, nome_item=item.descricao.strip())

        ItemNotaFiscal.objects.bulk_create(itens_para_salvar, batch_size=500)

    resultado.append(f"Nota {numero} ({tipo_str}) salva com {len(itens_para_salvar)} itens.")
