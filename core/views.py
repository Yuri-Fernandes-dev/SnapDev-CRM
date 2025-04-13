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
    """
    View para o dashboard principal
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    thirty_days_ago = today - timedelta(days=30)
    last_month_start = (today - timedelta(days=60)).replace(day=1)
    last_month_end = (today - timedelta(days=30)).replace(day=1) - timedelta(days=1)

    # Dados do mês atual
    current_month_sales = Sale.objects.filter(
        created_at__date__gte=thirty_days_ago,
        created_at__date__lte=today,
        status='paid'
    )
    
    total_sales = current_month_sales.count()
    
    # Dados do mês anterior para comparação de vendas
    last_month_total_sales = Sale.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lte=last_month_end,
        status='paid'
    ).count()
    
    # Calcular variação do número de vendas
    sales_variation = ((total_sales - last_month_total_sales) / float(last_month_total_sales or 1) * 100)

    current_revenue = current_month_sales.aggregate(
        total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField())
    )['total']
    
    current_ticket = current_month_sales.aggregate(
        avg=Coalesce(Avg('total_amount'), 0, output_field=DecimalField())
    )['avg']

    # Dados do mês anterior
    last_month_sales = Sale.objects.filter(
        created_at__date__gte=last_month_start,
        created_at__date__lte=last_month_end,
        status='paid'
    )
    
    last_month_revenue = last_month_sales.aggregate(
        total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField())
    )['total']

    # Dados de ontem
    yesterday_sales = Sale.objects.filter(
        created_at__date=yesterday,
        status='paid'
    )
    
    yesterday_ticket = yesterday_sales.aggregate(
        avg=Coalesce(Avg('total_amount'), 0, output_field=DecimalField())
    )['avg']

    # Calcular variações evitando divisão por zero
    revenue_variation = ((current_revenue - last_month_revenue) / float(last_month_revenue or 1) * 100)
    ticket_variation = ((current_ticket - yesterday_ticket) / float(yesterday_ticket or 1) * 100)

    # Calcular lucro e margem
    total_profit = current_month_sales.aggregate(
        total=Coalesce(Sum('profit'), 0, output_field=DecimalField())
    )['total']
    
    profit_margin = (total_profit / float(current_revenue or 1) * 100)

    # Produtos mais vendidos
    top_products = SaleItem.objects.filter(
        sale__created_at__date__gte=thirty_days_ago,
        sale__status='paid'
    ).values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_sales=Sum(F('quantity') * F('unit_price')),
        percentage=F('total_sales') * 100.0 / current_revenue if current_revenue > 0 else 0
    ).order_by('-total_sales')[:5]

    # Produtos com estoque baixo
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('stock_alert_level')
    ).annotate(
        stock_value=F('stock_quantity') * F('price')
    ).order_by('stock_quantity')

    # Dados para o gráfico de vendas
    sales_data = Sale.objects.filter(
        created_at__date__gte=thirty_days_ago,
        status='paid'
    ).values('created_at__date').annotate(
        total=Sum('total_amount')
    ).order_by('created_at__date')

    sales_chart_data = {
        'labels': [sale['created_at__date'].strftime('%d/%m') for sale in sales_data],
        'values': [float(sale['total']) for sale in sales_data]
    }

    context = {
        'total_sales': total_sales,
        'sales_variation': sales_variation,
        'total_revenue': current_revenue,
        'revenue_variation': revenue_variation,
        'average_ticket': current_ticket,
        'ticket_variation': ticket_variation,
        'profit_margin': profit_margin,
        'total_profit': total_profit,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'sales_chart_data': sales_chart_data,
    }

    return render(request, 'dashboard/dashboard.html', context)
