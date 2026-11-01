from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .forms import LoginForm, CadastroForm
from .models import Usuario
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import redirect
from django import forms

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')  # O campo do formulário ainda é 'username'
        senha = request.POST.get('password')

        user = authenticate(request, email=email, password=senha)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # ou a página inicial do seu sistema
        else:
            messages.error(request, 'E-mail ou senha incorretos.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def cadastro_view(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_password(form.cleaned_data['senha'])
            usuario.save()
            login(request, usuario)
            return redirect('dashboard')
    else:
        form = CadastroForm()
    return render(request, 'accounts/cadastro.html', {'form': form})

class EmailResetForm(forms.Form):
    email = forms.EmailField(label="E-mail", max_length=254)

def custom_password_reset_view(request):
    if request.method == 'POST':
        form = EmailResetForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email, is_active=True)
            for user in users:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                domain = settings.DEFAULT_DOMAIN
                link = f"http://{domain}/conta/senha/reset/{uid}/{token}/"

                subject = "Redefinição de senha - Morpho"
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'link': link
                })

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            return redirect('password_reset_done')
    else:
        form = EmailResetForm()
    return render(request, 'accounts/password_reset_form.html', {'form': form})