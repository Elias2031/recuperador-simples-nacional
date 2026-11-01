import xml.etree.ElementTree as ET
import os
import openpyxl
import pandas as pd 
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

cor = 'F0F8FF'  
border1 = Side(style='thin', color='FF000000')
thin = Border(left=border1, right=border1, top=border1, bottom=border1)
fill = PatternFill(start_color=cor, end_color=cor, fill_type='solid')

def finalizar_planilha(dicionario_segregacao, dicionario_csts_originais, razao_social, perido):
    contador_segregacao = 2
    
    # Preencher dados do dicionário de segregação
    for codigo, valor in dicionario_segregacao.items():
        planilha_de_itens_ativa[f'P{contador_segregacao}'] = codigo
        planilha_de_itens_ativa[f'Q{contador_segregacao}'] = valor
        contador_segregacao += 1
    contador_segregacao += 1
    
    # Adicionar cabeçalho de CSTS ORIGINAIS
    planilha_de_itens_ativa[f'P{contador_segregacao}'] = 'CSTS ORIGINAIS'
    planilha_de_itens_ativa[f'P{contador_segregacao}'].fill = fill
    planilha_de_itens_ativa[f'Q{contador_segregacao}'].fill = fill
    planilha_de_itens_ativa[f'P{contador_segregacao}'].font  = Font(bold=True, size=12)
    contador_segregacao += 1
    
    # Preencher dados do dicionário de CSTS originais
    for codigo, valor in dicionario_csts_originais.items():
        planilha_de_itens_ativa[f'P{contador_segregacao}'] = codigo
        planilha_de_itens_ativa[f'Q{contador_segregacao}'] = valor
        contador_segregacao += 1
    
    # Centralizar todo o conteúdo da planilha
    for row in planilha_de_itens_ativa.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Criar diretório "planilhas" caso não exista
    if not os.path.exists('PLANILHAS'):
        os.makedirs('PLANILHAS')
    
    # Salvar a planilha com o nome especificado
    planilha_de_itens.save(f'PLANILHAS/SEGREGACAO_DE_RECEITAS_{razao_social}_{perido}.xlsx')

def gerar_planilha_fisica():
    global planilha_de_itens, planilha_de_itens_ativa
    planilha_de_itens = Workbook()
    planilha_de_itens_ativa = planilha_de_itens.create_sheet('Planilha de itens')
    planilha_de_itens.remove(planilha_de_itens['Sheet'])  # Remove a sheet padrão criada
    
    headers = ["NOME DO ITEM NOTA", "CHAVE NOTA", "CST ICMS NOTA", "CST PIS NOTA", "CST ICMS CORRETO", 
               "CST PIS CORRETO", "NCM ITEM NOTA", "CFOP NOTA", "CFOP CORRETO", "VALOR ITEM", "DATA DE NOTA",
               "SITUAÇÃO PIS", "SITUAÇÃO ICMS", "SITUAÇÃO CFOP", "", "SEGREGAÇÃO DE RECEITAS", ""]
    widths = [51, 45, 15.60, 13.57, 19, 17, 17, 12.30, 12.30, 14.60, 16, 17, 15.71, 16, 10, 26.71, 10, 10, 10, 10, 10]
    
    for col, (header, width) in enumerate(zip(headers, widths), start=1):
        cell = planilha_de_itens_ativa.cell(row=1, column=col, value=header)
        cell.fill = fill
        cell.border = thin
        cell.font = Font(size=12, bold=True)
        planilha_de_itens_ativa.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width

def adicionar_item_na_planilha(item):
    contador = item['contador']
    
    planilha_de_itens_ativa[f'A{contador}'] = item['nome_item_nota']
    planilha_de_itens_ativa[f'B{contador}'] = item['chave_nota']
    planilha_de_itens_ativa[f'C{contador}'] = item['cst_icms']
    planilha_de_itens_ativa[f'D{contador}'] = item['cst_pis_cofins']
    planilha_de_itens_ativa[f'E{contador}'] = item['cst_icms_correto']
    planilha_de_itens_ativa[f'F{contador}'] = item['cst_pis_cofins_correto']
    planilha_de_itens_ativa[f'G{contador}'] = item['ncm']
    planilha_de_itens_ativa[f'H{contador}'] = item['cfop']
    planilha_de_itens_ativa[f'I{contador}'] = item['cfop_excel']
    planilha_de_itens_ativa[f'J{contador}'] = item['valor']
    planilha_de_itens_ativa[f'K{contador}'] = item['data']
    
    for row in planilha_de_itens_ativa.iter_rows(min_row=contador, max_row=contador):
        for celulas in row:
            celulas.border = thin
            celulas.font = Font(size=11)
            
def formatar_planilha(arquivo):
    # Carregar a planilha
    wb = Workbook()
    ws = wb.active
    ws.title = "Itens Analisados"
    
    # Ler os dados do DataFrame
    df = pd.read_excel(arquivo)
    
    # Definir borda fina para as células
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Adicionar o cabeçalho
    for col_num, column_title in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_num, value=column_title)
        cell.font = Font(bold=True, color="FFFFFF")  # Texto em negrito e branco
        cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")  # Fundo azul
        cell.alignment = Alignment(horizontal='center')  # Centraliza o texto
        cell.border = thin_border  # Aplica borda às células do cabeçalho

    # Adicionar os dados
    for row_num, row in enumerate(dataframe_to_rows(df, index=False, header=False), start=2):
        for col_num, value in enumerate(row, start=1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.alignment = Alignment(horizontal='center', vertical='center')  # Centraliza os dados horizontal e verticalmente
            cell.border = thin_border  # Aplica borda às células de dados
            
            # Formatar como moeda (se o valor for numérico)
            if isinstance(value, (int, float)):
                cell.number_format = 'R$ #,##0.00'  # Formato para dinheiro brasileiro

    # Formatar largura das colunas
    for col in range(1, len(df.columns) + 1):
        column_letter = get_column_letter(col)
        ws.column_dimensions[column_letter].width = 20  # Define largura da coluna

    # Salvar a planilha formatada
    wb.save(arquivo)