import xml.etree.ElementTree as ET
import zipfile
import os 
from core.services.config import cfops_nao_compoe_simples
from core.services.extracao import extrair_formatar_data_nf, extrair_cst_csosn, extrair_valores_notas, extrair_dados_nota, extrair_dados_emitente, extrair_dados_destinatario
from core.services.public import inicializar_dicionario_central_periodo_cnpj, dados_por_periodo_e_cnpj, notas_processadas, ncm_nao_encontrados
from core.services.utilitarios import buscar_melhor_correspondencia_ncm

destinatarios_unicos = {}
cache_correspondencias_ncm = {}
unidades_unicas = set()

def verificar_nota_fiscal(dados_nota, finalidade_nfe, notas_processadas):
    dados_items = dados_nota['itens']
    dados_items_filtrados = []
    valor_que_nao_compoe_simples_nacional = 0
    valor_nf = dados_nota['valor_total']
    chave_nota = dados_nota['chave']
    
    for item in dados_items:
        dados_items_filtrados.append(item)
        if item['cfop'] in cfops_nao_compoe_simples or item['cst_icms'] in cfops_nao_compoe_simples:
            valor_que_nao_compoe_simples_nacional += item['valor']
            # print(f"NOTA POSSUI O CFOP {item['cfop']} QUE NÃO COMPÕEM BASE DE CÁLCULO - REMOVENDO")
        
    if round(float(valor_nf), 2) != round(float(valor_que_nao_compoe_simples_nacional), 2) and float(valor_que_nao_compoe_simples_nacional) != 0:
        return float(valor_nf) - valor_que_nao_compoe_simples_nacional
    
    elif round(float(valor_nf), 2) == round(float(valor_que_nao_compoe_simples_nacional), 2):
        return 'VALOR TOTAL DA NOTA NAO COMPOE BASE DE CALCULO'    
    
    # Outras verificações podem ser adicionadas aqui, como:
    # if esta_em_intervalo_excluido(numero_nfe):
    #     print(f"Nota fiscal {chave_nota} é uma nota emitida para correção da malha. Ignorando...")
    #     return 'IGNORAR'

    # Se passou por todas as verificações, a nota deve ser processada
    return False

def extrair_dados_itens(items, cache_correspondencias_ncm, unidades_unicas, ncm_nao_encontrados, chave_nota, dados_datas, dados_empresa, dados_nota_fiscal, dados_destinatario, dados_emitente, finalidade_nfe):
    dados_itens = []
    valor_total_itens = 0

    for item in items:
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
        cest = extrair_valores_notas(item, 'CEST', '')
        numero_item = item.attrib.get('nItem')
        cst_icms = extrair_cst_csosn(item, chave_nota)

        if cfop == "1202":
            cfop = '5102'

        valor_base = v_prod - v_desc + v_frete + v_outro

        # --- ICMS ---
        icms = item.find('.//{http://www.portalfiscal.inf.br/nfe}ICMS')
        base_calculo_icms = extrair_valores_notas(icms, 'vBC', '0,00') if icms is not None else '0,00'
        aliq_icms = extrair_valores_notas(icms, 'pICMS', '0') if icms is not None else '0'
        valor_icms = extrair_valores_notas(icms, 'vICMS', '0,00') if icms is not None else '0,00'
        aliq_mva = extrair_valores_notas(icms, 'pMVAST', '0,00') if icms is not None else '0,00'
        bc_icms_st = extrair_valores_notas(icms, 'vBCST', '0,00') if icms is not None else '0,00'
        aliq_icms_st = extrair_valores_notas(icms, 'pICMSST', '0,00') if icms is not None else '0,00'
        valor_icms_st = extrair_valores_notas(icms, 'vICMSST', '0,00') if icms is not None else '0,00'

        # --- IPI ---
        ipi = item.find('.//{http://www.portalfiscal.inf.br/nfe}IPI')
        cst_ipi = extrair_valores_notas(ipi, 'CST', '50') if ipi is not None else '50'
        base_calculo_ipi = extrair_valores_notas(ipi, 'vBC', '0,00') if ipi is not None else '0,00'
        aliq_ipi = extrair_valores_notas(ipi, 'pIPI', '0') if ipi is not None else '0'
        valor_ipi = extrair_valores_notas(ipi, 'vIPI', '0,00') if ipi is not None else '0,00'
        codigo_enquadramento_ipi = extrair_valores_notas(ipi, 'cEnq', '999') if ipi is not None else '999'

        # --- PIS ---
        pis = item.find('.//{http://www.portalfiscal.inf.br/nfe}PIS')
        cst_pis = extrair_valores_notas(pis, 'CST', '99') if pis is not None else '99'
        base_calculo_pis = extrair_valores_notas(pis, 'vBC', '0,00') if pis is not None else '0,00'
        aliq_pis = extrair_valores_notas(pis, 'pPIS', '0') if pis is not None else '0'
        valor_pis = extrair_valores_notas(pis, 'vPIS', '0,00') if pis is not None else '0,00'

        # --- COFINS ---
        cofins = item.find('.//{http://www.portalfiscal.inf.br/nfe}COFINS')
        cst_cofins = extrair_valores_notas(cofins, 'CST', '01') if cofins is not None else '01'
        base_calculo_cofins = extrair_valores_notas(cofins, 'vBC', '0,00') if cofins is not None else '0,00'
        aliq_cofins = extrair_valores_notas(cofins, 'pCOFINS', '0') if cofins is not None else '0'
        valor_cofins = extrair_valores_notas(cofins, 'vCOFINS', '0,00') if cofins is not None else '0,00'

        unidades_unicas.add(unidade)

        if ncm not in cache_correspondencias_ncm:
            cache_correspondencias_ncm[ncm] = buscar_melhor_correspondencia_ncm(
                {
                    "nome_item_nota": nome,
                    "ncm_item_nota": ncm,
                    "cfop_item": cfop,
                    "valor_base_de_calculo_item": valor_base,
                    "unidade_item": unidade,
                    "codigo_barras_item": codigo_barras
                },
                dados_nota_fiscal, dados_destinatario, dados_emitente
            )

        melhor_correspondencia = cache_correspondencias_ncm[ncm]

        if melhor_correspondencia:
            cst_icms_correto = melhor_correspondencia['cst_icms']
            cst_pis_correto = melhor_correspondencia['cst_pis_cofins']
            cfop_correto = melhor_correspondencia['cfop_correto']
        else:
            ncm_nao_encontrados.append([
                ncm, nome, chave_nota,
                dados_datas['data_emissao_formatada_nota_para_excel'],
                valor_base
            ])
            cst_icms_correto = '102'
            cst_pis_correto = '49 - Outras Operações de Saída ou 99 - Outras Operações'
            cfop_correto = cfop

        dados_itens.append({
            'nome_item_nota': nome,
            'chave_nota': chave_nota,
            'cst_icms': cst_icms,
            'cst_pis_cofins': cst_pis,
            'cst_icms_correto': cst_icms_correto,
            'cst_pis_cofins_correto': cst_pis_correto,
            'ncm': ncm,
            'cfop': cfop,
            'valor': valor_base,
            'data': dados_datas['data_emissao_formatada_nota_para_excel'],
            'codigo_barras': codigo_barras,
            'unidade': unidade,
            'cfop_correto': cfop_correto,
            'cest' : cest,

            'base_calculo_icms': base_calculo_icms,
            'aliq_icms': aliq_icms,
            'valor_icms': valor_icms,
            'aliq_mva' : aliq_mva,
            'bc_icms_st' : bc_icms_st,
            'aliq_icms_st' : aliq_icms_st,
            'valor_icms_st' : valor_icms_st,

            'cst_ipi': cst_ipi,
            'base_calculo_ipi': base_calculo_ipi,
            'aliq_ipi': aliq_ipi,
            'valor_ipi': valor_ipi,
            'codigo_enquadramento_ipi': codigo_enquadramento_ipi,

            'cst_pis': cst_pis,
            'base_calculo_pis': base_calculo_pis,
            'aliq_pis': aliq_pis,
            'valor_pis': valor_pis,

            'cst_cofins': cst_cofins,
            'base_calculo_cofins': base_calculo_cofins,
            'aliq_cofins': aliq_cofins,
            'valor_cofins': valor_cofins
        })

        valor_total_itens += valor_base
        
        if finalidade_nfe == '1':

            for key, value in [(cst_icms_correto, valor_base), (cst_pis_correto, valor_base)]:
                dados_empresa['dicionario_csts_corretos'].setdefault(key, 0)
                dados_empresa['dicionario_csts_corretos'][key] += float(value)

            for key, value in [(cst_icms, valor_base), (cst_pis, valor_base)]:
                dados_empresa['dicionario_csts_originais'].setdefault(key, 0)
                dados_empresa['dicionario_csts_originais'][key] += float(value)

    return dados_itens, valor_total_itens

def processar_notas_saida(nome_arquivo_zip) :
    with zipfile.ZipFile(os.path.join('notas_fiscais', nome_arquivo_zip), 'r') as arquivo_zip:
        lista_de_arquivos = [f for f in arquivo_zip.namelist() if not f.startswith('CANCELADO')]
        
        for arquivo_nome in lista_de_arquivos:
            if 'EVENTO' in arquivo_nome:
                print(arquivo_nome, 'É UMA NOTA DE EVENTOS')
                continue
            else:
                try:
                    with arquivo_zip.open(arquivo_nome) as arquivo_xml:
                        tree = ET.parse(arquivo_xml)
                        root = tree.getroot()
                        
                        # Verificando se o arquivo é um evento pela tag <tpEvento>
                        tp_evento = root.find('.//{http://www.portalfiscal.inf.br/nfe}tpEvento')
                        if tp_evento is not None:
                            print(f"{arquivo_nome} é um evento, pulando...")
                            continue  # Ignorar a nota se for um evento

                        chave_nota = extrair_valores_notas(root, 'chNFe', '0')
                        finalidade_nfe = extrair_valores_notas(root, 'finNFe', '1')
                        modelo_nota = extrair_valores_notas(root, 'mod', None)
                        dados_datas = extrair_formatar_data_nf(root, chave_nota)
                        mes_ano = dados_datas['mes_ano']
                        dados_empresa_emitente = root.find('.//{http://www.portalfiscal.inf.br/nfe}emit') 
                        dados_emitente = extrair_dados_emitente(dados_empresa_emitente)
                        dados_empresa_destinatario = root.find('.//{http://www.portalfiscal.inf.br/nfe}dest') 
                        dados_destinatario, cnpj_destinatario = extrair_dados_destinatario(dados_empresa_destinatario, destinatarios_unicos)
                        dados_nota_fiscal = extrair_dados_nota(root, chave_nota, cnpj_destinatario)
                        
                        # Verifica se a nota já foi processada
                        if chave_nota in notas_processadas:
                            print(f"Nota fiscal {chave_nota} já foi processada. Ignorando...")
                            continue
                        notas_processadas.add(chave_nota)
                                                
                        inicializar_dicionario_central_periodo_cnpj(mes_ano, dados_emitente['cnpj'])
                        dados_empresa = dados_por_periodo_e_cnpj[mes_ano][dados_emitente['cnpj']]
                        
                        items = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')
                        dados_items, valor_total_itens = extrair_dados_itens(items, cache_correspondencias_ncm, unidades_unicas, ncm_nao_encontrados, chave_nota, dados_datas, dados_empresa, dados_nota_fiscal, dados_destinatario, dados_emitente, finalidade_nfe)
                        dados_nota_fiscal['itens'] = dados_items
                        dados_nota_fiscal['destinatarios'] = {}
                        dados_nota_fiscal['indicador_operacao'] = '1'
                        
                        # # Usar a função de verificação
                        # verificacao_nota_fiscal = verificar_nota_fiscal(dados_nota_fiscal, finalidade_nfe, notas_processadas)
                        
                        # if verificacao_nota_fiscal == 'VALOR TOTAL DA NOTA NAO COMPOE BASE DE CALCULO':
                        #     dados_empresa['notas_que_nao_compoem_base'].append(dados_nota_fiscal)

                        #     if cnpj_destinatario not in dados_empresa['destinatarios'] and modelo_nota != '65':
                        #         dados_nota_fiscal['destinatarios'][cnpj_destinatario] = dados_destinatario 
                        #     continue         
                        # else:
                        
                        if finalidade_nfe == '4':
                            dados_empresa['dados_devolucao']['notas'].append(dados_nota_fiscal)
                            dados_empresa['dados_devolucao']['itens'].extend(dados_items)
                            dados_empresa['dados_devolucao']['emitente'] = dados_emitente
                            dados_empresa['dados_devolucao']['unidades'] = unidades_unicas
                            if cnpj_destinatario not in dados_empresa['destinatarios'] and modelo_nota != '65':
                                dados_empresa['destinatarios'][cnpj_destinatario] = dados_destinatario   
                                dados_nota_fiscal['destinatarios'] = dados_destinatario 
                            continue
                        
                        elif finalidade_nfe == '1':
                            if cnpj_destinatario not in dados_empresa['destinatarios'] and modelo_nota != '65':
                                dados_empresa['destinatarios'][cnpj_destinatario] = dados_destinatario   
                                dados_nota_fiscal['destinatarios'] = dados_destinatario 
                            
                            dados_empresa['valor_total_nfe'] += valor_total_itens
                            dados_empresa['notas'].append(dados_nota_fiscal)
                            dados_empresa['itens'].extend(dados_items)
                            dados_empresa['emitente'] = dados_emitente
                            dados_empresa['unidades'] = unidades_unicas

                except ET.ParseError as e:
                    print(f"Erro ao processar o arquivo XML {arquivo_nome}: {e}")