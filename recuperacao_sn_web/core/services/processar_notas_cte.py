import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

from core.models import Empresa, NotaFiscal, ItemNotaFiscal, Participante, NotaParticipante, ApuracaoFiscal, Competencia

def extrair_valores_notas_cte(root, caminho, valor_padrao):
    elemento = root.find(f'.//{{http://www.portalfiscal.inf.br/cte}}{caminho}')
    return elemento.text if elemento is not None else valor_padrao

def extrair_formatar_data_nf_cte(root):
    # EXTRAIR E FORMATAR DATA DA NOTA
    data_emissao_nota = root.find('.//{http://www.portalfiscal.inf.br/cte}dhEmi')
    data_emissao_nota = data_emissao_nota.text if data_emissao_nota is not None else '0'    
    
    data_hora_recebimento = root.find('.//{http://www.portalfiscal.inf.br/cte}dhRecbto')
    data_hora_recebimento = data_hora_recebimento.text if data_hora_recebimento is not None else '0'  

    if data_emissao_nota != '0':
        data_objeto = datetime.strptime(data_emissao_nota[:10], "%Y-%m-%d")
        data_emissao_formatada_nota_para_excel = data_objeto.strftime("%d/%m/%Y")
        mes_emissao = str(data_objeto.month).zfill(2)
        ano_emissao = data_objeto.year
    else:
        data_emissao_formatada_nota_para_excel = '0'
        mes_emissao = '0'
        ano_emissao = '0'
    
    if data_hora_recebimento != '0':
        data_recebimento_objeto = datetime.strptime(data_hora_recebimento[:10], "%Y-%m-%d")
        data_recebimento_formatada_para_excel = data_recebimento_objeto.strftime("%d/%m/%Y")
        mes_recebimento = str(data_recebimento_objeto.month).zfill(2)
        ano_recebimento = data_recebimento_objeto.year
    else:
        data_recebimento_formatada_para_excel = '0'
        mes_recebimento = '0'
        ano_recebimento = '0'
        
    dados_datas = {
        'data_emissao_formatada_nota_para_excel': data_emissao_formatada_nota_para_excel,
        'mes_ano_emissao': f'{mes_emissao}_{ano_emissao}',
        'data_recebimento_formatada_para_excel': data_recebimento_formatada_para_excel,
        'mes_ano_recebimento': f'{ano_recebimento}_{mes_recebimento}'
    }    

    return dados_datas

def processar_cte_xml(xml_file, nome_arquivo, usuario, empresa_ativa, resultado):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    chave = extrair_valores_notas_cte(root, 'chCTe', '')
    if NotaFiscal.objects.filter(chave=chave).exists():
        resultado.append(f"Ignorado: CTe {chave} já foi processado.")
        return

    emitente = root.find('.//{http://www.portalfiscal.inf.br/cte}emit')
    icms = root.find('.//{http://www.portalfiscal.inf.br/cte}ICMS')
    dados_datas = extrair_formatar_data_nf_cte(root)

    try:
        mes, ano = map(int, dados_datas['mes_ano_emissao'].split('_'))
    except Exception as e:
        resultado.append(f"Erro ao interpretar a data da CTe {chave}: {str(e)}")
        return

    try:
        data_emissao = datetime.strptime(dados_datas['data_emissao_formatada_nota_para_excel'], "%d/%m/%Y").date()
    except Exception as e:
        resultado.append(f"Erro ao converter data da CTe {chave}: {str(e)}")
        return

    competencia, _ = Competencia.objects.get_or_create(mes=mes, ano=ano)
    apuracao, _ = ApuracaoFiscal.objects.get_or_create(empresa=empresa_ativa, competencia=competencia)

    destinatario = root.find('.//{http://www.portalfiscal.inf.br/cte}dest')
    cnpj_emitente = extrair_valores_notas_cte(emitente, 'CNPJ', '').zfill(14)
    cnpj_destinatario = extrair_valores_notas_cte(destinatario, 'CNPJ', '').zfill(14)

    if empresa_ativa.cnpj not in [cnpj_emitente, cnpj_destinatario]:
        resultado.append(f"Rejeitado: CTe {chave} não pertence à empresa ativa ({empresa_ativa.razao_social}).")
        return

    tipo_str = 'saida' if empresa_ativa.cnpj == cnpj_emitente else 'entrada'

    nota = NotaFiscal.objects.create(
        empresa=empresa_ativa,
        apuracao=apuracao,
        numero=extrair_valores_notas_cte(root, 'nCT', ''),
        serie=extrair_valores_notas_cte(root, 'serie', ''),
        data_emissao=data_emissao,
        valor_total=extrair_valores_notas_cte(root, 'vTPrest', '0.00'),
        tipo='cte',
        chave=chave,
        arquivo_xml = xml_file
    )

    for xml_elemento, papel in [(emitente, 'emitente'), (destinatario, 'destinatario')]:
        cnpj = extrair_valores_notas_cte(xml_elemento, 'CNPJ', '').zfill(14)
        nome = extrair_valores_notas_cte(xml_elemento, 'xNome', 'Desconhecido')
        participante, _ = Participante.objects.get_or_create(cnpj=cnpj, defaults={'nome': nome})
        NotaParticipante.objects.get_or_create(nota=nota, participante=participante, tipo=papel)

    ItemNotaFiscal.objects.create(
        nota=nota,
        descricao='CT-e Transporte',
        ncm='',
        unidade='UN',
        valor_produto=extrair_valores_notas_cte(root, 'vTPrest', '0.00'),
        cst_original=extrair_valores_notas_cte(icms, 'CST', ''),
    )

    resultado.append(f"CT-e {chave} ({tipo_str}) salvo com sucesso.")
