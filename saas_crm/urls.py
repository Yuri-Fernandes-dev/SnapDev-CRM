"""
URL configuration for saas_crm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import ensure_csrf_cookie
from core import views as core_views
from sales.views import public_receipt
from django.contrib.auth.models import User
from django.shortcuts import redirect

# Middleware para suporte à impersonificação de usuários
class ImpersonateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar se há uma sessão de impersonificação
        if request.user.is_authenticated and request.user.is_superuser and 'impersonate_user_id' in request.session:
            user_id = request.session['impersonate_user_id']
            try:
                # Substituir o usuário da request temporariamente
                request.real_user = request.user
                request.user = User.objects.get(pk=user_id)
                # Adicionar indicador de impersonificação
                request.is_impersonating = True
            except User.DoesNotExist:
                # Remover ID inválido da sessão
                del request.session['impersonate_user_id']

        # Continuar com o fluxo normal
        response = self.get_response(request)
        return response

# Adicionar o middleware ao settings.py
if 'saas_crm.urls.ImpersonateMiddleware' not in settings.MIDDLEWARE:
    settings.MIDDLEWARE.append('saas_crm.urls.ImpersonateMiddleware')

# View para parar a impersonificação
def stop_impersonating(request):
    if hasattr(request, 'real_user'):
        request.user = request.real_user
        del request.session['impersonate_user_id']
    return redirect('/')

# Definir URL patterns públicos que não precisam de autenticação
public_receipt_patterns = [
    path('recibo/<str:token>/', public_receipt, name='public_receipt'),
    path('r/<str:token>/', public_receipt, name='public_receipt_short'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stop-impersonating/', stop_impersonating, name='stop-impersonating'),
    path('', core_views.home, name='home'),
    path('sobre/', core_views.about, name='about'),
    path('precos/', core_views.pricing, name='pricing'),
    path('dashboard/', include('dashboard.urls')),
    path('produtos/', include('products.urls')),
    path('vendas/', include('sales.urls')),
    path('clientes/', include('customers.urls')),
    
    # URLs públicas (não exigem login, incluso diretamente na raiz)
    path('', include('sales.public_urls')),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', core_views.register, name='register'),
    
    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Perfil e Configurações
    path('perfil/', core_views.profile, name='profile'),
    path('empresa/', core_views.company_settings, name='company_settings'),
    path('plano/', core_views.subscription, name='subscription'),
    path('suporte/', core_views.support, name='support'),
    
    # Assinaturas
    path('planos/', core_views.subscription_plans, name='subscription_plans'),
    path('planos/<str:plan>/assinar/', core_views.update_subscription, name='update_subscription'),
]

# Adicionar URLs para arquivos de media em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
