from django.shortcuts import render, get_object_or_404
from core.models import NcmUnico, Empresa

def analise_ncm_detalhada_view(request, ncm_id):
    empresa_ativa = request.session.get('empresa_id')

    ncm = get_object_or_404(
        NcmUnico,
        id=ncm_id,
        empresa_id=empresa_ativa
    )
    # print(ncm)

    return render(request, 'analise_detalhada_ncm.html', {'ncm': ncm})
