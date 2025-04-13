from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Company, Subscription
from django.db.models import Sum, Count, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer

@login_required
def home(request):
    """
    View para a página inicial
    """
    return render(request, 'core/home.html')

@login_required
def about(request):
    """
    View para a página sobre
    """
    return render(request, 'core/about.html')

@login_required
def pricing(request):
    """
    View para a página de preços
    """
    return render(request, 'core/pricing.html')

@login_required
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
    if request.method == 'POST':
        user = request.user
        if 'email' in request.POST:
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
        elif 'password' in request.POST:
            password = request.POST.get('password')
            user.set_password(password)
            user.save()
            messages.success(request, 'Senha atualizada com sucesso!')
        return redirect('profile')
    return render(request, 'core/profile.html')

@login_required
def company_settings(request):
    """
    View para configurações da empresa
    """
    if request.method == 'POST':
        company = request.user.company
        company.name = request.POST.get('name')
        company.cnpj = request.POST.get('cnpj')
        company.email = request.POST.get('email')
        company.phone = request.POST.get('phone')
        company.address = request.POST.get('address')
        company.notifications = request.POST.get('notifications', False) == 'on'
        company.save()
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('company_settings')
    return render(request, 'core/company_settings.html')

@login_required
def dashboard(request):
    return render(request, 'dashboard/dashboard.html')
