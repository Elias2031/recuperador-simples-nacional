from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from core.views.home import dashboard_view
from core.views.upload import upload_view
from core.views.empresa import (
    empresas_view,
    nova_empresa_view,
    editar_empresa_view,
    excluir_empresa_view,
    selecionar_empresa_view,
    consultar_cnpj_view
)
from core.views.periodo import selecionar_periodo_view
from core.views.notas import notas_fiscais_view
from core.views.apuracoes_view import apuracoes_view
from core.views.apuracao_detalhada_view import apuracao_detalhada_view
from core.views.pgdas_view import pgdas_view, excluir_pgdas_view
from core.views.itens_view import listar_itens_nfe_view
from core.views.analise_tributaria_view import analise_tributaria_view, analisar_ncm_view, analisar_todos_ncms_view, analisar_ncms_nao_analisados
from core.views.analise_ncm_detalhada_view import analise_ncm_detalhada_view
from core.views.apuracoes_view import executar_apuracao_view, executar_apuracao_todas
from core.views.espelho_pgdas import gerar_espelho_pgdas

urlpatterns = [
    path('', dashboard_view, name='dashboard'),

    # Autenticação
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Upload de arquivos
    path('uploads/', upload_view, name='upload_view'),

    # Empresas
    path('empresas/', empresas_view, name='empresas_view'),
    path('empresas/nova/', nova_empresa_view, name='nova_empresa_view'),
    path('empresas/<int:pk>/editar/', editar_empresa_view, name='editar_empresa_view'),
    path('empresas/<int:pk>/excluir/', excluir_empresa_view, name='excluir_empresa_view'),
    path('empresas/<int:pk>/selecionar/', selecionar_empresa_view, name='selecionar_empresa'),

    # Período
    path('selecionar-periodo/', selecionar_periodo_view, name='selecionar_periodo'),

    # Notas fiscais
    path('notas/', notas_fiscais_view, name='notas_fiscais_view'),
    path('pgdas/<int:pgdas_id>/excluir/', excluir_pgdas_view, name='excluir_pgdas'),
    
    # Apuração
    path('apuracoes/', apuracoes_view, name='apuracoes_mensais_view'),  # Lista de apurações
    path('apuracoes/<int:apuracao_id>/', apuracao_detalhada_view, name='apuracao_detalhada'),  # Detalhe
    
    # PGDAS
    path('pgdas/', pgdas_view, name='pgdas_view'),
    path('itens/', listar_itens_nfe_view, name='listar_itens'),
    
    path('analise_tributaria/', analise_tributaria_view, name='analise_tributaria'),
    path('ncm/<int:ncm_id>/detalhes/', analise_ncm_detalhada_view, name='analise_detalhada_ncm'),
    
    path('analise/tributaria/analisar-todos/', analisar_todos_ncms_view, name='analisar_todos_ncms'),
    path('analise/tributaria/analisar-ncms-nao-analisados/', analisar_ncms_nao_analisados, name='analisar_ncms_nao_analisados'),
    path('analise/tributaria/<int:ncm_id>/analisar/', analisar_ncm_view, name='analisar_ncm'),
    
    path('apurar/<int:apuracao_id>/', executar_apuracao_view, name='executar_apuracao'),
    path('apuracoes/apurar-todas/', executar_apuracao_todas, name='executar_apuracao_todas'),

    path('consultar-cnpj/', consultar_cnpj_view, name='consultar_cnpj'),
    
    path('apuracoes/<int:apuracao_id>/espelho-pgdas/', gerar_espelho_pgdas, name='gerar_espelho_pgdas'),

]
