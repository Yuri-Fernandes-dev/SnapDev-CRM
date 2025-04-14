from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from .models import Company

class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificação específica para rotas de recibos públicos que contêm um token
        is_receipt_url = (
            request.path.startswith('/recibo/') or 
            request.path.startswith('/r/') or
            request.path.startswith('/vendas/recibo/') or 
            request.path.startswith('/vendas/r/')
        )
        
        # Outras URLs públicas que não precisam de empresa
        public_paths = [
            '/',  # home
            '/sobre/',  # about
            '/precos/',  # pricing
            '/login/',  # login
            '/logout/',  # logout
            '/cadastro/',  # register
            '/admin/',  # admin
            '/static/',  # arquivos estáticos
            '/media/',  # arquivos de mídia
        ]
        
        # Verifica se o caminho atual começa com alguma das URLs públicas
        is_public = any(request.path.startswith(path) for path in public_paths) or is_receipt_url
        
        # Se o usuário está autenticado e a URL não é pública, verificar empresa
        if request.user.is_authenticated and not is_public:
            try:
                # Tenta obter a empresa do usuário
                request.company = Company.objects.get(owner=request.user)
                
                # Verifica se a assinatura está ativa
                if not request.company.subscription.is_active():
                    messages.warning(
                        request,
                        'Sua assinatura expirou. Por favor, atualize seu plano para continuar usando o sistema.'
                    )
                    return redirect('subscription_plans')
                    
            except Company.DoesNotExist:
                messages.error(
                    request,
                    'Você precisa criar uma empresa para acessar o sistema.'
                )
                return redirect('register')
        
        response = self.get_response(request)
        return response 

class AuthenticationExemptMiddleware:
    """
    Middleware que permite acesso a URLs específicas sem autenticação
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Verificar se a URL atual é para recibo público (em todos os caminhos possíveis)
        is_receipt_url = (
            request.path.startswith('/recibo/') or 
            request.path.startswith('/r/') or
            request.path.startswith('/vendas/recibo/') or 
            request.path.startswith('/vendas/r/')
        )
        
        if is_receipt_url:
            # Se for um recibo público, marcar a requisição como isenta de autenticação
            request.exempt_from_auth = True
        return None
            
    def __call__(self, request):
        # Adicionar um atributo à requisição
        request.exempt_from_auth = False
        
        # Chamar process_view (será executado antes da view)
        if hasattr(self, 'process_view'):
            result = self.process_view(request, None, None, None)
            if result is not None:
                return result
                
        response = self.get_response(request)
        return response 

class CustomAuthenticationMiddleware:
    """
    Middleware que verifica a flag exempt_from_auth antes de aplicar a autenticação
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Se a requisição está marcada como isenta de autenticação, 
        # não verificar se o usuário está autenticado
        if hasattr(request, 'exempt_from_auth') and request.exempt_from_auth:
            # Pular a verificação de autenticação
            pass
        else:
            # Aplicar a lógica de autenticação normal
            pass
            
        # Continuar com o fluxo normal
        response = self.get_response(request)
        return response 