from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.models import Empresa
from core.forms import EmpresaForm
from django.http import JsonResponse
from django.contrib import messages
from core.services.apis.consultar_cnpj import consultar_dados_cnpj

@login_required
def empresas_view(request):
    empresas = Empresa.objects.filter(usuario=request.user)
    return render(request, 'empresas.html', {'empresas': empresas})

@login_required
def nova_empresa_view(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.usuario = request.user
            try:
                empresa.save()
                messages.success(request, "✅ Empresa cadastrada com sucesso.")
                return redirect('empresas_view')
            except Exception as e:
                messages.error(request, f"❌ Erro ao salvar empresa: {str(e)}")
        else:
            messages.warning(request, "⚠️ Empresa já cadastrada")
    else:
        form = EmpresaForm()
    return render(request, 'empresa_form.html', {'form': form, 'titulo': 'Nova Empresa'})

def consultar_cnpj_view(request):
    cnpj = request.GET.get('cnpj', '').replace('.', '').replace('/', '').replace('-', '')
    
    if not cnpj or len(cnpj) != 14:
        return JsonResponse({'error': 'CNPJ inválido'}, status=400)

    dados = consultar_dados_cnpj(cnpj)

    if not dados:
        return JsonResponse({'error': 'Erro ao consultar CNPJ'}, status=500)

    return JsonResponse({
        'razao_social': dados.get('razao_social', ''),
        'nome_fantasia': dados.get('nome_fantasia', ''),
        'inscricao_estadual': dados.get('inscricao_estadual', ''),
        'cep': dados.get('cep', ''),
        'endereco': dados.get('endereco', ''),
        'numero': dados.get('numero', ''),
        'bairro': dados.get('bairro', ''),
        'municipio': dados.get('municipio', ''),
        'uf': dados.get('uf', ''),
        'data_abertura': dados.get('data_abertura', ''),
        'cnae_principal' : dados.get('cnae_principal', {}),
        'cnaes_secundarios' : dados.get('cnaes_secundarios', {})
    })

@login_required
def editar_empresa_view(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Empresa atualizada com sucesso.")
            return redirect('empresas_view')
        else:
            messages.warning(request, "⚠️ Empresa já cadastrada")
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'empresa_form.html', {'form': form, 'titulo': 'Editar Empresa'})

@login_required
def excluir_empresa_view(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    if request.method == 'POST':
        empresa.delete()
        messages.success(request, "🗑️ Empresa excluída com sucesso.")
        return redirect('empresas_view')
    return render(request, 'empresa_confirm_delete.html', {'empresa': empresa})

@login_required
def selecionar_empresa_view(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    request.session['empresa_id'] = empresa.id
    request.session['empresa_nome'] = empresa.razao_social
    messages.success(request, f"🏢 Empresa selecionada: {empresa.razao_social}")
    return redirect('empresas_view')
