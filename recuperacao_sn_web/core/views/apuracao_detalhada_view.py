from django.shortcuts import render, get_object_or_404
from core.models import ApuracaoFiscal, NotaFiscal
from core.templatetags.format_extras import formata_brl  # Certifique-se que esse import esteja correto

def apuracao_detalhada_view(request, apuracao_id):
    apuracao = get_object_or_404(
        ApuracaoFiscal.objects.select_related('empresa', 'competencia'),
        id=apuracao_id
    )
    notas = NotaFiscal.objects.filter(apuracao=apuracao).select_related('empresa')

    return render(request, 'apuracao_detalhada.html', {
        'apuracao': apuracao,
        'notas': notas,
    })
