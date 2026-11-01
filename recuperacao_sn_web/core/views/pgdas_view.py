from django.shortcuts import render, redirect
from core.models import PgdasValorDeclarado
from django.shortcuts import get_object_or_404
from django.contrib import messages


def pgdas_view(request):
    empresa_id = request.session.get('empresa_id')
    cnpj = request.GET.get('cnpj')
    competencia = request.GET.get('competencia')

    # Busca inicial por empresa
    pgdas = PgdasValorDeclarado.objects.select_related('empresa', 'competencia')\
        .filter(empresa_id=empresa_id)

    if cnpj:
        pgdas = pgdas.filter(empresa__cnpj__icontains=cnpj)

    if competencia:
        try:
            mes, ano = map(int, competencia.split('_'))
            pgdas = pgdas.filter(competencia__mes=mes, competencia__ano=ano)
        except:
            pass

    return render(request, 'pgdas_listagem.html', {'pgdas': pgdas})


def excluir_pgdas_view(request, pgdas_id):
    if request.method == 'POST':
        pgdas = get_object_or_404(PgdasValorDeclarado, id=pgdas_id)
        pgdas.delete()
        messages.success(request, 'Declaração PGDAS excluída com sucesso.')
    return redirect('pgdas_view')  # ajuste para o nome da URL da lista