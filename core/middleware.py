from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Company

class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # URLs públicas que não precisam de empresa
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
            is_public = any(request.path.startswith(path) for path in public_paths)
            
            if not is_public:
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