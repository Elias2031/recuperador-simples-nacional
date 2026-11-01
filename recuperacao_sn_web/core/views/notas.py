from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.models import NotaFiscal, ItemNotaFiscal
from django.db.models import Q
from core.models import PgdasValorDeclarado
from django.contrib import messages

@login_required
def notas_fiscais_view(request):
    empresa_id = request.session.get('empresa_id')
    notas = NotaFiscal.objects.filter(empresa_id=empresa_id)

    # Filtros
    busca = request.GET.get('q')
    tipo = request.GET.get('tipo')
    competencia = request.GET.get('competencia')

    if busca:
        notas = notas.filter(chave__icontains=busca)

    if tipo:
        notas = notas.filter(tipo=tipo)

    if competencia:
        mes, ano = competencia.split('_')
        notas = notas.filter(apuracao__competencia__mes=mes, apuracao__competencia__ano=ano)

    return render(request, 'notas_fiscais.html', {'notas': notas})

@login_required
def itens_importados_view(request):
    empresa_id = request.session.get('empresa_id')
    competencia_id = request.session.get('competencia_id')

    if not empresa_id or not competencia_id:
        return render(request, 'itens_importados.html', {'erro': 'Selecione uma empresa e um período.'})

    itens = ItemNotaFiscal.objects.filter(
        nota__empresa_id=empresa_id,
        nota__apuracao__competencia_id=competencia_id
    ).select_related('nota')

    return render(request, 'itens_importados.html', {'itens': itens})


