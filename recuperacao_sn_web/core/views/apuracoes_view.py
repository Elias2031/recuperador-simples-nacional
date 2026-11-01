from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from core.models import ApuracaoFiscal, NotaFiscal
from django.contrib.auth.decorators import login_required
from core.services.apuracao_simples import apurar_empresa_simples  # ajuste o import se necessário
from django.contrib import messages

@login_required
def executar_apuracao_view(request, apuracao_id):
    apuracao = get_object_or_404(ApuracaoFiscal, id=apuracao_id)
    try:
        apurar_empresa_simples(apuracao.empresa.id, apuracao.competencia.id)
        messages.success(request, "Apuração executada com sucesso.")
    except Exception as e:
        messages.error(request, f"Erro na apuração: {e}")
    return redirect('apuracoes_mensais_view')  # ou ajuste para a URL correta

@login_required
def apuracoes_view(request):
    empresa_id = request.session.get('empresa_id')
    apuracoes = ApuracaoFiscal.objects.filter(empresa_id=empresa_id).select_related('empresa', 'competencia').order_by('competencia__ano', 'competencia__mes')
    
    # Pré-carregar as notas com suas apurações para evitar múltiplas queries
    notas = NotaFiscal.objects.filter(apuracao__in=apuracoes)

    # Agrupar os totais por apuração e tipo
    totais = {}
    for apuracao in apuracoes:
        notas_apuracao = notas.filter(apuracao=apuracao)
        total_entrada = notas_apuracao.filter(tipo='entrada').aggregate(soma=Sum('valor_total'))['soma'] or 0
        total_saida = notas_apuracao.filter(tipo='saida').aggregate(soma=Sum('valor_total'))['soma'] or 0
        total_cte = notas_apuracao.filter(tipo='cte').aggregate(soma=Sum('valor_total'))['soma'] or 0
        total_geral = total_entrada + total_saida + total_cte

        totais[apuracao.id] = {
            'entrada': total_entrada,
            'saida': total_saida,
            'cte': total_cte,
            'geral': total_geral
        }

    return render(request, 'apuracoes_mensais.html', {
        'apuracoes': apuracoes,
        'totais': totais
    })

@login_required
def executar_apuracao_todas(request):
    empresa_id = request.session.get('empresa_id')
    if request.method == 'POST':
        apuracoes = ApuracaoFiscal.objects.filter(empresa_id=empresa_id).select_related('empresa', 'competencia').order_by('competencia__ano', 'competencia__mes')

        total = 0
        for apuracao in apuracoes:
            try:
                apurar_empresa_simples(apuracao.empresa_id, apuracao.competencia_id)  # função que executa a apuração de fato
                total += 1
            except Exception as e:
                messages.error(request, f"Erro ao apurar {apuracao.empresa}: {str(e)}")

        messages.success(request, f'{total} apurações executadas com sucesso.')
    return redirect('apuracoes_mensais_view')  # ou o nome da view que exibe a tabela