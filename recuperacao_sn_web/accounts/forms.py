from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='E-mail', widget=forms.EmailInput())

class CadastroForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput())
    confirmar_senha = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Usuario
        fields = ['nome', 'email']

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get("senha")
        confirmar = cleaned_data.get("confirmar_senha")
        if senha != confirmar:
            self.add_error("confirmar_senha", "As senhas não coincidem")
