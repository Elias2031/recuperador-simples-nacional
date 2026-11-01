from django import forms
from .models import Empresa
import re

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'cnpj',
            'razao_social',
            'nome_fantasia',
            'inscricao_estadual',
            'cep',
            'endereco',
            'numero',
            'bairro',
            'municipio',
            'uf',
            'regime_tributario',
            'data_abertura',
            'cnae_principal',
            'cnaes_secundarios'
        ]
        widgets = {
            'regime_tributario': forms.TextInput(attrs={'placeholder': 'Ex: Simples Nacional'}),
            'cep': forms.TextInput(attrs={'placeholder': '00000-000'}),
            'cnpj': forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
            'cnae_principal': forms.TextInput(attrs={'readonly': 'readonly'}),
            'cnaes_secundarios': forms.Textarea(attrs={'rows': 3, 'readonly': 'readonly'}),
        }


    def clean_cnpj(self):
        """Remove pontos, barras e traços do CNPJ."""
        cnpj = self.cleaned_data['cnpj']
        return re.sub(r'\D', '', cnpj)