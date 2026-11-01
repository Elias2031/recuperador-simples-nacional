import pandas as pd
import os
from pyautogui import alert
from MODULES.public import dados_por_periodo_e_cnpj, ncm_nao_encontrados
from MODULES.gerar_planilha_segregacao import gerar_planilha_fisica, adicionar_item_na_planilha, finalizar_planilha
from MODULES.calculos_tributarios import calcular_simples_nacional_anexo_I
from MODULES.processar_notas_entrada import processar_notas_entrada
from MODULES.processar_notas_cte import processar_notas_entrada_cte
from MODULES.processar_notas_saida import processar_notas_saida

def processar_planilhas_segregacao(dados_por_periodo_e_cnpj):
    # Percorre cada período
    for periodo, dados_cnpj in dados_por_periodo_e_cnpj.items():
        # Para cada CNPJ dentro do período
        for cnpj, dados in dados_cnpj.items():
            contador = 2  # Inicializa o contador para a planilha
            gerar_planilha_fisica()  # Função que cria a planilha física

            # Itera sobre os itens para adicionar na planilha
            for item in dados['itens']:
                item_dict = {
                    'nome_item_nota': item['nome_item_nota'],
                    'chave_nota': item['chave_nota'],
                    'cst_icms': item['cst_icms'],
                    'cst_pis_cofins': item['cst_pis_cofins'],
                    'cst_icms_correto': item['cst_icms_correto'],
                    'cst_pis_cofins_correto': item['cst_pis_cofins_correto'],
                    'ncm': item['ncm'],
                    'cfop': item['cfop'],
                    'valor': item['valor'],
                    'ncm_excel': 'item[ncm_excel]',  # Mantém como string literal, se necessário
                    'contador': contador,
                    'data': item['data'],
                    'cfop_excel': item['cfop_correto'],  # Mantém como string literal, se necessário
                }
                adicionar_item_na_planilha(item_dict)
                contador += 1

            # Finaliza a planilha com os dicionários de CSTs corretos e originais
            finalizar_planilha(
                dados['dicionario_csts_corretos'],
                dados['dicionario_csts_originais'],
                cnpj,
                periodo
            )

def comecar_apurar(NCMS_ANALISADOS):
    diretorio_atual = os.getcwd()
    arquivos_na_pasta_notas_fiscais = os.listdir(os.path.join(diretorio_atual, 'notas_fiscais'))
    arquivos_zip = [arquivo for arquivo in arquivos_na_pasta_notas_fiscais if arquivo.endswith('.zip')]
    
    notas_entradas = []
    notas_entradas_cte = []
    notas_saidas = []
    
    for nome_arquivo_zip in arquivos_zip:
        if 'cte'in nome_arquivo_zip.lower():
            notas_entradas_cte.append(nome_arquivo_zip)
        elif 'dest' in nome_arquivo_zip.lower() or 'destinatário' in nome_arquivo_zip.lower():
            notas_entradas.append(nome_arquivo_zip)
        else :
            notas_saidas.append(nome_arquivo_zip)
        
    for nota in notas_saidas:
        processar_notas_saida(nota)
    for nota in notas_entradas:
        processar_notas_entrada(nota)
    for nota in notas_entradas_cte:
        processar_notas_entrada_cte(nota)
    
    processar_planilhas_segregacao(dados_por_periodo_e_cnpj)
    calcular_simples_nacional_anexo_I(dados_por_periodo_e_cnpj)

    if len(ncm_nao_encontrados) > 1:
        df = pd.DataFrame(ncm_nao_encontrados[1:], columns=ncm_nao_encontrados[0])
        df.to_excel('Itens sem correspondência.xlsx', index=False)
        alert(text=f'{len(ncm_nao_encontrados)} Itens não foram analisados corretamente. Por favor, verifique a tabela de NCMs sem correspondência.', title='Segregador Simples Nacional', button='OK')
    else:
        alert(text=f'Segregação finalizada com SUCESSO', title='Segregador Simples Nacional', button='OK')
        
comecar_apurar('NCMS_ANALISADOS')
