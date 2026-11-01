from .models import Competencia, ApuracaoFiscal

def competencias_disponiveis(request):
    competencias = []

    empresa_id = request.session.get('empresa_id')
    if empresa_id:
        competencias = Competencia.objects.filter(
            apuracaofiscal__empresa_id=empresa_id
        ).distinct().order_by('-ano', '-mes')

    return {'competencias_disponiveis': competencias}

from .models import Empresa

def empresas_disponiveis(request):
    if request.user.is_authenticated:
        return {
            'empresas_disponiveis': Empresa.objects.filter(usuario=request.user)
        }
    return {}