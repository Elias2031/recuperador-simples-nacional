from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .views import custom_password_reset_view


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),

    path('senha/reset/', custom_password_reset_view, name='password_reset'),
    path('senha/reset/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),

    path('senha/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/conta/senha/reset/feito/',
    ), name='password_reset_confirm'),

    path('senha/reset/feito/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]