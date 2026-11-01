import datetime
import PyPDF2
import os 
from core.models import Empresa, Competencia, PgdasValorDeclarado


NAMESPACE = {'ns': 'http://www.portalfiscal.inf.br/nfe'}

def extrair_valores_notas(root, caminho, valor_padrao='', ns=NAMESPACE):
    """Extrai texto de um campo XML da NFe, retornando valor padrão se ausente ou vazio."""
    try:
        elemento = root.find(f'.//ns:{caminho}', ns)
        texto = elemento.text.strip() if elemento is not None and elemento.text else valor_padrao
        return texto
    except Exception:
        return valor_padrao

def extrair_dados_nota(root, chave, cnpj_destinatario):
    totais = root.find('.//{http://www.portalfiscal.inf.br/nfe}total')
    modelo = extrair_valores_notas(root, 'mod', None)
    if modelo == '65':
        dados_nota = {
            'modelo' : extrair_valores_notas(root, 'mod', None),
            'serie' : extrair_valores_notas(root, 'serie', None),
            'numero' : extrair_valores_notas(root, 'nNF', None),
            'data_emissao' : extrair_valores_notas(root, 'dhEmi', None),
            'valor_total' : extrair_valores_notas(root, 'vNF', None),
            'tipo_pagamento' : extrair_valores_notas(root, 'indPag', '0'),
            'valor_desconto' : extrair_valores_notas(totais, 'vDesc', None),
            'tipo_frete' : extrair_valores_notas(root, 'modFrete', None),
            'valor_frete' : extrair_valores_notas(totais, 'vFrete', None),
            'valor_seguro' : extrair_valores_notas(totais, 'vSeg', None),
            'valor_outros' : extrair_valores_notas(totais, 'vOutro', None),
            'valor_bc_icms' : extrair_valores_notas(totais, 'vBC', None),
            'valor_icms' : extrair_valores_notas(totais, 'vICMS', None),
            'valor_bc_icms_st' : '',
            'valor_icms_st' : '',
            'valor_ipi' : '',
            'valor_pis' : '',
            'valor_cofins' : '',
            'valor_pis_st' : extrair_valores_notas(totais, 'vPISST', ''),
            'valor_cofins_st' : extrair_valores_notas(totais, 'vCOFINSST', ''),
            'chave' : chave,
            'cnpj_destinatario' : '',
            'natureza_operação' : extrair_valores_notas(root, 'natOp', ''),
        }
    else:
        dados_nota = {
            'modelo' : extrair_valores_notas(root, 'mod', None),
            'serie' : extrair_valores_notas(root, 'serie', None),
            'numero' : extrair_valores_notas(root, 'nNF', None),
            'data_emissao' : extrair_valores_notas(root, 'dhEmi', None),
            'valor_total' : extrair_valores_notas(root, 'vNF', None),
            'tipo_pagamento' : extrair_valores_notas(root, 'indPag', '0'),
            'valor_desconto' : extrair_valores_notas(root, 'vDesc', None),
            'tipo_frete' : extrair_valores_notas(root, 'modFrete', None),
            'valor_frete' : extrair_valores_notas(totais, 'vFrete', None),
            'valor_seguro' : extrair_valores_notas(totais, 'vSeg', None),
            'valor_outros' : extrair_valores_notas(totais, 'vOutro', None),
            'valor_bc_icms' : extrair_valores_notas(totais, 'vBC', None),
            'valor_icms' : extrair_valores_notas(totais, 'vICMS', None),
            'valor_bc_icms_st' : extrair_valores_notas(totais, 'vBCST', None),
            'valor_icms_st' : extrair_valores_notas(totais, 'vST', None),
            'valor_ipi' : extrair_valores_notas(totais, 'vIPI', None),
            'valor_pis' : extrair_valores_notas(totais, 'vPIS', None),
            'valor_cofins' : extrair_valores_notas(totais, 'vCOFINS', None),
            'valor_pis_st' : extrair_valores_notas(totais, 'vPISST', ''),
            'valor_cofins_st' : extrair_valores_notas(totais, 'vCOFINSST', ''),
            'chave' : chave,''
            'cnpj_destinatario' : cnpj_destinatario,
            'natureza_operação' : extrair_valores_notas(root, 'natOp', ''),
        }
    
    
    return dados_nota

def extrair_dados_emitente(dados_empresa_emitente):
    if dados_empresa_emitente is not None:
        dados_emitente = {
            "razao_social": extrair_valores_notas(dados_empresa_emitente, 'xNome', None),
            "nome_fantasia": extrair_valores_notas(dados_empresa_emitente, 'xFant', None),
            "inscricao_estadual": extrair_valores_notas(dados_empresa_emitente, 'IE', None),
            "UF": extrair_valores_notas(dados_empresa_emitente, 'UF', None),
            "codigo_municipio": extrair_valores_notas(dados_empresa_emitente, 'cMun', None),
            "cnpj": extrair_valores_notas(dados_empresa_emitente, 'CNPJ', None),
            "cep": extrair_valores_notas(dados_empresa_emitente, 'CEP', None),
            "logradouro": extrair_valores_notas(dados_empresa_emitente, 'xLgr', None),
            "numero_logradouro": extrair_valores_notas(dados_empresa_emitente, 'nro', None),
            "bairro": extrair_valores_notas(dados_empresa_emitente, 'xBairro', None),
            "telefone": extrair_valores_notas(dados_empresa_emitente, 'fone', None),
            "codigo_pais": extrair_valores_notas(dados_empresa_emitente, 'cPais', ''),
        }
    else:
        dados_emitente = {
            "razao_social": None,
            "nome_fantasia": None,
            "inscricao_estadual": None,
            "UF": None,
            "codigo_municipio": None,
            "cnpj": None,
            "cep": None,
            "logradouro": None,
            "numero_logradouro": None,
            "bairro": None,
            "telefone": None,
            "codigo_pais": ''
        }

    return dados_emitente

def extrair_dados_destinatario(dados_empresa_destinatario, destinatarios_unicos):
    if dados_empresa_destinatario is not None:
        razao_social_destinatario = extrair_valores_notas(dados_empresa_destinatario, 'xNome', None)
        cnpj_destinatario = extrair_valores_notas(dados_empresa_destinatario, 'CNPJ', None)

        if cnpj_destinatario is None:
            cnpj_destinatario = extrair_valores_notas(dados_empresa_destinatario, 'CPF', None)

        dados_destinatario = {
            "razao_social": razao_social_destinatario,
            "codigo_pais": extrair_valores_notas(dados_empresa_destinatario, 'cPais', ''),
            "inscricao_estadual": extrair_valores_notas(dados_empresa_destinatario, 'IE', ''),
            "codigo_municipio": extrair_valores_notas(dados_empresa_destinatario, 'cMun', None),
            "logradouro": extrair_valores_notas(dados_empresa_destinatario, 'xLgr', None),
            "numero_logradouro": extrair_valores_notas(dados_empresa_destinatario, 'nro', None),
            "bairro": extrair_valores_notas(dados_empresa_destinatario, 'xBairro', None),
            "uf": extrair_valores_notas(dados_empresa_destinatario, 'UF', None),
        }

        if cnpj_destinatario not in destinatarios_unicos:
            destinatarios_unicos[cnpj_destinatario] = dados_destinatario
    else:
        dados_destinatario = {
            "razao_social": '',
            "codigo_pais": '',
            "inscricao_estadual": '',
            "codigo_municipio": '',
            "logradouro": '',
            "numero_logradouro": '',
            "bairro": '',
            "uf": '',
        }
        cnpj_destinatario = ''
    return dados_destinatario, cnpj_destinatario

def extrair_dados_pgdas(caminho_pdf):
    print(caminho_pdf)
    valor_rbt12 = 0
    contador_linhas_apos_total = 0     
    periodo = ''
    conteudo = ''
    valor_IRPJ_pago_original = ''
    valor_CSLL_pago_original = ''
    valor_COFINS_pago_original = ''
    valor_PIS_pago_original = ''
    valor_INSS_pago_original = ''
    valor_ICMS_pago_original = ''
    valor_IPI_pago_original = ''
    valor_ISS_pago_original = ''
    valor_DAS_pago_original = ''
    encontrou_total = False
    dados_pgdas = {}
    cnpj_encontrado = None
    receita_bruta_cnpj = None

    try:
        with open(caminho_pdf, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            number_of_pages = len(reader.pages)
            valor_rbt12p = None
            for page_num in range(number_of_pages):
                page = reader.pages[page_num]
                text = page.extract_text()
                conteudo += text
            
            # Processando o conteúdo extraído
            linhas = conteudo.splitlines()
            for linha in linhas:
                
                # Extração do período de apuração
                if linha.startswith('Período de Apuração'):
                    data_final = linha[33:44].replace('/', '').replace(" ", "")
                    ano = data_final[4:8]
                    mes = data_final[2:4]
                    periodo = f'{mes}_{ano}'
                
                if '(RBT12)' in linha:
                    dados_linha = linha.split()
                    rbt12 = dados_linha[2]
                    valor_rbt12 = float(rbt12[7:].replace('.', '').replace(',', '.'))
                
                if '(RBT12p)' in linha:
                    dados_linha = linha.split()
                    valor_rbt12p = dados_linha[3].split(')')[1]
                    if valor_rbt12p:
                        valor_rbt12 = float(valor_rbt12p.replace('.', '').replace(',', '.'))

                if encontrou_total:
                        contador_linhas_apos_total += 1
                        if contador_linhas_apos_total == 2:
                            valores_a_pagar_originais = linha.split(' ')
                            valor_IRPJ_pago_original = valores_a_pagar_originais[0]
                            valor_CSLL_pago_original = valores_a_pagar_originais[1]
                            valor_COFINS_pago_original = valores_a_pagar_originais[2]
                            valor_PIS_pago_original = valores_a_pagar_originais[3]
                            valor_INSS_pago_original = valores_a_pagar_originais[4]
                            valor_ICMS_pago_original = valores_a_pagar_originais[5]
                            valor_IPI_pago_original = valores_a_pagar_originais[6]
                            valor_ISS_pago_original = valores_a_pagar_originais[7]
                            valor_DAS_pago_original = valores_a_pagar_originais[8]
                    
                if 'Total do Débito Exigível (R$)' in linha:
                    encontrou_total = True
                    contador_linhas_apos_total = 0  # Reseta o contador após encontrar a linha alvo

                if 'CNPJ Estabelecimento' in linha:
                    cnpj_encontrado = linha.split(' ')[2].replace('.', '').replace('-', '').replace('/', '')
                
                # Se encontrar "Nenhuma atividade selecionada", ignora o CNPJ e seus dados
                if 'Nenhuma atividade selecionada' in linha:
                    if cnpj_encontrado in dados_pgdas:
                        del dados_pgdas[cnpj_encontrado]  # Remove qualquer dado já adicionado para o CNPJ
                    cnpj_encontrado = None
                    receita_bruta_cnpj = None
                    continue
                
                if 'Valor Informado' in linha :
                    receita_bruta_cnpj = linha.split(' ')[2].replace('.', '').replace(',', '.')

                if cnpj_encontrado and encontrou_total:
                    dados_pgdas[cnpj_encontrado] = {
                        'receita_bruta': float(receita_bruta_cnpj) if receita_bruta_cnpj else 0.0,
                        'valor_rbt12': float(valor_rbt12),
                        'periodo': periodo,
                        'cnpj' : cnpj_encontrado,
                        'valor_IRPJ_pago_original': valor_IRPJ_pago_original,
                        'valor_CSLL_pago_original': valor_CSLL_pago_original,
                        'valor_COFINS_pago_original': valor_COFINS_pago_original,
                        'valor_PIS_pago_original': valor_PIS_pago_original,
                        'valor_INSS_pago_original': valor_INSS_pago_original,
                        'valor_ICMS_pago_original': valor_ICMS_pago_original,
                        'valor_IPI_pago_original': valor_IPI_pago_original,
                        'valor_ISS_pago_original': valor_ISS_pago_original,
                        'valor_DAS_pago_original': valor_DAS_pago_original
                    }
                
                if 'Total Geral da Empresa' in linha:
                    return dados_pgdas

        return dados_pgdas
    except Exception as e:
        print(f'Erro ao processar o arquivo {caminho_pdf}: {e}')

def extrair_formatar_data_nf(root, chave_nota):
    # EXTRAIR E FORMATAR DATA DA NOTA  
    data_emissao_nota = extrair_valores_notas(root, 'dhEmi', '0' )
    if data_emissao_nota != '0':
        # Converter a string para um objeto datetime
        data_objeto = datetime.datetime.strptime(data_emissao_nota[:10], "%Y-%m-%d")
        
        # Formatar para exibição no Excel
        data_emissao_formatada_nota_para_excel = data_objeto.strftime("%d/%m/%Y")
        
        # Extrair mês e ano
        mes = data_objeto.month
        mes = str(mes).zfill(2)
        ano = data_objeto.year
        mes_ano = f'{mes}_{ano}'
    else:
        data_emissao_formatada_nota_para_excel = '0'
        mes = '0'
        ano = '0'
        print(chave_nota, 'NOTA SEM DATA')
        
    dados_datas = {
        'data_emissao_formatada_nota_para_excel' : data_emissao_formatada_nota_para_excel,
        'mes_ano' : mes_ano
    }    
        
    return dados_datas

def extrair_cst_csosn(item):
    # EXTRAIR E FORMATAR SITAÇÃO TRIBUTARIA DO ICMS 
    icms = item.find('.//{http://www.portalfiscal.inf.br/nfe}ICMS')
    if icms is not None:
        cst_icms = icms.find('.//{http://www.portalfiscal.inf.br/nfe}CST').text if icms.find('.//{http://www.portalfiscal.inf.br/nfe}CST') is not None else 0
        csosn_imcs = icms.find('.//{http://www.portalfiscal.inf.br/nfe}CSOSN').text if icms.find('.//{http://www.portalfiscal.inf.br/nfe}CSOSN') is not None else 0
    else:
        print("NOTA SEM ICMS")
        situacao_tributaria_icms = '090'
        return situacao_tributaria_icms
    
    if cst_icms == 0 :
            situacao_tributaria_icms = csosn_imcs
    else: 
        situacao_tributaria_icms = cst_icms
        
    return situacao_tributaria_icms
