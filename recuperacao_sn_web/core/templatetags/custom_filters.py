from django import template

register = template.Library()

@register.filter
def zfill(value, size=2):
    try:
        return str(value).zfill(size)
    except:
        return value

@register.filter
def dict_get(dicionario, chave):
    if isinstance(dicionario, dict):
        return dicionario.get(chave)
    return None


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)