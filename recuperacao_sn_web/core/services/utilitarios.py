import pandas as pd
from difflib import SequenceMatcher
import re
from time import sleep
from functools import lru_cache


def carregar_planilha(arquivo='./ANALISE/ANALISE TRIBUTARIA DROGARIA MRS SIMPLES NACIONAL.xlsx'):
    """Carrega e indexa a planilha uma única vez."""
    df = pd.read_excel(arquivo)
    df['NCM'] = df['NCM'].astype(str)  # Garante que o NCM seja string
    return df.set_index('NCM')  # Torna a busca mais rápida

# df_analise = carregar_planilha()

def jaccard_similarity(str1, str2):
    # Convert to lowercase and remove punctuation
    str1 = re.sub(r'[^\w\s]', '', str1.lower())
    str2 = re.sub(r'[^\w\s]', '', str2.lower())
    
    set1 = set(str1.split())
    set2 = set(str2.split())
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union)

def similaridade(texto1, texto2):
    """Calcula a similaridade entre dois textos."""
    return SequenceMatcher(None, str(texto1), str(texto2)).ratio()

def extrair_valores_notas(root, caminho, valor_padrao):
    """Extrai um valor de um elemento XML, retornando um padrão se não encontrado."""
    elemento = root.find(f'.//{{http://www.portalfiscal.inf.br/nfe}}{caminho}')
    return elemento.text if elemento is not None else valor_padrao

def buscar_melhor_correspondencia_ncm(dados_itens, dados_nota, dados_destinatario, dados_emitente):
    ncm = str(dados_itens['ncm_item_nota'])
    descricao_item = dados_itens['nome_item_nota']
    venda_interestadual = None
    
    # VERIFICANDO SE É UMA VENDA INTERESTADUAL 
    if dados_destinatario['uf'] != None and dados_destinatario['uf'] != '' and dados_destinatario['uf'] != dados_emitente['UF']:
        venda_interestadual = True
    
    if ncm not in df_analise.index:
        print(f'NCM NÃO ENCONTRADO => {ncm}')
        return None

    # Filtra os dados já indexados
    filtro = df_analise.loc[[ncm]].reset_index()

    melhor_correspondencia = None
    maior_similaridade = -1

    for _, linha in filtro.iterrows():
        sim = similaridade(linha['NOME ITEM NOTA'], descricao_item) * 100
        if sim > maior_similaridade:
            maior_similaridade = sim
            melhor_correspondencia = linha

            # Para otimização, interrompe se a similaridade for alta
            if sim > 70:
                break

    if melhor_correspondencia is not None:
        
        if melhor_correspondencia['CST ICMS'] == '101 ou 102' and venda_interestadual: 
            melhor_correspondencia['CST ICMS'] = '102'
            cfop_correto = '6102'
        elif melhor_correspondencia['CST ICMS'] == '101 ou 102' and not venda_interestadual:
            melhor_correspondencia['CST ICMS'] = '102'
            cfop_correto = '5102'
        
        elif melhor_correspondencia['CST ICMS'] == '201, 202, ou 500' and venda_interestadual:
            melhor_correspondencia['CST ICMS'] = '500'
            cfop_correto = '6404'
        elif melhor_correspondencia['CST ICMS'] == '201, 202, ou 500' and not venda_interestadual:
            melhor_correspondencia['CST ICMS'] = '500'
            cfop_correto = '5405'
        
        return {
            'cfop_correto': cfop_correto,
            'cst_icms': melhor_correspondencia['CST ICMS'],
            'cst_pis_cofins': melhor_correspondencia['CST PIS COFINS']
        }

    return None