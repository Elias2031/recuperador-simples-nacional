import zipfile
import os
import xml.etree.ElementTree as ET
from time import sleep
from MODULES.public import inicializar_dicionario_central_periodo_cnpj, dados_por_periodo_e_cnpj
from MODULES.extracao import extrair_formatar_data_nf, extrair_cst_csosn, extrair_valores_notas, extrair_dados_nota, extrair_dados_emitente

naturezas_unicas = {}
notas_processadas = set()

def adicionar_natureza_operacao(natureza, dados_empresa):
    if natureza not in naturezas_unicas:
        naturezas_unicas

def extrair_dados_destinatario(dados_empresa_destinatario):
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

def validar_nota_entrada(chave_nota):
    # return True
    if chave_nota in notas_processadas:
        print(f"Nota fiscal {chave_nota} já foi processada. Ignorando...")
        return False

    notas_processadas.add(chave_nota)
    return True

def extrair_dados_itens(items, chave_nota, dados_datas):
    dados_itens = []
    valor_total_itens = 0
    unidades_unicas_nota = set()
    
    for item in items:
        # Extração de campos com fallback
        nome = extrair_valores_notas(item, 'xProd', 'ITEM IMPORTADO')
        ncm = extrair_valores_notas(item, 'NCM', None)
        cfop = extrair_valores_notas(item, 'CFOP', None)
        v_desc = float(extrair_valores_notas(item, 'vDesc', '0'))
        v_frete = float(extrair_valores_notas(item, 'vFrete', '0')) 
        v_outro = float(extrair_valores_notas(item, 'vOutro', '0'))
        unidade = extrair_valores_notas(item, 'uCom', None)
        codigo_barras = extrair_valores_notas(item, 'cEAN', None)
        quantidade = extrair_valores_notas(item, 'qCom', None)
        valor_unitario = extrair_valores_notas(item, 'vUnCom', None)
        v_prod = float(extrair_valores_notas(item, 'vProd', '0'))
        numero_item = item.attrib.get('nItem')
        cst_icms = extrair_cst_csosn(item, chave_nota)
        cest = extrair_valores_notas(item, 'CEST', '')
        
        # Extração do ICMS
        icms = item.find('.//{http://www.portalfiscal.inf.br/nfe}ICMS')
        base_calculo_icms = extrair_valores_notas(icms, 'vBC', '0,00') if icms is not None else '0,00'
        aliq_icms = extrair_valores_notas(icms, 'pICMS', '0') if icms is not None else '0'
        valor_icms = extrair_valores_notas(icms, 'vICMS', '0,00') if icms is not None else '0,00'
        aliq_mva = extrair_valores_notas(icms, 'pMVAST', '0,00') if icms is not None else '0,00'
        bc_icms_st = extrair_valores_notas(icms, 'vBCST', '0,00') if icms is not None else '0,00'
        aliq_icms_st = extrair_valores_notas(icms, 'pICMSST', '0,00') if icms is not None else '0,00'
        valor_icms_st = extrair_valores_notas(icms, 'vICMSST', '0,00') if icms is not None else '0,00'
        
        # Extração do IPI
        ipi = item.find('.//{http://www.portalfiscal.inf.br/nfe}IPI')
        cst_ipi = extrair_valores_notas(ipi, 'CST', '50') if ipi is not None else '50'
        base_calculo_ipi = extrair_valores_notas(ipi, 'vBC', '0,00') if ipi is not None else '0,00'
        aliq_ipi = extrair_valores_notas(ipi, 'pIPI', '0') if ipi is not None else '0'
        valor_ipi = extrair_valores_notas(ipi, 'vIPI', '0,00') if ipi is not None else '0,00'
        codigo_enquadramento_ipi = extrair_valores_notas(ipi, 'cEnq', '999') if ipi is not None else '999'
        
        # Extração do CST do PIS
        pis = item.find('.//{http://www.portalfiscal.inf.br/nfe}PIS')
        cst_pis = extrair_valores_notas(pis, 'CST', '99') if pis is not None else '99'
        base_calculo_pis = extrair_valores_notas(pis, 'vBC', '0,00') if pis is not None else '0,00'
        aliq_pis = extrair_valores_notas(pis, 'pPIS', '0') if pis is not None else '0'
        valor_pis = extrair_valores_notas(pis, 'vPIS', '0,00') if pis is not None else '0,00'
        
        # Extração do CST do PIS
        cofins = item.find('.//{http://www.portalfiscal.inf.br/nfe}COFINS')
        cst_cofins = extrair_valores_notas(cofins, 'CST', '01') if cofins is not None else '01'
        base_calculo_cofins = extrair_valores_notas(cofins, 'vBC', '0,00') if cofins is not None else '0,00'
        aliq_cofins = extrair_valores_notas(cofins, 'pCOFINS', '0') if cofins is not None else '0'
        valor_cofins = extrair_valores_notas(cofins, 'vCOFINS', '0,00') if cofins is not None else '0,00'
        
        # Cálculo da base de cálculo do item
        valor_base = v_prod - v_desc + v_frete + v_outro
        valor_total_itens += valor_base

        unidades_unicas_nota.add(unidade)
        
        if cfop[0] == "5":
            cfop = "1" + cfop[1:]
        elif cfop[0] == "6":
            cfop = "2" + cfop[1:]
        elif cfop[0] == "7":
            cfop = "3" + cfop[1:]
        
        if cfop == "1405":
            cfop = "1403"

        if cfop == '1927':
            return 'pular'
        
        # Monta o dicionário final
        dados_itens.append({
            'nome_item_nota': nome,
            'chave_nota': chave_nota,
            'situacao_tributaria_icms': cst_icms,
            'cst_pis_cofins': cst_pis,
            'ncm': ncm,
            'cfop': cfop,
            'valor': valor_base,
            'data': dados_datas['data_emissao_formatada_nota_para_excel'],
            'codigo_barras': codigo_barras,
            'unidade': unidade,
            'numero_item': numero_item,
            'quantidade_item' : quantidade,
            'valor_unitario' : valor_unitario,
            'desconto_item_nota' : v_desc,
            'cest' : cest, 
            
            'cst_icms' : cst_icms,
            'base_calculo_icms' : base_calculo_icms,
            'aliq_icms' : aliq_icms,
            'valor_icms' : valor_icms, 
            'aliq_mva' : aliq_mva,
            'bc_icms_st' : bc_icms_st,
            'aliq_icms_st' : aliq_icms_st,
            'valor_icms_st' : valor_icms_st,
            
            'cst_ipi' : cst_ipi, 
            'base_calculo_ipi' : base_calculo_ipi, 
            'aliq_ipi' : aliq_ipi, 
            'valor_ipi' : valor_ipi, 
            'codigo_enquadramento_ipi' : codigo_enquadramento_ipi, 
            
            'cst_pis' : cst_pis,
            'base_calculo_pis' : base_calculo_pis,
            'aliq_pis' : aliq_pis,
            'valor_pis' : valor_pis,
            
            'cst_cofins' : cst_cofins,
            'base_calculo_cofins' : base_calculo_cofins,
            'aliq_cofins' : aliq_cofins,
            'valor_cofins' : valor_cofins
        })

    return dados_itens, valor_total_itens, unidades_unicas_nota

def processar_notas_entrada(nome_arquivo_zip):
    with zipfile.ZipFile(os.path.join('notas_fiscais', nome_arquivo_zip), 'r') as arquivo_zip:
        lista_de_arquivos = [f for f in arquivo_zip.namelist() if not f.startswith('CANCELADO')]
        
        for arquivo_nome in lista_de_arquivos:
            try:
                with arquivo_zip.open(arquivo_nome) as arquivo_xml:
                    tree = ET.parse(arquivo_xml)
                    root = tree.getroot()
                    chave_nota = extrair_valores_notas(root, 'chNFe', '')
                    finalidade_nfe = extrair_valores_notas(root, 'finNFe', '1')
                    
                    if validar_nota_entrada(chave_nota):
                    # if True:
                        if finalidade_nfe in ('1', '4', '2', '3'):                                         
                            chave_nota = extrair_valores_notas(root, 'chNFe', f'merda{arquivo_nome}')
                            
                            modelo_nota = extrair_valores_notas(root, 'mod', None)
                            dados_datas = extrair_formatar_data_nf(root, chave_nota)
                            mes_ano = dados_datas['mes_ano']
                            dados_empresa_emitente = root.find('.//{http://www.portalfiscal.inf.br/nfe}emit') 
                            dados_emitente = extrair_dados_emitente(dados_empresa_emitente)
                            dados_empresa_destinatario = root.find('.//{http://www.portalfiscal.inf.br/nfe}dest') 
                            dados_destinatario, cnpj_destinatario = extrair_dados_destinatario(dados_empresa_destinatario)
                            dados_nota_fiscal = extrair_dados_nota(root, chave_nota, cnpj_destinatario)
                            
                            if dados_nota_fiscal['cnpj_destinatario'] != "":
                                dados_nota_fiscal['cnpj_destinatario'] = dados_emitente['cnpj']
                            
                            inicializar_dicionario_central_periodo_cnpj(mes_ano, cnpj_destinatario)
                            dados_empresa = dados_por_periodo_e_cnpj[mes_ano][cnpj_destinatario]['dados_entradas']
                            dados_empresa['num_notas_entrada'] += 1
                            
                            dados_empresa['creditos_por_entrada_icms'] += float(dados_nota_fiscal['valor_icms'].replace(',','.'))
                            
                            items = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
                            
                            if extrair_dados_itens(items, chave_nota, dados_datas) == 'pular':
                                continue
                            else :
                                dados_items, valor_total_itens, unidades_unicas_notas = extrair_dados_itens(items, chave_nota, dados_datas)
                                dados_nota_fiscal['itens'] = dados_items
                                dados_nota_fiscal['emitentes'] = {}
                                dados_nota_fiscal['indicador_operacao'] = '0'
                                
                                if dados_emitente['cnpj'] not in dados_empresa['emitentes'] and modelo_nota != '65':
                                    dados_empresa['emitentes'][dados_emitente['cnpj']] = dados_emitente   
                                    dados_nota_fiscal['emitentes'] = dados_emitente 
                                    
                                dados_empresa['valor_total_nfe_entrada'] += valor_total_itens
                                dados_empresa['notas'].append(dados_nota_fiscal)
                                dados_empresa['itens'].extend(dados_items)
                                dados_empresa['emitente'] = dados_emitente
                                
                                for unidade in unidades_unicas_notas:
                                    dados_empresa['unidades'].add(unidade)

            except ET.ParseError as e:
                print(f"Erro ao processar o arquivo XML de ENTRADA {arquivo_nome}: {e}")