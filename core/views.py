from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Company, Subscription

def home(request):
    """
    View para a página inicial
    """
    return render(request, 'core/home.html')

def about(request):
    """
    View para a página sobre
    """
    return render(request, 'core/about.html')

def pricing(request):
    """
    View para a página de preços
    """
    return render(request, 'core/pricing.html')

@ensure_csrf_cookie
def register(request):
    """
    View para registro de usuário
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('dashboard')
        else:
            # Re-renderizar com erros de validação
            return render(request, 'core/register.html', {'form': form})
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def profile(request):
    """
    View para o perfil do usuário
    """
    company = get_object_or_404(Company, id=1)  # No MVP teremos apenas uma empresa
    return render(request, 'core/profile.html', {'company': company})

@login_required
def company_settings(request):
    """
    View para configurações da empresa
    """
    company = get_object_or_404(Company, id=1)  # No MVP teremos apenas uma empresa
    return render(request, 'core/company_settings.html', {'company': company})
