from django.shortcuts import render, redirect, get_object_or_404
from core.models import NcmUnico, ItemNotaFiscal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.services.analise_ncm_service import analisar_ncm_unico

def analisar_e_vincular_ncm(ncm, empresa_id):
    """Executa a análise do NCM e vincula os itens da empresa."""
    dados = analisar_ncm_unico(
        ncm=ncm.ncm,
        nome_item=ncm.nome_item,
        regime_tributario=3,
        atividade_origem=4,
        atividade_destino=4
    )

    for campo, valor in dados.items():
        campo_model = campo.replace(" ", "_")
        if hasattr(ncm, campo_model):
            setattr(ncm, campo_model, valor)

    ncm.ncm_foi_analisado = True
    ncm.save()

    ItemNotaFiscal.objects.filter(
        ncm=ncm.ncm,
        nota__empresa_id=empresa_id
    ).update(ncm_analisado=ncm)


@login_required
def analise_tributaria_view(request):
    empresa_id = request.session.get('empresa_id')
    ncms = NcmUnico.objects.filter(empresa_id=empresa_id)
    return render(request, 'analise_tributaria.html', {'ncms': ncms})


@login_required
def analisar_ncm_view(request, ncm_id):
    empresa_id = request.session.get('empresa_id')
    ncm = get_object_or_404(NcmUnico, id=ncm_id, empresa_id=empresa_id)

    try:
        analisar_e_vincular_ncm(ncm, empresa_id)
        messages.success(request, f"✅ NCM {ncm.ncm} analisado e vinculado com sucesso.")
    except Exception as e:
        messages.error(request, f"❌ Erro ao analisar NCM {ncm.ncm}: {str(e)}")

    return redirect('analise_detalhada_ncm', ncm.id)


@login_required
def analisar_todos_ncms_view(request):
    empresa_id = request.session.get('empresa_id')
    ncms = NcmUnico.objects.filter(empresa_id=empresa_id)

    if not ncms.exists():
        messages.warning(request, "⚠️ Nenhum NCM encontrado para análise.")
        return redirect('analise_tributaria')

    total = 0
    for ncm in ncms:
        try:
            analisar_e_vincular_ncm(ncm, empresa_id)
            total += 1
        except Exception as e:
            messages.warning(request, f"⚠️ Erro ao analisar NCM {ncm.ncm}: {str(e)}")

    messages.success(request, f"✅ {total} NCMs analisados e vinculados com sucesso.")
    return redirect('analise_tributaria')


@login_required
def analisar_ncms_nao_analisados(request):
    empresa_id = request.session.get('empresa_id')

    # Vincula todos os itens com os NCMs da empresa (mesmo os já analisados)
    ncms_para_vincular = NcmUnico.objects.filter(empresa_id=empresa_id)
    for ncm in ncms_para_vincular:
        ItemNotaFiscal.objects.filter(
            ncm=ncm.ncm,
            nota__empresa_id=empresa_id
        ).update(ncm_analisado=ncm)

    # Filtra apenas os não analisados
    ncms = NcmUnico.objects.filter(empresa_id=empresa_id, ncm_foi_analisado=False)

    if not ncms.exists():
        messages.info(request, "ℹ️ Todos os NCMs já foram analisados.")
        return redirect('analise_tributaria')

    total = 0
    for ncm in ncms:
        try:
            analisar_e_vincular_ncm(ncm, empresa_id)
            total += 1
        except Exception as e:
            messages.warning(request, f"⚠️ Erro ao analisar NCM {ncm.ncm}: {str(e)}")

    messages.success(request, f"✅ {total} NCMs não analisados foram processados com sucesso.")
    return redirect('analise_tributaria')
