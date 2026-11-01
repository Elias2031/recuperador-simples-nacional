from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Competencia


@login_required
def selecionar_periodo_view(request):
    if request.method == 'POST':
        competencia_id = request.POST.get('competencia_id')
        try:
            competencia = Competencia.objects.get(id=competencia_id)
            request.session['competencia_id'] = competencia.id
            request.session['competencia_nome'] = f"{competencia.mes:02d}/{competencia.ano}"
        except Competencia.DoesNotExist:
            pass
    return redirect(request.META.get('HTTP_REFERER', '/'))
