# core/views/espelho_pgdas.py

from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from io import BytesIO
from core.models import ApuracaoFiscal
from django.shortcuts import get_object_or_404

def gerar_espelho_pgdas(request, apuracao_id):
    apuracao = get_object_or_404(ApuracaoFiscal, id=apuracao_id)
    competencia = apuracao.competencia
    
    
    # BLOCO SEM ST 
    

    context = {
        'empresa': apuracao.empresa,
        'competencia': apuracao.competencia,
        'competencia_formatada': f"{competencia.mes:02d}/{competencia.ano}",
        'periodo_inicio': f"01/{competencia.mes:02d}/{competencia.ano}",
        'periodo_fim': f"{competencia.mes:02d}/{competencia.ano}",
        'apuracao': apuracao,
        
    }

    print(apuracao.aliquota_icms)
    
    html = render_to_string('espelho_pgdas.html', context)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        return HttpResponse("Erro ao gerar PDF", status=500)

    return HttpResponse(result.getvalue(), content_type='application/pdf')
