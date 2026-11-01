from django import template

register = template.Library()

@register.filter
def get_participante(participacoes, tipo):
    try:
        return next(p for p in participacoes if p.tipo == tipo)
    except StopIteration:
        return None