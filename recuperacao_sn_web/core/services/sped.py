from datetime import datetime, timedelta
import pandas as pd
from MODULES.alterador_sped import alterar_sped
from MODULES.utilitarios import jaccard_similarity
from MODULES.config import generos, cst_icms_nao_compoe_simples, cfops_nao_compoe_simples
from functools import lru_cache
import json
import os

global qtd_linhas_arquivo, contador_blocos

contador_registros = {}
contador_blocos = {}
contador_csts = {}
qtd_linhas_arquivo = 0
naturezas = []
tipo_item_cache = {}



@lru_cache()
def get_tipi_df():
    import pandas as pd
    return pd.read_excel('_RECURSOS/tipi.xlsx')

def formata_valor(valor):
    try:
        return f"{float(valor):.2f}".replace('.', ',')
    except (TypeError, ValueError):
        print(TypeError, valor)
        return "0,00"

def gerar_bloco_9(arquivo):
    global qtd_linhas_arquivo
    qtd_registros_9900 = 0
    contar_e_escrever('|9001|0|', arquivo)
    
    for tipo_registro, quantidade in contador_registros.items():
        arquivo.write(f"|9900|{tipo_registro}|{quantidade}|\n")
        qtd_linhas_arquivo += 1
        qtd_registros_9900 += 1
        contador_blocos['9'] += 1 
    
    arquivo.write(f'|9900|9999|1|\n')
    arquivo.write(f'|9900|9990|1|\n')
    arquivo.write(f'|9900|9900|{qtd_registros_9900 + 3}|\n')
    arquivo.write(f'|9990|{contador_blocos['9'] + 5}|\n')
    arquivo.write(f'|9999|{qtd_linhas_arquivo + 5}|\n')
    
    # print(contador_registros)
    # print(contador_blocos)
    
    contador_registros.clear()
    contador_blocos.clear()
    qtd_linhas_arquivo = 0
    
def contar_e_escrever(registro, arquivo):
    global qtd_linhas_arquivo, contador_blocos

    tipo_registro = registro.split('|')[1]
    bloco_registro = tipo_registro[0]
    
    if bloco_registro in contador_blocos :
        contador_blocos[bloco_registro] +=1
    else:
        contador_blocos[bloco_registro] = 1
    
    if tipo_registro in contador_registros :
        contador_registros[tipo_registro] += 1
    else :
        contador_registros[tipo_registro] = 1
        
    arquivo.write(f'{registro}\n')
    qtd_linhas_arquivo += 1 

def formatar_data(data_iso):
    """
    Converte uma data no formato ISO 8601 (YYYY-MM-DDTHH:MM:SS±HH:MM)
    para o formato DDMMAAAA.
    
    :param data_iso: String da data no formato ISO 8601.
    :return: String da data no formato DDMMAAAA.
    """
    try:
        # Parse da string ISO 8601 para um objeto datetime
        data = datetime.fromisoformat(data_iso)
        # Formatar a data no formato DDMMAAAA
        return data.strftime('%d%m%Y')
    except ValueError:
        raise ValueError(f"Formato de data inválido: {data_iso}")

def obter_primeiro_e_ultimo_dia(mes_ano):
    mes, ano = map(int, mes_ano.split("_"))
    primeiro_dia = datetime(ano, mes, 1)
    ultimo_dia = (primeiro_dia + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    return primeiro_dia.strftime("%d%m%Y"), ultimo_dia.strftime("%d%m%Y")

def determinar_tipo_item(ncm, cfop, descricao):
    # Regras baseadas no CFOP
    if cfop.startswith('5') or cfop.startswith('6'):
        if cfop in ['5405', '5102']:  # Exemplos de CFOP para revenda
            return "00"  # Mercadoria para Revenda
        elif cfop in ['5101', '5401']:  # Exemplos de CFOP para matéria-prima
            return "01"  # Matéria-Prima
    elif cfop.startswith('1') or cfop.startswith('2'):
        return "07"  # Material de Uso e Consumo

    # Regras baseadas no NCM
    if ncm.startswith('32'):  # Tintas, vernizes
        return "00"  # Mercadoria para Revenda

    # Caso nenhuma regra seja satisfeita
    return "99"  # Outras

def determinar_tipo_item_cached(ncm, cfop, descricao):
    chave = (ncm, cfop, descricao)
    if chave in tipo_item_cache:
        return tipo_item_cache[chave]
    
    tipo = determinar_tipo_item(ncm, cfop, descricao)  # sua função original
    tipo_item_cache[chave] = tipo
    return tipo

def buscar_codigo_ex_tipi(ncm):
    ncm_formatado = f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}"
    df = get_tipi_df()
    linha = df[df['NCM'] == ncm_formatado]
    if not linha.empty:
        codigo_ex = linha.iloc[0]['EX']
        return str(codigo_ex) if pd.notnull(codigo_ex) else '0'
    return '0'

def buscar_codigo_genero(descricao):
    max_similaridade = 0
    melhor_correspondencia = None
    
    for codigo, descricao_genero in generos.items():
        similaridade = jaccard_similarity(descricao, descricao_genero)
        if similaridade > max_similaridade:
            max_similaridade = similaridade
            melhor_correspondencia = codigo
    if melhor_correspondencia :
        return melhor_correspondencia
    else :
        return ''

def gerar_registro_0000(periodo, razao_social, cnpj, inscricao_estadual, uf, cod_municipio, arquivo):
    data_inicial, data_final = obter_primeiro_e_ultimo_dia(periodo)
    ano = data_inicial[-4:]
    layout = ''
    
    if ano == '2020':
        layout = '014'
    elif ano == '2021':
        layout = '015'
    elif ano == '2022':
        layout = '016'
    elif ano == '2023':
        layout = '017'
    elif ano == '2024':
        layout = '018'
    elif ano == '2025':
        layout = '019'
    
    registro = f"|0000|{layout}|1|{data_inicial}|{data_final}|{razao_social}|{cnpj}||{uf}|{inscricao_estadual}|{cod_municipio}|||A|1|"
    contar_e_escrever(registro, arquivo)

def gerar_registro_0001(arquivo):
    registro = '|0001|0|'
    contar_e_escrever(registro, arquivo)

def gerar_registro_0005(nome_fantasia, cep, logradouro, numero_logradouro, bairro, telefone, arquivo):
    
    if telefone == None:
        telefone = ''
    elif len(telefone) == 8:
        telefone = f'61{telefone}'
    
    registro = f"|0005|{nome_fantasia}|{cep}|{logradouro}|{numero_logradouro}||{bairro}|{telefone}|||"
    contar_e_escrever(registro, arquivo)

def gerar_registro_0100(arquivo):
    # Dados do contabilista responsável (registro 0100), lidos de variáveis de ambiente.
    contabilista = {
        'nome': os.getenv('SPED_CONTABILISTA_NOME', 'NOME DO CONTABILISTA'),
        'cpf': os.getenv('SPED_CONTABILISTA_CPF', '00000000000'),
        'crc': os.getenv('SPED_CONTABILISTA_CRC', '000000O'),
        'cnpj': os.getenv('SPED_CONTABILISTA_CNPJ', ''),
        'cep': os.getenv('SPED_CONTABILISTA_CEP', '00000000'),
        'endereco': os.getenv('SPED_CONTABILISTA_ENDERECO', 'ENDERECO'),
        'bairro': os.getenv('SPED_CONTABILISTA_BAIRRO', 'BAIRRO'),
        'fone': os.getenv('SPED_CONTABILISTA_FONE', ''),
        'email': os.getenv('SPED_CONTABILISTA_EMAIL', 'contato@example.com'),
        'cod_mun': os.getenv('SPED_CONTABILISTA_COD_MUN', '5300108'),
    }
    registro = (
        f"|0100|{contabilista['nome']}|{contabilista['cpf']}|{contabilista['crc']}|{contabilista['cnpj']}|"
        f"{contabilista['cep']}|{contabilista['endereco']}|||"
        f"{contabilista['bairro']}|{contabilista['fone']}||{contabilista['email']}|{contabilista['cod_mun']}|"
    )
    contar_e_escrever(registro, arquivo)

def gerar_registro_0150(destinatarios, arquivo):
    mapa_codigos = {}  # Dicionário para armazenar o mapeamento
    for index, (cnpj_destinatario, dados_destinatario) in enumerate(destinatarios.items(), start=1):
        codigo = f"MPHDEST{index:04}"  # Código único baseado no índice
        razao_social_destinatario = dados_destinatario['razao_social']
        codigo_pais_destinatario = dados_destinatario['codigo_pais']
        inscricao_estadual_destinatario = dados_destinatario['inscricao_estadual']
        codigo_municipio_destinatario = dados_destinatario['codigo_municipio']
        logradouro_destinatario = dados_destinatario['logradouro']
        numero_logradouro_destinatario = dados_destinatario['numero_logradouro']
        bairro_destinatario = dados_destinatario['bairro']
        
        if codigo_pais_destinatario == "" :
            codigo_pais_destinatario = "1058"
        
        if len(cnpj_destinatario) == 14 :
            registro = f"|0150|{codigo}|{razao_social_destinatario}|{codigo_pais_destinatario}|{cnpj_destinatario}||{inscricao_estadual_destinatario}|{codigo_municipio_destinatario}||{logradouro_destinatario}|{numero_logradouro_destinatario}||{bairro_destinatario}|"
        else :
            registro = f"|0150|{codigo}|{razao_social_destinatario}|{codigo_pais_destinatario}||{cnpj_destinatario}|{inscricao_estadual_destinatario}|{codigo_municipio_destinatario}||{logradouro_destinatario}|{numero_logradouro_destinatario}||{bairro_destinatario}|"

        contar_e_escrever(registro, arquivo)

        # Adiciona o mapeamento CNPJ/CPF -> Código
        mapa_codigos[cnpj_destinatario] = codigo

    return mapa_codigos
        
def gerar_registro_0190(unidades, arquivo):
    unidades_unicas = []
    
    for unidade in unidades:        
        if unidade not in unidades_unicas :
            unidades_unicas.append(unidade)
            registro = f'|0190|{unidade}|Unidade Importada Nfe|'
            contar_e_escrever(registro, arquivo)

def gerar_registro_0200(itens, arquivo):
    itens_unicos = {}

    for index, item in enumerate(itens, start=1):
        # Gera um identificador único (por exemplo, com NCM + Nome)
        identificador = f"{item['ncm']}-{item['nome_item_nota']}"
        codigo = f"MPHPROD{index:04}"

        if identificador not in itens_unicos:
            
            tipo_item = determinar_tipo_item_cached(item['ncm'], item['cfop'], item['nome_item_nota'])
            codigo_ex = buscar_codigo_ex_tipi(item['ncm'])
            codigo_genero = buscar_codigo_genero(item['nome_item_nota'])

            # Adiciona o item ao dicionário de itens únicos
            itens_unicos[identificador] = codigo
                        
            # print(item)
            # Formata o registro 0200
            registro = f"|0200|{codigo}|{item['nome_item_nota']}|{item['codigo_barras']}||{item['unidade'].upper().replace(' ', '')}|{tipo_item}|{item['ncm']}|{codigo_ex}|{codigo_genero}||{formata_valor(item['aliq_icms'])}|{item['cest']}|"

            # Escreve o registro no arquivo
            contar_e_escrever(registro, arquivo)

    return itens_unicos

def gerar_registro_0400(naturezas, arquivo):
    naturezas_unicas = {}
    
    for index, natureza in enumerate(naturezas) :
        natureza = natureza.lower()
        
        if natureza not in naturezas_unicas:
            codigo = f"MPHNAT{index:04}"
            
            naturezas_unicas[natureza] = codigo

            registro = f"|0400|{codigo}|{natureza}|"
            
            contar_e_escrever(registro, arquivo)
    
    return naturezas_unicas
    
def gerar_registro_c170(nota, mapa_codigos_items, mapa_codigos_naturezas, arquivo):
    natureza = nota['natureza_operação']
    codigo_natureza = ''

    for item in nota['itens']:
        identificador = f"{item['ncm']}-{item['nome_item_nota']}"
        codigo_item = mapa_codigos_items.get(identificador, "")
        
        if item['situacao_tributaria_icms'] == "00":
            cst_icms = "000"
        elif item['situacao_tributaria_icms'] == "101 ou 102":
            cst_icms = "102"
        else :
            cst_icms = item['situacao_tributaria_icms']
            
        if cst_icms == "00":
                cst_icms = "000"
        if cst_icms == "10":
            cst_icms = "010"
        if cst_icms == "60":
            cst_icms = "060"
        if cst_icms == "30":
            cst_icms = "030"
            
        if item['cfop'] == '2101':
            item['cfop'] = '2102'
            
        gerar_registro_c170 = (
            f"|C170|{item['numero_item']}|{codigo_item}|{item['nome_item_nota']}|"
            f"{formata_valor(item['quantidade_item'])}|{item['unidade'].upper().replace(' ', '')}|{formata_valor(item['valor_unitario'])}|"
            f"{formata_valor(item['desconto_item_nota'])}|1|{cst_icms}|{item['cfop']}|{codigo_natureza}|"
            # f"0,00|0,00|0,00|0,00|0,00|0,00||||0,00|0,00|0,00||0,00|0,00|||0,00||0,00|0,00|||0,00|||"
            # f"{formata_valor(item['base_calculo_icms'])}|{formata_valor(item['aliq_icms'])}|{formata_valor(item['valor_icms'])}|{formata_valor(item['bc_icms_st'])}|{formata_valor(item['aliq_icms_st'])}|{formata_valor(item['valor_icms_st'])}|1|"
            f"{formata_valor(item['base_calculo_icms'])}|{formata_valor(item['aliq_icms'])}|{formata_valor(item['valor_icms'])}|0,00|0,00|0,00|1|"
            f"||0,00|{formata_valor(item['aliq_ipi'])}|{formata_valor(item['valor_ipi'])}|"
            f"{item['cst_pis']}|{formata_valor(item['base_calculo_pis'])}|{formata_valor(item['aliq_pis'])}|||{formata_valor(item['valor_pis'])}|{item['cst_cofins']}|{formata_valor(item['base_calculo_cofins'])}|{formata_valor(item['aliq_cofins'])}|||{formata_valor(item['valor_cofins'])}|||"
        )

        contar_e_escrever(gerar_registro_c170, arquivo)

def normalizar_cst(cst):
    mapeamento = {
        "00": "000",
        "10": "010",
        "101 ou 102": "102",
        "60": "060",
        "30": "030"
    }
    return mapeamento.get(cst, cst)

def processar_itens(nota, periodo, cnpj, incluir_base_icms=False):
    consolidados = {}
    valor_total_c190 = 0

    for item in nota['itens']:
        # Determinar CFOP e CST
        if nota['indicador_operacao'] == '1' and item['cfop'] not in cfops_nao_compoe_simples:
            cst_icms = item['cst_icms_correto']
            cfop = item['cfop_correto']
        else:
            cst_icms = item['cst_icms']
            cfop = item['cfop']

        cst_icms = normalizar_cst(cst_icms)
        aliq_icms = formata_valor(item['aliq_icms'])
        
        chave = (cst_icms, cfop, aliq_icms)

        if chave not in consolidados:
            consolidados[chave] = {
                'VL_OPR': 0,
                'VL_BC_ICMS': 0 if incluir_base_icms else '0,00',
                'VL_ICMS': 0 if incluir_base_icms else '0,00',
                # 'VL_BC_ICMS_ST': 0 if incluir_base_icms else '0,00',
                # 'VL_ICMS_ST': 0 if incluir_base_icms else '0,00',
                'VL_BC_ICMS_ST': '0,00',
                'VL_ICMS_ST': '0,00',
                'VL_RED_BC': '0,00',
                'VL_IPI': '0,00'
            }

        # Atualiza contador seguro
        chave_contador = f'{cst_icms}_{cfop}'
        contador_csts[periodo][cnpj][chave_contador] = contador_csts[periodo][cnpj].get(chave_contador, 0) + item['valor']

        consolidados[chave]['VL_OPR'] += item['valor']
        valor_total_c190 += item['valor']

        if incluir_base_icms:
            bc_icms = float(str(item['base_calculo_icms']).replace(',', '.'))
            vl_icms = float(str(item['valor_icms']).replace(',', '.'))
            # bc_icms_st = float(str(item['bc_icms_st']).replace(',', '.'))
            # vl_icms_st = float(str(item['valor_icms_st']).replace(',', '.'))
            consolidados[chave]['VL_BC_ICMS'] += bc_icms
            consolidados[chave]['VL_ICMS'] += vl_icms
            # consolidados[chave]['VL_BC_ICMS_ST'] += bc_icms_st
            # consolidados[chave]['VL_ICMS_ST'] += vl_icms_st

    return consolidados, valor_total_c190

def gerar_registro_c190(nota, arquivo, periodo, cnpj):
    valor_total_nota = nota['valor_total']

    if nota['indicador_operacao'] not in ['0', '1']:
        return  # ignora notas com indicador inválido

    incluir_base_icms = nota['indicador_operacao'] == '0'
    consolidados, valor_total_c190 = processar_itens(nota, periodo, cnpj, incluir_base_icms)

    diferenca = float(valor_total_nota) - float(valor_total_c190)
    if diferenca > 0:
        print(' DIFERENÇA ENTRE NOTA =>', diferenca)

    registros = list(consolidados.items())
    if registros and diferenca > 0:
        ultima_chave, ultimos_valores = registros[-1]
        ultimos_valores['VL_OPR'] += diferenca
        registros[-1] = (ultima_chave, ultimos_valores)

    for (cst_icms, cfop, aliq_icms), valores in registros:
        registro = (
            f"|C190|{cst_icms}|{cfop}|{aliq_icms}|"
            f"{str(round(valores['VL_OPR'], 2)).replace('.', ',')}|"
        )

        if incluir_base_icms:
            registro += (
                f"{str(round(valores['VL_BC_ICMS'], 2)).replace('.', ',')}|"
                f"{str(round(valores['VL_ICMS'], 2)).replace('.', ',')}|"
                # f"{str(round(valores['VL_BC_ICMS_ST'], 2)).replace('.', ',')}|"
                # f"{str(round(valores['VL_ICMS_ST'], 2)).replace('.', ',')}|"
            )
        else:
            registro += (f"{valores['VL_BC_ICMS']}|{valores['VL_ICMS']}|"
                        # f"{valores['VL_BC_ICMS_ST']}|{valores['VL_ICMS_ST']}|"
            )

        registro += (
            f"{valores['VL_BC_ICMS_ST']}|{valores['VL_ICMS_ST']}|"
            f"{valores['VL_RED_BC']}|{valores['VL_IPI']}||"
        )
        contar_e_escrever(registro, arquivo)

def gerar_registro_c100(notas_saida, mapa_codigos, arquivo, dicionario_csts_originais, dicionario_csts_corretos, periodo, cnpj, mapa_codigos_itens, mapa_codigos_naturezas):
    for nota in notas_saida:
        cnpj_destinatario = nota['cnpj_destinatario']
        codigo_participante = mapa_codigos.get(cnpj_destinatario, "")
        data_formatada = formatar_data(nota['data_emissao'])
        if nota['indicador_operacao'] == '1':
        
            registro = (
                f"|C100|1|0|{codigo_participante}|{nota['modelo']}|00|{nota['serie']}|{nota['numero']}|{nota['chave']}|"
                f"{data_formatada}|{data_formatada}|"
                f"{str(nota['valor_total']).replace('.', ',')}|{nota['tipo_pagamento']}|"
                f"{str(nota['valor_desconto']).replace('.', ',')}|0,00|{str(nota['valor_total']).replace('.', ',')}|{nota['tipo_frete']}|"
                f"{str(nota['valor_frete']).replace('.', ',')}|{str(nota['valor_seguro']).replace('.', ',')}|"
                f"{str(nota['valor_outros']).replace('.', ',')}|0,00|||||||||"
                # f"0,00|0,00|"
                # f"0,00||"
                # f"0,00|0,00|"
                # f"0,00|0,00|"
            )
            
            contar_e_escrever(registro, arquivo)

            gerar_registro_c190(nota, arquivo, periodo, cnpj)

        if nota['indicador_operacao'] == '0':
            
            soma_total_itens = sum(float(item['valor_unitario']) for item in nota['itens'])
            total_nota = float(nota['valor_total'])

            if soma_total_itens > total_nota:
                nota['valor_mercadorias'] = soma_total_itens 
            else :
                nota['valor_mercadorias'] = total_nota 
                
            registro = (
                f"|C100|0|1|{codigo_participante}|{nota['modelo']}|00|{nota['serie']}|{nota['numero']}|{nota['chave']}|"
                f"{data_formatada}|{data_formatada}|"
                f"{str(nota['valor_total']).replace('.', ',')}|{nota['tipo_pagamento']}|"
                f"{str(nota['valor_desconto']).replace('.', ',')}|0,00|{formata_valor(nota['valor_mercadorias'])}|{nota['tipo_frete']}|"
                f"{str(nota['valor_frete']).replace('.', ',')}|{str(nota['valor_seguro']).replace('.', ',')}|"
                f"{str(nota['valor_outros']).replace('.', ',')}|{str(nota['valor_bc_icms']).replace('.', ',')}|"
                # f"{str(nota['valor_icms']).replace('.', ',')}|{str(nota['valor_bc_icms_st']).replace('.', ',')}|{str(nota['valor_icms_st']).replace('.', ',')}||{str(nota['valor_pis']).replace('.', ',')}|{str(nota['valor_cofins']).replace('.', ',')}|||"
                f"{str(nota['valor_icms']).replace('.', ',')}|0,00|0,00||{str(nota['valor_pis']).replace('.', ',')}|{str(nota['valor_cofins']).replace('.', ',')}|||"
            )
            
            contar_e_escrever(registro, arquivo)
            
            gerar_registro_c170(nota, mapa_codigos_itens, mapa_codigos_naturezas, arquivo)

            gerar_registro_c190(nota, arquivo, periodo, cnpj)

def gerar_registro_d100(notas, arquivo, mapa_codigo_participante):
    
    for nota in notas:
        dados_participante = nota['participante']
        
        
        cnpj_participante = nota['cnpj_participante']
        codigo_participante = mapa_codigo_participante.get(cnpj_participante, "")
        # registro = (f"|D100|{nota['indicador_operacao']}|{nota['indicador_emitente']}|{codigo_participante}|"
        #             f"{nota['modelo']}|{nota['situacao']}|{nota['serie']}|{nota['subserie']}|{nota['numero']}|{nota['chave']}|{nota['data'].replace('/','')}|"
        #             f"{nota['data_recebimento'].replace('/','')}|{nota['tipo_cte']}|{nota['cte_referencia']}|{formata_valor(nota['valor_total_nota'])}|{formata_valor(nota['valor_total_desconto'])}|{nota['tipo_frete']}|"
        #             f"{formata_valor(nota['valor_total_nota'])}|{formata_valor(nota['bc_icms'])}|{formata_valor(nota['valor_icms'])}|{formata_valor(nota['valor_nao_tributado'])}|||{dados_participante['codigo_municipio']}|{nota['codigo_municipio_destinatario']}|")
        
        registro = (f"|D100|{nota['indicador_operacao']}|{nota['indicador_emitente']}|{codigo_participante}|"
                    f"{nota['modelo']}|{nota['situacao']}|{nota['serie']}|{nota['subserie']}|{nota['numero']}|{nota['chave']}|{nota['data'].replace('/','')}|"
                    f"{nota['data_recebimento'].replace('/','')}|{nota['tipo_cte']}|{nota['cte_referencia']}|{formata_valor(nota['valor_total_nota'])}|{formata_valor(nota['valor_total_desconto'])}|{nota['tipo_frete']}|"
                    f"{formata_valor(nota['valor_total_nota'])}|0,00|0,00|{formata_valor(nota['valor_nao_tributado'])}|||{dados_participante['codigo_municipio']}|{nota['codigo_municipio_destinatario']}|")
        
        contar_e_escrever(registro, arquivo)
        
        gerar_registro_d190(nota, arquivo)
        
def gerar_registro_d190(nota, arquivo):
    if nota['cst_icms'] == '00':
        nota['cst_icms'] = '000'
    if nota['cst_icms'] == '60':
        nota['cst_icms'] = '060'
        
    cfop = nota['cfop']

    if cfop[0] == "5":
        cfop = "1" + cfop[1:]
    elif cfop[0] == "6":
        cfop = "2" + cfop[1:]
    elif cfop[0] == "7":
        cfop = "3" + cfop[1:]
    
    if cfop == "1405":
        cfop = "1403"
    
    # registro = f"|D190|{nota['cst_icms']}|{cfop}|{formata_valor(nota['aliquota_icms'])}|{formata_valor(nota['bc_icms'])}|{formata_valor(nota['bc_icms'])}|{formata_valor(nota['valor_icms'])}|0,00||"
    registro = f"|D190|{nota['cst_icms']}|{cfop}|0,00|0,00|0,00|0,00|0,00||"
    
    contar_e_escrever(registro, arquivo)
    
def gerar_arquivo_sped(dados):
    global contador_csts
    contador_csts = {}  # Inicializa o dicionário global
    
    os.makedirs('SPED', exist_ok=True)
    
    def converter_sets_para_listas(dado):
        if isinstance(dado, set):
            return list(dado)  # Converte set para lista
        elif isinstance(dado, dict):
            return {chave: converter_sets_para_listas(valor) for chave, valor in dado.items()}
        elif isinstance(dado, list):
            return [converter_sets_para_listas(item) for item in dado]
        return dado

    with open("arquivo_sped.json", "w", encoding="utf-8") as teste:
        json.dump(converter_sets_para_listas(dados), teste, indent=4, ensure_ascii=False)
    
    for periodo, dados_periodo in dados.items():
        
        contador_csts[periodo] = {}  # Inicializa o dicionário para o período
        
        for cnpj, dados_cnpj in dados_periodo.items():
            contador_csts[periodo][cnpj] = {}  # Inicializa o dicionário para o CNPJ
            
            nome_arquivo = f"SPED/sped_retificador_{cnpj}_{periodo}.txt"
            
            data_inicial, data_final = obter_primeiro_e_ultimo_dia(periodo)
            emitente = dados_cnpj['emitente']
            razao_social_emitente = emitente['razao_social']
            nome_fantasia_emitente = emitente['nome_fantasia']
            inscricao_estadual_emitente = emitente['inscricao_estadual']
            uf_emitente = emitente['UF']
            codigo_municipio_emitente = emitente['codigo_municipio']
            cep_emitente = emitente['cep']
            logradouro_emitente = emitente['logradouro']
            numero_logradouro_emitente = emitente['numero_logradouro']
            bairro_emitente = emitente['bairro']
            telefone_emitente = emitente['telefone']
            creditos_icms = dados_cnpj['dados_entradas']['creditos_por_entrada_icms']

            itens = dados_cnpj['dados_entradas']['itens']
            
            unidades = []
            
            for unidade in dados_cnpj['dados_entradas']['unidades']:                
                unidades.append(unidade.upper().replace(' ', ''))
            
            notas = dados_cnpj['notas']
            destinatarios = dados_cnpj['destinatarios']
            notas_que_nao_compoem_base = dados_cnpj['notas_que_nao_compoem_base']
            dicionario_csts_originais = dados_cnpj['dicionario_csts_originais']
            dicionario_csts_corretos = dados_cnpj['dicionario_csts_corretos']
            
            notas_cte = dados_cnpj['dados_cte']['notas']
            
            for nota in dados_cnpj['dados_entradas']['notas']:
                notas.append(nota)
            
            for nota in dados_cnpj['dados_devolucao']['notas']:
                notas.append(nota)
                natureza_operacao = nota['natureza_operação']
                if natureza_operacao not in naturezas:
                    naturezas.append(natureza_operacao)
            
            for nota in notas_que_nao_compoem_base:
                notas.append(nota)
                for (cnpj_destinatario, dados_destinatario) in nota['destinatarios'].items():
                    destinatarios[cnpj_destinatario] = dados_destinatario
            
            for cnpj_emitente, dados_emitente in dados_cnpj['dados_entradas']['emitentes'].items():
                destinatarios[cnpj_emitente] = dados_emitente
            
            for cnpj_participante, dados_participante in dados_cnpj['dados_cte']['participantes'].items():
                destinatarios[cnpj_participante] = dados_participante

            for nota in dados_cnpj['dados_entradas']['notas']:
                natureza_operacao = nota['natureza_operação']

                if natureza_operacao not in naturezas:
                    naturezas.append(natureza_operacao)
            
            with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
                # Bloco 0
                gerar_registro_0000(periodo, razao_social_emitente, cnpj, inscricao_estadual_emitente, uf_emitente, codigo_municipio_emitente, arquivo)
                gerar_registro_0001(arquivo)
                gerar_registro_0005(nome_fantasia_emitente, cep_emitente, logradouro_emitente, numero_logradouro_emitente, bairro_emitente, telefone_emitente, arquivo)
                gerar_registro_0100(arquivo)
                mapa_codigos_participantes = gerar_registro_0150(destinatarios, arquivo)
                gerar_registro_0190(unidades, arquivo)
                mapa_codigos_itens = gerar_registro_0200(itens, arquivo)
                # mapa_codigos_naturezas = gerar_registro_0400(naturezas, arquivo)
                
                
                contar_e_escrever(f'|0990|{contador_blocos['0'] + 1}|', arquivo)
                
                # Bloco B
                contar_e_escrever('|B001|0|', arquivo)
                contar_e_escrever('|B470|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|', arquivo)
                contar_e_escrever(f'|B990|{contador_blocos['B'] + 1}|', arquivo)

                # Bloco C
                contar_e_escrever('|C001|0|', arquivo)
                gerar_registro_c100(notas, mapa_codigos_participantes, arquivo, dicionario_csts_originais, dicionario_csts_corretos, periodo, cnpj, mapa_codigos_itens, mapa_codigos_naturezas='')
                contar_e_escrever(f'|C990|{contador_blocos['C'] + 1}|', arquivo)
                                
                # Bloco D
                if len(notas_cte) > 0:
                    contar_e_escrever("|D001|0|", arquivo)
                else :
                    contar_e_escrever("|D001|1|", arquivo)
                    
                gerar_registro_d100(notas_cte, arquivo, mapa_codigos_participantes)    
                contar_e_escrever(f'|D990|{contador_blocos['D'] + 1}|', arquivo)


                # Bloco E
                contar_e_escrever(f"|E001|0|", arquivo)
                contar_e_escrever(f"|E100|{data_inicial}|{data_final}|", arquivo)
                contar_e_escrever(f"|E110|0,00|0,00|0,00|{formata_valor(creditos_icms)}|{formata_valor(creditos_icms)}|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|0,00|", arquivo)
                
                if creditos_icms > 0 :
                    contar_e_escrever(f"|E111|DF010231|Créditos por Entradas (SIMPLES Nacional)|{formata_valor(creditos_icms)}|", arquivo)
                
                contar_e_escrever(f"|E200|{uf_emitente}|{data_inicial}|{data_final}|", arquivo)
                contar_e_escrever(f"|E210|0|0|0|0|0|0|0|0|0|0|0|0|0|0|", arquivo)
                contar_e_escrever(f"|E300|{uf_emitente}|{data_inicial}|{data_final}|", arquivo)
                contar_e_escrever(f"|E310|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|", arquivo)
                contar_e_escrever(f'|E990|{contador_blocos['E'] + 1}|', arquivo)
                
                contar_e_escrever('|G001|1|', arquivo)
                contar_e_escrever(f'|G990|{contador_blocos['G'] + 1}|', arquivo)
                
                contar_e_escrever('|H001|1|', arquivo)
                contar_e_escrever(f'|H990|{contador_blocos['H'] + 1}|', arquivo)
                
                contar_e_escrever('|K001|1|', arquivo)
                contar_e_escrever(f'|K990|{contador_blocos['K'] + 1}|', arquivo)
                
                contar_e_escrever('|1001|0|', arquivo)
                contar_e_escrever('|1010|N|N|N|N|N|N|N|N|N|N|N|N|N|', arquivo)
                contar_e_escrever(f'|1990|{contador_blocos['1'] + 1}|', arquivo)
                
                # No final do arquivo, escreva o resumo da contagem
                gerar_bloco_9(arquivo)

            # print(periodo, cnpj, contador_csts[periodo][cnpj])
            # Quero veruifcar se os valores de cst_icms estão de acordo com o dicionario_csts_corretos
            cst_500 = contador_csts[periodo][cnpj]['500_5405']
            cst_500_correto = dicionario_csts_corretos['500']
            if cst_500 != cst_500_correto:
                print(f"CST 500 valor {cst_500} não de acordo com o valor correto {cst_500_correto}")
                diferenca = round(cst_500_correto - cst_500, 2)
                print(f"Diferença: {diferenca}")

                alterar_sped(nome_arquivo, diferenca)

            print(f"Arquivo SPED Retificador gerado com sucesso: {nome_arquivo}")