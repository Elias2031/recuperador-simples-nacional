from django.contrib import admin
from .models import (
    Empresa, Competencia, ApuracaoFiscal,
    NotaFiscal, ItemNotaFiscal,
    Participante, NotaParticipante,
    UploadLote
)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'cnpj', 'usuario', 'data_cadastro']
    search_fields = ['nome', 'cnpj']

@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ['mes', 'ano']
    list_filter = ['ano']

@admin.register(ApuracaoFiscal)
class ApuracaoFiscalAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'competencia', 'valor_total_nfe', 'num_itens_processados', 'criado_em']
    list_filter = ['empresa', 'competencia']

# @admin.register(NotaFiscal)
# class NotaFiscalAdmin(admin.ModelAdmin):
#     list_display = ['numero', 'empresa', 'data_emissao', 'valor_total', 'tipo']
#     list_filter = ['empresa', 'tipo', 'data_emissao']
#     search_fields = ['numero', 'chave']

# @admin.register(ItemNotaFiscal)
# class ItemNotaFiscalAdmin(admin.ModelAdmin):
#     list_display = ['nota', 'descricao', 'ncm', 'valor_produto', 'unidade']
#     search_fields = ['descricao', 'ncm']

@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj']
    search_fields = ['nome', 'cnpj']

@admin.register(NotaParticipante)
class NotaParticipanteAdmin(admin.ModelAdmin):
    list_display = ['nota', 'participante', 'tipo']
    list_filter = ['tipo']

# @admin.register(UploadLote)
# class UploadLoteAdmin(admin.ModelAdmin):
#     list_display = ['empresa', 'usuario', 'nome_arquivo', 'data_envio', 'status']
#     list_filter = ['empresa', 'usuario', 'status']