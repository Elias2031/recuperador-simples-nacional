import pandas as pd
import os
from django.conf import settings
from core.services.apis.legisweb import (
    consultar_api_aliquota_diferenciada_icms,
    consultar_api_st_interna,
    consultar_api_st_interestadual,
    consultar_api_pis_cofins,
    consultar_api_beneficios_fiscais_isencao,
)
from datetime import datetime
from decimal import Decimal, InvalidOperation

TIPI_PATH = os.path.join(settings.BASE_DIR, '_RECURSOS_', 'tipi.xlsx')

def tratar_decimais(dados):
    campos_decimais = [
        'aliquota_icms_retornado',
        'mva',
        'mva_ajustada_4',
        'mva_ajustada_7',
        'mva_ajustada_12',
        'mva_original_st_interestadual',
        'mva_ajustada_4_st_interestadual',
        'mva_ajustada_12_st_interestadual',
    ]

    for campo in campos_decimais:
        valor = dados.get(campo)
        try:
            if valor not in [None, ""]:
                dados[campo] = Decimal(str(valor).replace(",", "."))
            else:
                dados[campo] = None
        except (InvalidOperation, ValueError):
            dados[campo] = None

    return dados

def tratar_datas(dados):
    print(dados)
    campos_data = [
        'vigencia_inicial',
        'vigencia_inicial_st',
        'vigencia_inicial_st_interestadual',
        'vigencia_inicial_icms',
        
    ]

    for campo in campos_data:
        if campo in dados and isinstance(dados[campo], str):
            try:
                dados[campo] = datetime.strptime(dados[campo], "%d/%m/%Y").date()
            except ValueError:
                dados[campo] = None  # ou continue para ignorar a data inválida
    print(dados)
    return dados

def formatar_ncm(ncm):
    if len(ncm) == 8:
        return f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}"
    return None

def consultar_tipi(dados_ncm, tipi):
    ncm_formatado = formatar_ncm(dados_ncm['ncm'])
    if not ncm_formatado:
        return "NCM inválido"

    linha = tipi[tipi['NCM'] == ncm_formatado]
    if linha.empty:
        return f"NCM {ncm_formatado} não encontrado na TIPI"

    return linha['DESCRIÇÃO'].iloc[0]

def consultar_dados_ncm(dados_ncm):
    tipi_df = pd.read_excel(TIPI_PATH)

    dados_icms = consultar_api_aliquota_diferenciada_icms(dados_ncm)
    dados_st = consultar_api_st_interna(dados_ncm)
    dados_st_inter = consultar_api_st_interestadual(dados_ncm)
    dados_pis_cofins = consultar_api_pis_cofins(dados_ncm)
    desc_tipi = consultar_tipi(dados_ncm, tipi_df)

    return {
        'ncm': dados_ncm['ncm'],
        'nome_item': dados_ncm['nome_item'],
        'desc_tipi': desc_tipi,

        'descricao_st': dados_st.get('descricao_ncm', ''),
        'aliquota_icms_retornado': dados_icms.get('aliquota_icms_retornado', ''),
        'descricao_icms_retornado': dados_icms.get('descricao_icms_retornado', ''),
        'base_legal_icms_retornado': dados_icms.get('base_legal_retornado', ''),
        'vigencia_inicial_icms': dados_icms.get('vigencia_inicial', ''),
        'observacao_icms': dados_icms.get('observacao_icms', ''),
        'cst_icms': '201 ou 202 ou 500' if dados_st.get('cest') != 'NÃO TEM ST' else dados_icms.get('cst_icms', ''),

        'cest': dados_st.get('cest', ''),
        'descricao_ncm_st': dados_st.get('descricao_ncm', ''),
        'base_legal_st': dados_st.get('base_legal_st', ''),
        'vigencia_inicial_st': dados_st.get('vigencia_inicial', ''),
        'observacao_st': dados_st.get('observacao', ''),
        'segmentos_st': dados_st.get('segmento', ''),
        'mva': dados_st.get('mva', ''),
        'mva_ajustada_4': dados_st.get('mva_ajustada_4', ''),
        'mva_ajustada_7': dados_st.get('mva_ajustada_7', ''),
        'mva_ajustada_12': dados_st.get('mva_ajustada_12', ''),

        'cst_simples_pis_cofins': dados_pis_cofins.get('cst_simples', ''),
        'base_legal_pis_cofins': dados_pis_cofins.get('base_legal', ''),

        'cest_st_interestadual': dados_st_inter.get('cest_st_interestadual', ''),
        'descricao_st_interestadual': dados_st_inter.get('descricao_st_interestadual', ''),
        'segmento_st_interestadual': dados_st_inter.get('segmento_st_interestadual', ''),
        'mva_original_st_interestadual': dados_st_inter.get('mva_original_st_interestadual', ''),
        'mva_ajustada_4_st_interestadual': dados_st_inter.get('mva_ajustada_4_st_interestadual', ''),
        'mva_ajustada_12_st_interestadual': dados_st_inter.get('mva_ajustada_12_st_interestadual', ''),
        'vigencia_inicial_st_interestadual': dados_st_inter.get('vigencia_inicial_st_interestadual', ''),
        'base_legal_st_interestadual': dados_st_inter.get('base_legal_st_interestadual', ''),
        'base_legal_interna_st_interestadual': dados_st_inter.get('base_legal_int_st_interestadual', ''),
        'aplicabilidade_st_interestadual': dados_st_inter.get('aplicabilidade_st_interestadual', ''),
        'nao_aplicabilidade_st_interestadual': dados_st_inter.get('nao_aplicabilidade_st_interestadual', ''),
    }

def analisar_ncm_unico(ncm, nome_item, regime_tributario, atividade_origem, atividade_destino):
    dados = {
        'nome_item': nome_item,
        'ncm': ncm,
        'estado': 'DF',
        'id_usuario': settings.LEGISWEB_USER_ID,
        'token': settings.LEGISWEB_TOKEN,
        'modo_busca': 1,
        'regime_tributario_origem': regime_tributario,
        'atividade_origem': atividade_origem,
        'atividade_destino': atividade_destino,
        'aliquota_padrao': 0,
    }
    return tratar_decimais(tratar_datas(consultar_dados_ncm(dados)))
