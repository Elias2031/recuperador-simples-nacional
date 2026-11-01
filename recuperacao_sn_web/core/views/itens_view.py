from core.models import ItemNotaFiscal
from django.shortcuts import render, redirect, get_object_or_404
# views.py
def listar_itens_nfe_view(request):
    empresa_id = request.session.get('empresa_id')
    itens = ItemNotaFiscal.objects.filter(nota__empresa_id=empresa_id)

    # Filtros
    cnpj = request.GET.get('cnpj')
    competencia = request.GET.get('competencia')
    descricao = request.GET.get('descricao')
    ncm = request.GET.get('ncm')

    if cnpj:
        itens = itens.filter(nota__empresa__cnpj__icontains=cnpj)
    if competencia:
        try:
            mes, ano = competencia.split('_')
            itens = itens.filter(nota__apuracao__competencia__mes=mes, nota__apuracao__competencia__ano=ano)
        except:
            pass
    if descricao:
        itens = itens.filter(descricao__icontains=descricao)
    if ncm:
        itens = itens.filter(ncm__icontains=ncm)

    return render(request, 'itens_nfe.html', {'itens': itens})