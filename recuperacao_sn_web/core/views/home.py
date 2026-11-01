from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from core.models import Empresa, NotaFiscal, ApuracaoFiscal
from django.db.models import Sum
from decimal import Decimal

@login_required
def dashboard_view(request):
    empresa_id = request.session.get('empresa_id')
    apuracoes = ApuracaoFiscal.objects.filter(empresa_id=empresa_id)
    total_notas = NotaFiscal.objects.filter(empresa_id=empresa_id).count()
    valor_total_apurado = apuracoes.aggregate(Sum('valor_total_nfe'))['valor_total_nfe__sum'] or Decimal('0.00')
    
    valor_icms_recuperado = apuracoes.filter(icms_recuperado__gt=0).aggregate(
        total=Sum('icms_recuperado')
    )['total'] or Decimal('0.00')

    valor_pis_recuperado = apuracoes.filter(pis_recuperado__gt=0).aggregate(
        total=Sum('pis_recuperado')
    )['total'] or Decimal('0.00')

    valor_cofins_recuperado = apuracoes.filter(cofins_recuperado__gt=0).aggregate(
        total=Sum('cofins_recuperado')
    )['total'] or Decimal('0.00')

    total_recuperado = apuracoes.filter(credito_total_apurado__gt=0).aggregate(
        total=Sum('credito_total_apurado')
    )['total'] or Decimal('0.00')

    total_recuperado = valor_icms_recuperado + valor_pis_recuperado + valor_cofins_recuperado

    def percentual(valor):
        return round((valor / valor_total_apurado) * 100, 2) if valor_total_apurado > 0 else 0

    context = {
        'total_notas': total_notas,
        'valor_total_apurado': valor_total_apurado,
        'valor_icms_total': valor_icms_recuperado,
        'valor_pis_total': valor_pis_recuperado,
        'valor_cofins_total': valor_cofins_recuperado,
        'total_recuperado': total_recuperado,
        'apuracoes': apuracoes.order_by('competencia__ano', 'competencia__mes'),
    }

    return render(request, 'home.html', context)
