notas_processadas = set()
ncm_nao_encontrados = [['NCM', 'NOME ITEM', 'NUMERO DA NOTA', 'DATA DE EMISSÃO', 'VALOR DO PRODUTO']]
dados_por_periodo_e_cnpj = {}

def inicializar_dicionario_central_periodo_cnpj(periodo, cnpj):

    if periodo not in dados_por_periodo_e_cnpj:
        dados_por_periodo_e_cnpj[periodo] = {}

    if cnpj not in dados_por_periodo_e_cnpj[periodo]:
        dados_por_periodo_e_cnpj[periodo][cnpj] = {
            'valor_total_nfe': 0,
            'itens': [],
            'notas' : [],
            'dicionario_csts_corretos': {},
            'dicionario_csts_originais': {},
            'destinatarios' : {},
            'notas_que_nao_compoem_base' : [],
            'num_itens_processados' : 0,
            'emitente' : {},
            'unidades' : [],
            
            'dados_entradas' : {
                'num_notas_entrada' : 0,
                'creditos_por_entrada_icms' : 0,
                'emitentes' : {},
                'valor_total_nfe_entrada' : 0,
                'notas' : [],
                'itens' : [],
                'unidades' : set()
                
            },
            
            'dados_devolucao' : {
                'emitentes' : {},
                'valor_total_nfe_entrada' : 0,
                'notas' : [],
                'itens' : [],
                'unidades' : set()
            },
            
            'dados_cte' : {
                'notas' : [],
                'participantes' : {},
            }
        }