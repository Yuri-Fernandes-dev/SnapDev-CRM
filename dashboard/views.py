from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from datetime import timedelta
import json

@login_required
def dashboard(request):
    """
    View principal do dashboard com resumo geral
    """
    # Obter período de filtro (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = timezone.now().date() - timedelta(days=days)
    end_date = timezone.now().date()
    
    # Métricas de vendas
    sales_data = Sale.objects.filter(status='paid', created_at__date__gte=start_date)
    total_sales = sales_data.count()
    total_revenue = float(sales_data.aggregate(total=Sum('total'))['total'] or 0)
    
    # Produtos mais vendidos
    top_products = (
        SaleItem.objects
        .filter(sale__status='paid', sale__created_at__date__gte=start_date)
        .values('product__name')
        .annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum(F('price') * F('quantity'))
        )
        .order_by('-total_qty')[:5]
    )
    
    # Calcular porcentagem para cada produto
    if top_products:
        max_qty = top_products[0]['total_qty']
        for product in top_products:
            product['percentage'] = (product['total_qty'] / max_qty * 100) if max_qty > 0 else 0
    
    # Produtos com estoque baixo
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')[:5]
    
    # Add stock value calculation for each product
    for product in low_stock_products:
        product.stock_value = float(product.stock_quantity * product.cost)
    
    # Contagem de clientes
    total_customers = Customer.objects.count()
    new_customers = Customer.objects.filter(created_at__date__gte=start_date).count()
    
    # Gerar lista de datas para o período
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Dados para o gráfico de vendas diárias
    daily_sales = (
        Sale.objects
        .filter(status='paid', created_at__date__gte=start_date, created_at__date__lte=end_date)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(total=Sum('total'))
        .order_by('date')
    )
    
    # Criar dicionário com vendas por data
    sales_by_date = {sale['date']: float(sale['total']) for sale in daily_sales}
    
    # Formatação para o gráfico (preenchendo datas sem vendas com 0)
    sales_chart_data = {
        'labels': [date.strftime('%d/%m') for date in dates],
        'values': [sales_by_date.get(date, 0) for date in dates]
    }
    
    # Garantir que os valores são serializáveis
    sales_chart_data = json.dumps(sales_chart_data)
    
    # Cálculo da lucratividade (baseada no custo dos produtos)
    profit_data = (
        SaleItem.objects
        .filter(sale__status='paid', sale__created_at__date__gte=start_date)
        .annotate(
            profit=ExpressionWrapper(
                (F('price') - F('product__cost')) * F('quantity'),
                output_field=DecimalField()
            )
        )
        .aggregate(total_profit=Sum('profit'))
    )
    
    total_profit = float(profit_data['total_profit'] or 0)
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calcular ticket médio
    average_ticket = total_revenue / total_sales if total_sales > 0 else 0
    
    context = {
        'period': period,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'sales_chart_data': sales_chart_data,
        'average_ticket': average_ticket,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def inventory_dashboard(request):
    """
    View para dashboard de estoque
    """
    # Produtos com estoque baixo
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')
    
    # Valor total do estoque
    stock_value = Product.objects.aggregate(
        total_value=Sum(F('stock_quantity') * F('cost'))
    )['total_value'] or 0
    
    # Produtos por categoria
    products_by_category = (
        Product.objects
        .values('category__name')
        .annotate(count=Count('id'), total_value=Sum(F('stock_quantity') * F('cost')))
        .order_by('-count')
    )
    
    context = {
        'low_stock_products': low_stock_products,
        'stock_value': stock_value,
        'products_by_category': products_by_category,
    }
    
    return render(request, 'dashboard/inventory_dashboard.html', context)

@login_required
def sales_dashboard(request):
    """
    View para dashboard de vendas
    """
    # Obter período de filtro (padrão: últimos 90 dias)
    period = request.GET.get('period', '90')
    
    try:
        days = int(period)
    except ValueError:
        days = 90
    
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Vendas por mês
    monthly_sales = (
        Sale.objects
        .filter(status='paid', created_at__date__gte=start_date)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('month')
    )
    
    # Vendas por método de pagamento
    sales_by_payment = (
        Sale.objects
        .filter(status='paid', created_at__date__gte=start_date)
        .values('payment_method__name')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('-total')
    )
    
    # Ticket médio
    avg_ticket = (
        Sale.objects
        .filter(status='paid', created_at__date__gte=start_date)
        .aggregate(avg=Avg('total'))['avg'] or 0
    )
    
    context = {
        'period': period,
        'monthly_sales': monthly_sales,
        'sales_by_payment': sales_by_payment,
        'avg_ticket': avg_ticket,
    }
    
    return render(request, 'dashboard/sales_dashboard.html', context)

@login_required
def customers_dashboard(request):
    """
    View para dashboard de clientes
    """
    # Clientes que mais compram
    top_customers = (
        Sale.objects
        .filter(status='paid')
        .values('customer__name')
        .annotate(total_spent=Sum('total'), order_count=Count('id'))
        .filter(customer__isnull=False)
        .order_by('-total_spent')[:10]
    )
    
    # Clientes por cidade
    customers_by_city = (
        Customer.objects
        .values('city')
        .annotate(count=Count('id'))
        .filter(city__isnull=False)
        .exclude(city='')
        .order_by('-count')[:10]
    )
    
    context = {
        'top_customers': top_customers,
        'customers_by_city': customers_by_city,
    }
    
    return render(request, 'dashboard/customers_dashboard.html', context)
