import requests
import re
import string

def sanitize(text):
    # Converte todo o texto para minúsculas
    text = text.lower()
    
    # Remove pontuações
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Remove espaços em branco
    text = text.strip()
    
    return text

# from core.services.utils import sanitize, jaccard_similarity

# VERIFICAR SEMELHANÇA ENTRE STRINGS
def jaccard_similarity(str1, str2):
    # Convert to lowercase and remove punctuation
    str1 = re.sub(r'[^\w\s]', '', str1.lower())
    str2 = re.sub(r'[^\w\s]', '', str2.lower())
    
    set1 = set(str1.split())
    set2 = set(str2.split())
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union)

# Consulta Alíquota Diferenciada ICMS
def consultar_api_aliquota_diferenciada_icms(dados_ncm):
    ncm = dados_ncm['ncm']
    estado = dados_ncm['estado']
    id_usuario = dados_ncm['id_usuario']
    token = dados_ncm['token']
    modo_busca = dados_ncm['modo_busca']
    url_aliq_icms = f'https://www.legisweb.com.br/api/icms/?ncm={ncm}&estado={estado}&c={id_usuario}&t={token}&modo_busca={modo_busca}'
    
    ncms_isentos = {
        "4901": "Livros, brochuras e impressos semelhantes, mesmo em folhas soltas - Em folhas soltas, mesmo dobradas",
        "49011000": "Livros, brochuras e impressos semelhantes, mesmo em folhas soltas - Outros: Dicionários e enciclopédias, mesmo em fascículos",
        "49019": "Livros, brochuras e impressos semelhantes, mesmo em folhas soltas - Outros: Outros",
        "49019100": "Jornais e publicações periódicas, impressos, mesmo ilustrados ou que contenham publicidade - Que se publiquem pelo menos quatro vezes por semana",
        "49019900": "Jornais e publicações periódicas, impressos, mesmo ilustrados ou que contenham publicidade - Que se publiquem pelo menos quatro vezes por semana: Com publicidade",
        "4902": "Jornais e publicações periódicas, impressos, mesmo ilustrados ou que contenham publicidade - Outros",
        "49021000": "Jornais e publicações periódicas, impressos, mesmo ilustrados ou que contenham publicidade - Outros: Com publicidade",
        "49021000": "Álbuns ou livros de ilustrações e álbuns para desenhar ou colorir, para crianças",
        "49029000": "Música manuscrita ou impressa, ilustrada ou não, mesmo encadernada",
        "49029000": "Obras cartográficas de qualquer espécie, incluindo as cartas murais, as plantas topográficas e os globos, impressas - Sob a forma de livros ou brochuras",
        "49030000": "Obras cartográficas de qualquer espécie, incluindo as cartas murais, as plantas topográficas e os globos, impressas - Outras",
        "49040000": "Obras cartográficas de qualquer espécie, incluindo as cartas murais, as plantas topográficas e os globos, impressas - Outras",
        "4905": "Obras cartográficas de qualquer espécie, incluindo as cartas murais, as plantas topográficas e os globos, impressas - Outras",
        "49052000": "Obras cartográficas de qualquer espécie, incluindo as cartas murais, as plantas topográficas e os globos, impressas - Outras",
        "49059000": "Obras cartográficas de qualquer espécie, incluindo as cartas murais, as plantas topográficas e os globos, impressas - Outras",
    }
    
    if ncm in ncms_isentos:
        resposta_api_icms = {
            'ncm_retornado' : ncm,
            'aliquota_icms_retornado' : 0,
            'descricao_icms_retornado' : 'Aliquota Zeo ou isenção com base no artigo Artigo 150, inciso VI, alínea d, da Constituição Federal. :',
            'base_legal_retornado' : 'Artigo 150, inciso VI, alínea d, da Constituição Federal.',
            'cst_icms' : '300 ou 400',
            'vigencia_inicial' : '?',
            'observacao_icms' : '?'
        }
        return resposta_api_icms
    else:
        try:
            resposta_aliq_icms = requests.get(url_aliq_icms)        
            retorno_aliq_icms = resposta_aliq_icms.json()

            # Verifica se existem registros
            if retorno_aliq_icms.get('registros', 0) == 0:
                resposta_api_icms = {
                'ncm_retornado' : ncm,
                'aliquota_icms_retornado' : 20.00,
                'descricao_icms_retornado' : 'Alíquota Interna Padrão para Distrito Federal:',
                'base_legal_retornado' : 'Base Legal: Alínea "c", Inciso II, Art. 18º da Lei Nº 1254 DE 08/11/1996',
                'cst_icms' : '101 ou 102',
                'vigencia_inicial' : '22/01/2024',
                'observacao_icms' : 'Para datas anteriores a Vigencia de 22/01/2024 a aliquota padrão era de 18%'
                }
                return resposta_api_icms
            else:
                # Pegando a última resposta
                resposta = retorno_aliq_icms['resposta'][-1]        
                resposta_api_icms = {
                    'ncm_retornado' : resposta.get('ncm', 'NCM não disponível'),
                    'aliquota_icms_retornado' : resposta.get('aliquota', 'Alíquota não disponível'),
                    'descricao_icms_retornado' : resposta.get('descricao', 'Descrição não disponível'),
                    'base_legal_retornado' : resposta.get('base_legal', 'Base legal não disponível'),
                    'vigencia_inicial' : resposta.get('vigencia_inicial', 'Vigencia Inicial não disponivel'),
                    'observacao_icms' : resposta.get('observacao', 'Observação não disponivel'),
                    'cst_icms' : '101 ou 102',
                }
                return resposta_api_icms
        except requests.exceptions.RequestException as e:
            resposta_api_icms = {
                'ncm_retornado' : ncm,
                'aliquota_icms_retornado' : 20.00,
                'descricao_icms_retornado' : 'Alíquota Interna Padrão para Distrito Federal:',
                'base_legal_retornado' : 'Base Legal: Alínea "c", Inciso II, Art. 18º da Lei Nº 1254 DE 08/11/1996',
                'cst_icms' : '101 ou 102',
                'vigencia_inicial' : '22/01/2024',
                'observacao_icms' : 'Para datas anteriores a Vigencia de 22/01/2024 a aliquota padrão era de 18%'
                }
                
            return resposta_api_icms
        except KeyError as e:
            print(f"Erro: A chave {e} não foi encontrada no JSON.")
            return None
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return None

# Consulta ST Interna
def consultar_api_st_interna(dados_ncm):
    atividade_origem = dados_ncm['atividade_origem']
    ncm = dados_ncm['ncm']
    estado = dados_ncm['estado']
    id_usuario = dados_ncm['id_usuario']
    token = dados_ncm['token']
    buscar_por_atividade = ''
    nome_item = dados_ncm['nome_item']
    url_api_st_interna = f'https://www.legisweb.com.br/api/st-interna/?ncm={ncm}&estado={estado}&c={id_usuario}&t={token}'

    if atividade_origem == 1:
        buscar_por_atividade = ["ATACADISTAS", "ATACADISTA", "ATACADO"]
    elif atividade_origem == 2:
        buscar_por_atividade = ["DISTRIBUIDORES", "DISTRIBUIDOR", "DISTRIBUIÇÃO"]
    elif atividade_origem == 3:
        buscar_por_atividade = ["FABRICANTES", "INDUSTRIAS", "INDUSTRIAL", "INDUSTRIA", "FABRICANTE"]
    elif atividade_origem == 4:
        buscar_por_atividade = ["VAREJISTAS", "VAREJISTA", "VAREJO"]
    
    resposta_api_st_interna = requests.get(url_api_st_interna)
    retorno_api_st_interna = resposta_api_st_interna.json()
    
    if isinstance(retorno_api_st_interna, list):
        dados_st = {
        'descricao' : 'NÃO TEM ST',
        'cest' : 'NÃO TEM ST',
        'descricao_ncm' : 'NÃO TEM ST',
        'mva' : 'NÃO TEM ST',
        'mva_ajustada_4' : 'NÃO TEM ST',
        'mva_ajustada_7' : 'NÃO TEM ST',
        'mva_ajustada_12' : 'NÃO TEM ST',
        'base_legal_st' : 'NÃO TEM ST',
        'cest' : 'NÃO TEM ST',
        'observacao' : 'NÃO TEM ST',
        'vigencia_inicial' : 'NÃO TEM ST',
        'segmento' : 'NÃO TEM ST',
        }
        return dados_st
    
    # Verificando se existem registros
    if retorno_api_st_interna.get('registros', 0) == 0:        
        dados_st = {
        'descricao' : 'NÃO TEM ST',
        'cest' : 'NÃO TEM ST',
        'descricao_ncm' : 'NÃO TEM ST',
        'mva' : 'NÃO TEM ST',
        'mva_ajustada_4' : 'NÃO TEM ST',
        'mva_ajustada_7' : 'NÃO TEM ST',
        'mva_ajustada_12' : 'NÃO TEM ST',
        'base_legal_st' : 'NÃO TEM ST',
        'cest' : 'NÃO TEM ST',
        'observacao' : 'NÃO TEM ST',
        'vigencia_inicial' : 'NÃO TEM ST',
        'segmento' : 'NÃO TEM ST',
        }

        return dados_st
    else:
        respostas = retorno_api_st_interna['resposta']
        maior_similaridade = -1
        resposta_mais_similar = None

        # Iterando corretamente sobre a lista de respostas
        for resposta in respostas:
            descricao = resposta['descricao']
            
            if any(sanitize(atividade) in sanitize(descricao) for atividade in buscar_por_atividade):
                
                similaridade = jaccard_similarity(nome_item, descricao) * 100
                                
                if similaridade > maior_similaridade:
                    maior_similaridade = similaridade
                    resposta_mais_similar = resposta
                
        if resposta_mais_similar :
            cest = resposta_mais_similar.get('cest', 'não tem cest')
            descricao_ncm = resposta_mais_similar.get('descricao', 'Descrição não disponível')
            mva = resposta_mais_similar.get('mva', '')
            mva_ajustada_4 = resposta_mais_similar.get('mva_ajustada_4', '')
            mva_ajustada_7 = resposta_mais_similar.get('mva_ajustada_7', '')
            mva_ajustada_12 = resposta_mais_similar.get('mva_ajustada_12', '')
            base_legal_st = resposta_mais_similar.get('base_legal_st', 'Base legal não disponível')
            observacao = resposta_mais_similar.get('observacao', '')
            vigencia_inicial = resposta_mais_similar.get('vigencia_inicial', '')
            segmento = resposta_mais_similar.get('segmento', '')
            
            dados_st = {
                'descricao' : nome_item,
                'cest' : cest,
                'descricao_ncm' : descricao_ncm,
                'mva' : mva,
                'mva_ajustada_4' : mva_ajustada_4,
                'mva_ajustada_7' : mva_ajustada_7,
                'mva_ajustada_12' : mva_ajustada_12,
                'base_legal_st' : base_legal_st,
                'vigencia_inicial' : vigencia_inicial,
                'observacao' : observacao,
                'segmento' : segmento,
            }
            return dados_st  
        else:
            respostas = retorno_api_st_interna['resposta']
            maior_similaridade = -1
            resposta_mais_similar = None

            # Iterando corretamente sobre a lista de respostas
            for resposta in respostas:
                descricao = resposta['descricao']
                similaridade = jaccard_similarity(nome_item, descricao) * 100
                 
                if similaridade > maior_similaridade:
                    maior_similaridade = similaridade
                    resposta_mais_similar = resposta
                    
            if resposta_mais_similar :
                cest = resposta_mais_similar.get('cest', 'não tem cest')
                descricao_ncm = resposta_mais_similar.get('descricao', 'Descrição não disponível')
                mva = resposta_mais_similar.get('mva', '')
                mva_ajustada_4 = resposta_mais_similar.get('mva_ajustada_4', '')
                mva_ajustada_7 = resposta_mais_similar.get('mva_ajustada_7', '')
                mva_ajustada_12 = resposta_mais_similar.get('mva_ajustada_12', '')
                base_legal_st = resposta_mais_similar.get('base_legal_st', 'Base legal não disponível')
                observacao = resposta_mais_similar.get('observacao', '')
                vigencia_inicial = resposta_mais_similar.get('vigencia_inicial', '')
                segmento = resposta_mais_similar.get('segmento', '')
                
                dados_st = {
                    'descricao' : nome_item,
                    'cest' : cest,
                    'descricao_ncm' : descricao_ncm,
                    'mva' : mva,
                    'mva_ajustada_4' : mva_ajustada_4,
                    'mva_ajustada_7' : mva_ajustada_7,
                    'mva_ajustada_12' : mva_ajustada_12,
                    'base_legal_st' : base_legal_st,
                    'vigencia_inicial' : vigencia_inicial,
                    'observacao' : observacao,
                    'segmento' : segmento,
                }
                return dados_st  

# Consulta ST Interestadual
def consultar_api_st_interestadual(dados_ncm):
    atividade_origem = dados_ncm['atividade_origem']
    ncm = dados_ncm['ncm']
    estado = dados_ncm['estado']
    id_usuario = dados_ncm['id_usuario']
    token = dados_ncm['token']
    buscar_por_atividade = ''
    nome_item = dados_ncm['nome_item']
    url_api_st_interestadual = f"https://www.legisweb.com.br/api/st-interestadual/?ncm={ncm}&estado_origem={estado}&estado_destino=GO&destinacao_mercadoria=1&c={id_usuario}&t={token}"
    
    if atividade_origem == 1:
        buscar_por_atividade = ["ATACADISTAS", "ATACADISTA", "ATACADO"]
    elif atividade_origem == 2:
        buscar_por_atividade = ["DISTRIBUIDORES", "DISTRIBUIDOR", "DISTRIBUIÇÃO"]
    elif atividade_origem == 3:
        buscar_por_atividade = ["FABRICANTES", "INDUSTRIAS", "INDUSTRIAL", "INDUSTRIA", "FABRICANTE"]
    elif atividade_origem == 4:
        buscar_por_atividade = ["VAREJISTAS", "VAREJISTA", "VAREJO"]
    
    resposta_api_st_interestadual = requests.get(url_api_st_interestadual)
    retorno_api_st_interestadual = resposta_api_st_interestadual.json()
    
    if isinstance(retorno_api_st_interestadual, list):
        dados_st = {
        'descricao' : 'NÃO TEM ST INTERESTADUAL',
        'cest' : 'NÃO TEM ST INTERESTADUAL',
        'descricao_ncm' : 'NÃO TEM ST INTERESTADUAL',
        'mva' : 'NÃO TEM ST INTERESTADUAL',
        'mva_ajustada_4' : 'NÃO TEM ST INTERESTADUAL',
        'mva_ajustada_7' : 'NÃO TEM ST INTERESTADUAL',
        'mva_ajustada_12' : 'NÃO TEM ST INTERESTADUAL',
        'base_legal_st' : 'NÃO TEM ST INTERESTADUAL',
        'cest' : 'NÃO TEM ST INTERESTADUAL',
        'observacao' : 'NÃO TEM ST INTERESTADUAL',
        'vigencia_inicial' : 'NÃO TEM ST INTERESTADUAL',
        'segmento' : 'NÃO TEM ST INTERESTADUAL',
        }

        return dados_st
    
    if retorno_api_st_interestadual.get('registros', 0) == 0:
        dados_st = {
        'descricao' : 'NÃO TEM ST INTERESTADUAL',
        'cest' : 'NÃO TEM ST INTERESTADUAL',
        'descricao_ncm' : 'NÃO TEM ST INTERESTADUAL',
        'mva' : 'NÃO TEM ST INTERESTADUAL',
        'mva_ajustada_4' : 'NÃO TEM ST INTERESTADUAL',
        'mva_ajustada_7' : 'NÃO TEM ST INTERESTADUAL',
        'mva_ajustada_12' : 'NÃO TEM ST INTERESTADUAL',
        'base_legal_st' : 'NÃO TEM ST INTERESTADUAL',
        'cest' : 'NÃO TEM ST INTERESTADUAL',
        'observacao' : 'NÃO TEM ST INTERESTADUAL',
        'vigencia_inicial' : 'NÃO TEM ST INTERESTADUAL',
        'segmento' : 'NÃO TEM ST INTERESTADUAL',
        }

        return dados_st
    else:
        respostas = retorno_api_st_interestadual['resposta']
        maior_similaridade = -1
        resposta_mais_similar = None

        # Iterando corretamente sobre a lista de respostas
        for resposta in respostas:
            descricao = resposta['descricao']
            
            if any(sanitize(atividade) in sanitize(descricao) for atividade in buscar_por_atividade):                
                similaridade = jaccard_similarity(nome_item, descricao) * 100
                                
                if similaridade > maior_similaridade:
                    maior_similaridade = similaridade
                    resposta_mais_similar = resposta
        
        if resposta_mais_similar :            
            dados_st = {
                'cest_st_interestadual' : resposta_mais_similar.get('cest', ''),
                'descricao_st_interestadual' : resposta_mais_similar.get('descricao', ''),
                'observacao_st_interestadual' : resposta_mais_similar.get('observacao', ''),
                'segmento_st_interestadual' : resposta_mais_similar.get('segmento', ''),
                'mva_original_st_interestadual' : resposta_mais_similar.get('mva', ''),
                'mva_ajustada_st_interestadual' : resposta_mais_similar.get('mva_ajustada', ''),
                'mva_ajustada_4_st_interestadual' : resposta_mais_similar.get('mva_ajustada_4', ''),
                'mva_ajustada_12_st_interestadual' : resposta_mais_similar.get('mva_ajustada_12', ''),
                'vigencia_inicial_st_interestadual' : resposta_mais_similar.get('vigencia_inicial', ''),
                'base_legal_st_interestadual' : resposta_mais_similar.get('base_legal_st', ''),
                'base_legal_int_st_interestadual' : resposta_mais_similar.get('base_legal_int', ''),
                'aplicabilidade_st_interestadual' : resposta_mais_similar.get('aplicabilidade', ''),
                'nao_aplicabilidade_st_interestadual' : resposta_mais_similar.get('nao_aplicabilidade', ''),
            }
            return dados_st  
        else:
            respostas = retorno_api_st_interestadual['resposta']
            maior_similaridade = -1
            resposta_mais_similar = None

            # Iterando corretamente sobre a lista de respostas
            for resposta in respostas:
                descricao = resposta['descricao']
                similaridade = jaccard_similarity(nome_item, descricao) * 100
                 
                if similaridade > maior_similaridade:
                    maior_similaridade = similaridade
                    resposta_mais_similar = resposta
                    
            if resposta_mais_similar :
                dados_st = {
                'cest_st_interestadual' : resposta_mais_similar.get('cest', ''),
                'descricao_st_interestadual' : resposta_mais_similar.get('descricao', ''),
                'observacao_st_interestadual' : resposta_mais_similar.get('observacao', ''),
                'segmento_st_interestadual' : resposta_mais_similar.get('segmento', ''),
                'mva_original_st_interestadual' : resposta_mais_similar.get('mva', ''),
                'mva_ajustada_st_interestadual' : resposta_mais_similar.get('mva_ajustada', ''),
                'mva_ajustada_4_st_interestadual' : resposta_mais_similar.get('mva_ajustada_4', ''),
                'mva_ajustada_12_st_interestadual' : resposta_mais_similar.get('mva_ajustada_12', ''),
                'vigencia_inicial_st_interestadual' : resposta_mais_similar.get('vigencia_inicial', ''),
                'base_legal_st_interestadual' : resposta_mais_similar.get('base_legal_st', ''),
                'base_legal_int_st_interestadual' : resposta_mais_similar.get('base_legal_int', ''),
                'aplicabilidade_st_interestadual' : resposta_mais_similar.get('aplicabilidade', ''),
                'nao_aplicabilidade_st_interestadual' : resposta_mais_similar.get('nao_aplicabilidade', ''),
                }
                return dados_st  
# Consulta PIS/COFINS

def consultar_api_pis_cofins(dados_ncm):
    ncm = dados_ncm['ncm']
    id_usuario = dados_ncm['id_usuario']
    token = dados_ncm['token']
    regime_tributario_origem = dados_ncm['regime_tributario_origem']
    atividade_origem = dados_ncm['atividade_origem']
    atividade_destino = dados_ncm['atividade_destino']
    aliquota_padrao = dados_ncm['aliquota_padrao']

    url_aliq_pis_cofins = (f'https://www.legisweb.com.br/api/piscofins/?ncm={ncm}&c={id_usuario}&t={token}'
        f'&regime_tributario_origem={regime_tributario_origem}&atividade_origem={atividade_origem}'
        f'&atividade_destino={atividade_destino}&aliquota_padrao={aliquota_padrao}'
    )
    
    try:
        # Realizando a requisição
        retorno_aliq_pis_cofins = requests.get(url_aliq_pis_cofins)     
        print('RETORNO PIS COFINS =>', retorno_aliq_pis_cofins)   
        retorno_aliq_pis_cofins = retorno_aliq_pis_cofins.json()
        
        # Verifica se retorno_aliq_pis_cofins é do tipo lista
        if isinstance(retorno_aliq_pis_cofins, list):
            # Cria um dicionário com as informações necessárias
            dados_pís_cofins = {
                'ncm': ncm,  # Presume-se que 'ncm' está definido anteriormente
                'cst_simples': '49 - Outras Operações de Saída ou 99 - Outras Operações',
                'base_legal': 'Resolução CGSN Nº 140 DE 22/05/2018, Lei Complementar Nº 123 DE 14/12/2006.'
            }
            
            # Retorna o dicionário
            return dados_pís_cofins
        
        if retorno_aliq_pis_cofins.get('registros', 0) == 0:
            dados_pís_cofins ={
            'ncm' : ncm,
            'cst_simples' : '49 - Outras Operações de Saída ou 99 - Outras Operações',
            'base_legal' : 'Resolução CGSN Nº 140 DE 22/05/2018, Lei Complementar Nº 123 DE 14/12/2006.'
            }
            
            return dados_pís_cofins
        
        # Extraindo os valores de 'cst_simples'
        print('--'*50)
        for resposta in retorno_aliq_pis_cofins['resposta']:
            # print(retorno_aliq_pis_cofins)
            trib_list = resposta['trib']  # Acesso ao campo 'trib', que é uma lista
            for trib in trib_list:  # Iterando sobre os itens da lista 'trib'
                cst_simples = trib.get('cst_simples', 'Valor não encontrado')
                base_legal = trib.get('descricao_base_legal', 'Valor não encontrado')

        if cst_simples == '04 - Operação tributável Monofásica - Revenda a alíquota Zero':
            base_legal = (
                'Resolução CGSN Nº 140 DE 2018, art. 25, § 6º, e Lei Complementar Nº 123 DE 2006, art. 2º.'
            )
        elif cst_simples == '49 - Outras Operações de Saída ou 99 - Outras Operações':
            base_legal = (
                'Resolução CGSN Nº 140 DE 22/05/2018, Lei Complementar Nº 123 DE 14/12/2006.'
            )
        elif cst_simples == '05 - Operação tributável por Substituição Tributária':
            base_legal = (
                'Resolução CGSN Nº 140 DE 2018, art. 25, § 6º, e Lei Complementar Nº 123 DE 2006, art. 2º.'
            )
        elif sanitize(cst_simples) == sanitize('06 - Operação Tributável a Alíquota Zero'):
            base_legal = base_legal
        # else:
        #     base_legal = (
        #         'ASAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
        #     )
            
        dados_pís_cofins ={
            'ncm' : ncm,
            'cst_simples' : cst_simples,
            'base_legal' : base_legal
        }
            
        return dados_pís_cofins
    
    except requests.exceptions.RequestException as e:
        dados_pís_cofins ={
            'ncm' : ncm,
            'cst_simples' : '49 - Outras Operações de Saída ou 99 - Outras Operações',
            'base_legal' : 'Resolução CGSN Nº 140 DE 22/05/2018, Lei Complementar Nº 123 DE 14/12/2006.'
            }
        return dados_pís_cofins

# Consulta Benefícios Fiscais (Isenção)
def consultar_api_beneficios_fiscais_isencao(dados_ncm):
    nome_item = dados_ncm['nome_item']
    ncm = dados_ncm['ncm']
    estado = dados_ncm['estado']
    id_usuario = dados_ncm['id_usuario']
    token = dados_ncm['token']

    url_api_beneficios_fiscais_isencao = f'https://www.legisweb.com.br/api/beneficio-fiscal/?estado={estado}&c={id_usuario}&t={token}&categoria=3&descricao={nome_item}&ncm={ncm}'

    try:
        resposta_api_beneficios_fiscais_isencao = requests.get(url_api_beneficios_fiscais_isencao)
        resposta_api_beneficios_fiscais_isencao = resposta_api_beneficios_fiscais_isencao.json()

        # # Verificando se existem registros
        if resposta_api_beneficios_fiscais_isencao.get('registros', 0) == 0:
            print(f"O NCM {ncm} NÃO POSSUI BENEFÍCIOS DE ISENÇÃO")
            return None
    except KeyError as e:
        print(f"Erro ao acessar chave no JSON: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
