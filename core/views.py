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
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        
        # Atualiza a senha se fornecida
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 and password2 and password1 == password2:
            user.set_password(password1)
            messages.success(request, 'Senha atualizada com sucesso!')
        
        user.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('profile')
    
    return render(request, 'core/profile.html')

@login_required
def company_settings(request):
    """
    View para configurações da empresa
    """
    company = get_object_or_404(Company, id=1)  # No MVP teremos apenas uma empresa
    
    if request.method == 'POST':
        # Atualiza os dados da empresa
        company.name = request.POST.get('name', company.name)
        company.cnpj = request.POST.get('cnpj', company.cnpj)
        company.email = request.POST.get('email', company.email)
        company.phone = request.POST.get('phone', company.phone)
        company.postal_code = request.POST.get('postal_code', company.postal_code)
        company.address = request.POST.get('address', company.address)
        company.city = request.POST.get('city', company.city)
        company.state = request.POST.get('state', company.state)
        company.low_stock_alert = int(request.POST.get('low_stock_alert', company.low_stock_alert))
        company.enable_notifications = request.POST.get('enable_notifications') == 'on'
        
        company.save()
        messages.success(request, 'Configurações atualizadas com sucesso!')
        return redirect('company_settings')
    
    return render(request, 'core/company_settings.html', {'company': company})

@login_required
def dashboard(request):
    # Período selecionado (padrão: 30 dias)
    period = request.GET.get('period', '30')
    days = int(period)
    
    # Data inicial do período
    if days == 1:
        # Para "Hoje", pegamos o início do dia atual
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # Para outros períodos, subtraímos os dias normalmente
        start_date = timezone.now() - timedelta(days=days)
    
    # Vendas no período
    sales = Sale.objects.filter(
        created_at__gte=start_date,
        status='paid'
    )
    
    # Cálculo das métricas básicas
    total_sales = sales.count()
    
    # Usando DecimalField explicitamente para total_revenue
    total_revenue = sales.aggregate(
        total=Sum('total', output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or 0
    
    # Ticket médio
    average_ticket = float(total_revenue) / total_sales if total_sales > 0 else 0
    
    # Produtos com estoque baixo
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')[:5]
    
    # Produtos mais vendidos (simplificado para evitar problemas de tipo)
    top_products = SaleItem.objects.filter(
        sale__in=sales
    ).values(
        'product__name'
    ).annotate(
        total_qty=Count('id')
    ).order_by('-total_qty')[:5]
    
    # Clientes
    total_customers = Customer.objects.filter(is_active=True).count()
    new_customers = Customer.objects.filter(
        created_at__gte=start_date,
        is_active=True
    ).count()
    
    context = {
        'period': period,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'average_ticket': average_ticket,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
        'total_customers': total_customers,
        'new_customers': new_customers,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
