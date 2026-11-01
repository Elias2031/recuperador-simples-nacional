from django import template
import locale

register = template.Library()

@register.filter
def formata_brl(valor):
    try:
        valor = float(valor)
        return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return 'R$ 0,00'

@register.filter
def formata_qtd(valor):
    try:
        valor = float(valor)
        return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return '0,00'
    
@register.filter
def formata_cnpj(valor):
    """
    Formata uma string ou número de CNPJ para o formato 00.000.000/0000-00
    """
    try:
        cnpj = ''.join(filter(str.isdigit, str(valor)))
        if len(cnpj) != 14:
            return valor
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'
    except Exception:
        return valor