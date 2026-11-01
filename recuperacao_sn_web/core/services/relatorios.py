import os 

def gerar_relatorio_fiscal(dados):

    caminho_relatorios = os.path.join(os.getcwd(), 'RELATORIOS')

    if not os.path.exists(caminho_relatorios):
        os.makedirs(caminho_relatorios)
        print(f"A pasta 'relatorios' foi criada em {caminho_relatorios}")
    
    dados_pgdas = dados["dados_pgdas"]
    cnpj = dados["cnpj"]
    periodo = dados["periodo"]
    valor_rbt12 = dados["valor_rbt12"]
    valor_imposto_pagar_cheio = dados["valor_imposto_pagar_cheio"]
    valor_imposto_irrecuperavel_irpj_csll_cpp = dados["valor_imposto_irrecuperavel_irpj_csll_cpp"]
    valor_total_receita_nf = dados["valor_total_receita_nf"]
    diferenca_notas_pgdas = dados["diferenca_notas_pgdas"]
    aliquota_efetiva = dados["aliquota_efetiva"]
    aliquotas = dados["aliquotas"]
    aliquota_isenta_de_icms = dados["aliquota_isenta_de_icms"]
    dados_por_periodo = dados["dados_por_periodo"]
    valor_ICMS_novo = dados["valor_ICMS_novo"]
    valor_COFINS_novo = dados["valor_COFINS_novo"]
    valor_PIS_novo = dados["valor_PIS_novo"]
    das_total = dados["das_total"]
    icms_imune_ou_isento = dados["icms_imune_ou_isento"]
    icms_tributado = dados["icms_tributado"]
    icms_ST_e_pis_cofins_monofasico = dados["icms_ST_e_pis_cofins_monofasico"]
    icms_ST = dados["icms_ST"]
    # razao_social = dados["razao_social"]
    
    with open(f'RELATORIOS/relatorio_{periodo}_{cnpj}.txt', 'w') as file:
        # Cabeçalho do relatório
        file.write(f"{'='*50}\n")
        file.write(f"RELATÓRIO FISCAL - PERÍODO: {periodo.upper()} - {cnpj}\n")
        file.write(f"{'='*50}\n")
        
        # Seção de Receita e Impostos
        file.write(f"{'1. Informações de Receita e Impostos':^50}\n")
        file.write(f"{'-'*50}\n")
        file.write(f"RBT12: {valor_rbt12:.2f}\n")
        file.write(f"Receita Bruta Mensal:{dados_pgdas[cnpj]['receita_bruta']:.2f}\n")
        file.write(f"Valor do Imposto a Pagar (Cheio): {valor_imposto_pagar_cheio:.2f}\n")
        file.write(f"Valor do Imposto Irrecuperável (IRPJ, CSLL, CPP): {valor_imposto_irrecuperavel_irpj_csll_cpp:.2f}\n")
        file.write(f"Valor total da receita nas notas fiscais: {valor_total_receita_nf:.2f}\n")
        file.write(f"Diferença entre as notas fiscais e PGDAS: {diferenca_notas_pgdas:.2f}\n")
        file.write(f"{'-'*50}\n")
        
        # Seção de Alíquotas
        file.write(f"{'2. Alíquotas Aplicadas':^50}\n")
        file.write(f"{'-'*50}\n")
        file.write(f"Alíquota Efetiva: {round(aliquota_efetiva * 100, 8)}%\n")
        file.write(f"Alíquota ICMS: {round(aliquotas['aliquota_icms'] * 100, 8)}%\n")
        file.write(f"Alíquota PIS: {round(aliquotas['aliquota_pis'] * 100, 8)}%\n")
        file.write(f"Alíquota COFINS: {round(aliquotas['aliquota_cofins'] * 100, 8)}%\n")
        file.write(f"Alíquota Isenta de ICMS: {round(aliquota_isenta_de_icms * 100, 8)}%\n")
        file.write(f"{'-'*50}\n")
        
        # Seção de Valores por CST
        file.write(f"{'3. Valores por Código de Situação Tributária (CST)':^50}\n")
        file.write(f"{'-'*50}\n")
        file.write(f"Valor de '04 - Operação tributável Monofásica - Revenda a alíquota Zero': {dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0):.2f}\n")
        file.write(f"Valor de '102': {dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('102', 0):.2f}\n")
        file.write(f"Valor de '500': {dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('500', 0):.2f}\n")
        file.write(f"Valor de '900': {dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('900', 0):.2f}\n")
        file.write(f"Valor de '300 ou 400': {dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('300 ou 400', 0):.2f}\n")
        file.write(f"Valor de '05 - Operação tributável por Substituição Tributária': {dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('05 - Operação tributável por Substituição Tributária', 0):.2f}\n")
        file.write(f"{'-'*50}\n")
        
        # Seção de ICMS
        file.write(f"{'4. Informações de ICMS':^50}\n")
        file.write(f"{'-'*50}\n")
        file.write(f"ICMS Imune ou Isento (Base {round(dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('300 ou 400', 0),2)}): {icms_imune_ou_isento:.2f}\n")
        file.write(f"ICMS Tributado (Base {round(dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('102', 0),2)}): {icms_tributado:.2f}\n")
        file.write(f"ICMS ST e PIS/COFINS Monofásico (Base {round(dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0),2)}): {icms_ST_e_pis_cofins_monofasico:.2f}\n")
        file.write(f"ICMS ST (Base {round((dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('500', 0) - dados_por_periodo[periodo][cnpj]['dicionario_csts_corretos'].get('04 - Operação tributável Monofásica - Revenda a alíquota Zero', 0)),2)}): {icms_ST:.2f}\n")
        file.write(f"Total DAS: {das_total:.2f}\n")
        file.write(f"{'-'*50}\n")
        
        # Seção de Impostos Pagos Originalmente
        file.write(f"{'5. Impostos Pagos Originalmente':^50}\n")
        file.write(f"{'-'*50}\n")
        file.write(f"Valor de IRPJ Pago Original: {dados_pgdas[cnpj]['valor_IRPJ_pago_original']}\n")
        file.write(f"Valor de CSLL Pago Original: {dados_pgdas[cnpj]['valor_CSLL_pago_original']}\n")
        file.write(f"Valor de COFINS Pago Original: {dados_pgdas[cnpj]['valor_COFINS_pago_original']}\n")
        file.write(f"Valor de PIS Pago Original: {dados_pgdas[cnpj]['valor_PIS_pago_original']}\n")
        file.write(f"Valor de INSS Pago Original: {dados_pgdas[cnpj]['valor_INSS_pago_original']}\n")
        file.write(f"Valor de ICMS Pago Original: {dados_pgdas[cnpj]['valor_ICMS_pago_original']}\n")
        file.write(f"Valor de IPI Pago Original: {dados_pgdas[cnpj]['valor_IPI_pago_original']}\n")
        file.write(f"Valor de ISS Pago Original: {dados_pgdas[cnpj]['valor_ISS_pago_original']}\n")
        file.write(f"Valor de DAS Pago Original: {dados_pgdas[cnpj]['valor_DAS_pago_original']}\n")
        file.write(f"TESTE ICMS: {round(valor_ICMS_novo, 2)}\n")
        file.write(f"TESTE COFINS: {round(valor_COFINS_novo, 2)}\n")
        file.write(f"TESTE PIS : {round(valor_PIS_novo, 2)}\n")
        file.write(f"{'-'*50}\n")
        
        # Rodapé do relatório
        file.write(f"{'FIM DO RELATÓRIO - PGDAS':^50}\n")
