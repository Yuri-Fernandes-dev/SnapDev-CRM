from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, Avg, F, DecimalField, CharField, Value
from django.db.models.functions import Concat
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from .models import Sale, SaleItem, PaymentMethod
from products.models import Product
from customers.models import Customer

@login_required
def sale_list(request):
    """
    View para listar vendas com filtros e paginação
    """
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    payment_method = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Query base
    sales = Sale.objects.all().select_related('customer', 'payment_method')
    
    # Filtro por busca
    if query:
        sales = sales.filter(
            Q(customer__name__icontains=query) |
            Q(notes__icontains=query)
        )
    
    # Filtro por status
    if status:
        sales = sales.filter(status=status)
    
    # Filtro por método de pagamento
    if payment_method:
        sales = sales.filter(payment_method_id=payment_method)
    
    # Filtro por data
    if date_from:
        sales = sales.filter(created_at__date__gte=date_from)
    
    if date_to:
        sales = sales.filter(created_at__date__lte=date_to)
    
    # Estatísticas
    total_sales = sales.count()
    total_revenue = float(sales.aggregate(total=Sum('total'))['total'] or 0)
    avg_ticket = total_revenue / total_sales if total_sales > 0 else 0
    
    # Total de itens vendidos
    total_items = (
        SaleItem.objects
        .filter(sale__in=sales)
        .aggregate(total=Sum('quantity'))['total'] or 0
    )
    
    # Adicionar contagem de itens para cada venda
    sales = sales.annotate(items_count=Sum('items__quantity'))
    
    # Ordenação
    sales = sales.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(sales, 10)
    page_number = request.GET.get('page', 1)
    sales_page = paginator.get_page(page_number)
    
    # Contexto
    payment_methods = PaymentMethod.objects.all()
    
    context = {
        'sales': sales_page,
        'payment_methods': payment_methods,
        'query': query,
        'status': status,
        'payment_method': payment_method,
        'date_from': date_from,
        'date_to': date_to,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'avg_ticket': avg_ticket,
        'total_items': total_items,
    }
    
    return render(request, 'sales/sale_list.html', context)

@login_required
def sale_detail(request, pk):
    """
    View para detalhes de uma venda
    """
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'items': items})

@login_required
def point_of_sale(request):
    """
    View principal do PDV (Ponto de Venda)
    """
    products = Product.objects.filter(is_active=True)
    categories = Product.objects.values_list('category__name', flat=True).distinct()
    payment_methods = PaymentMethod.objects.all()
    customers = Customer.objects.all()
    
    # Preparar dados dos clientes para JSON
    customers_data = [{'id': c.id, 'name': c.name} for c in customers]
    
    context = {
        'products': products,
        'categories': categories,
        'payment_methods': payment_methods,
        'customers': customers,
        'customers_json': json.dumps(customers_data, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'sales/point_of_sale.html', context)

@login_required
def product_search(request):
    """
    View para busca de produtos por AJAX
    """
    query = request.GET.get('query', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(barcode__icontains=query)
        )
    
    if category:
        products = products.filter(category_id=category)
    
    product_list = []
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'code': product.code,
            'price': float(product.price),
            'stock': product.stock_quantity,
            'category': product.category.name if product.category else '',
        }
        product_list.append(product_data)
    
    return JsonResponse({'products': product_list})

@login_required
def create_sale(request):
    """
    View para criar uma nova venda via AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            customer_id = data.get('customer_id')
            payment_method_id = data.get('payment_method_id')
            items_data = data.get('items', [])
            discount = data.get('discount', 0)
            notes = data.get('notes', '')
            
            if not payment_method_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Método de pagamento é obrigatório'
                }, status=400)
            
            if not items_data:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhum item adicionado à venda'
                }, status=400)
            
            # Validar estoque antes de criar a venda
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = int(item_data.get('quantity'))
                
                product = Product.objects.get(pk=product_id)
                if product.stock_quantity < quantity:
                    return JsonResponse({
                        'success': False,
                        'error': f'Estoque insuficiente para o produto {product.name}'
                    }, status=400)
            
            # Calcular o total antes de criar a venda
            total = Decimal('0')
            for item_data in items_data:
                quantity = int(item_data.get('quantity'))
                price = Decimal(str(item_data.get('price')))
                total += quantity * price
            
            # Aplicar desconto
            discount = Decimal(str(discount))
            total = total - discount if total > discount else Decimal('0')
            
            # Criar a venda com o total já calculado
            sale = Sale.objects.create(
                customer_id=customer_id if customer_id else None,
                payment_method_id=payment_method_id,
                created_by=request.user,
                discount=discount,
                notes=notes,
                total=total,
                status='pending'
            )
            
            # Adicionar itens à venda
            for item_data in items_data:
                product_id = item_data.get('product_id')
                quantity = int(item_data.get('quantity'))
                price = Decimal(str(item_data.get('price')))
                
                product = Product.objects.get(pk=product_id)
                
                # Criar o item da venda
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price=price,
                    subtotal=quantity * price
                )
                
                # Atualizar estoque
                product.stock_quantity -= quantity
                product.save()
            
            # Finalizar a venda
            sale.status = 'paid'
            sale.save()
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'total': float(sale.total)
            })
            
        except Exception as e:
            print(f"Erro ao criar venda: {str(e)}")  # Debug
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)

@login_required
def sales_report(request):
    """
    View para relatório de vendas com gráficos
    """
    # Obtém o período selecionado (padrão: 30 dias)
    period = request.GET.get('period', '30')
    days = int(period)
    
    # Data inicial do período atual
    if days == 1:
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = timezone.now() - timedelta(days=days)
    
    # Data inicial do período anterior (para comparação)
    start_date_previous = start_date - timedelta(days=days)
    
    # Vendas no período atual
    sales = Sale.objects.filter(
        created_at__gte=start_date,
        status='paid'
    )
    
    # Vendas no período anterior
    sales_previous = Sale.objects.filter(
        created_at__gte=start_date_previous,
        created_at__lt=start_date,
        status='paid'
    )
    
    # Métricas do período atual
    total_sales = sales.count()
    total_revenue = sales.aggregate(
        total=Sum('total', output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or 0
    average_ticket = total_revenue / total_sales if total_sales > 0 else 0
    
    # Métricas do período anterior
    total_sales_previous = sales_previous.count()
    total_revenue_previous = sales_previous.aggregate(
        total=Sum('total', output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total'] or 0
    average_ticket_previous = total_revenue_previous / total_sales_previous if total_sales_previous > 0 else 0
    
    # Calcular variações percentuais
    sales_variation = ((total_sales - total_sales_previous) / total_sales_previous * 100) if total_sales_previous > 0 else 0
    revenue_variation = ((total_revenue - total_revenue_previous) / total_revenue_previous * 100) if total_revenue_previous > 0 else 0
    ticket_variation = ((average_ticket - average_ticket_previous) / average_ticket_previous * 100) if average_ticket_previous > 0 else 0
    
    # Taxa de conversão atual
    total_attempts = Sale.objects.filter(created_at__gte=start_date).count()
    conversion_rate = (total_sales / total_attempts * 100) if total_attempts > 0 else 0
    
    # Taxa de conversão anterior
    total_attempts_previous = Sale.objects.filter(
        created_at__gte=start_date_previous,
        created_at__lt=start_date
    ).count()
    conversion_rate_previous = (total_sales_previous / total_attempts_previous * 100) if total_attempts_previous > 0 else 0
    
    # Variação da taxa de conversão
    conversion_variation = ((conversion_rate - conversion_rate_previous) / conversion_rate_previous * 100) if conversion_rate_previous > 0 else 0
    
    # Vendas por dia
    sales_by_date = sales.values('created_at__date').annotate(
        date=F('created_at__date'),
        total_sales=Count('id'),
        total_revenue=Sum('total', output_field=DecimalField(max_digits=10, decimal_places=2)),
        avg_ticket=Avg('total', output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('created_at__date')
    
    # Adicionar taxa de conversão por dia
    for sale in sales_by_date:
        daily_attempts = Sale.objects.filter(
            created_at__date=sale['date']
        ).count()
        sale['conversion_rate'] = (sale['total_sales'] / daily_attempts * 100) if daily_attempts > 0 else 0
    
    # Produtos mais vendidos
    top_products = SaleItem.objects.filter(
        sale__in=sales
    ).values(
        'product__name'
    ).annotate(
        name=F('product__name'),
        quantity=Sum('quantity'),
        revenue=Sum('subtotal', output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('-quantity')[:10]
    
    # Desempenho por vendedor
    sellers = Sale.objects.filter(
        id__in=sales
    ).values(
        'created_by__username',
        'created_by__first_name',
        'created_by__last_name'
    ).annotate(
        name=Concat(
            F('created_by__first_name'),
            Value(' '),
            F('created_by__last_name'),
            output_field=CharField()
        ),
        username=F('created_by__username'),
        total_sales=Count('id'),
        total_revenue=Sum('total', output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('-total_revenue')
    
    # Adicionar ticket médio por vendedor e tratar nomes vazios
    for seller in sellers:
        seller['avg_ticket'] = seller['total_revenue'] / seller['total_sales'] if seller['total_sales'] > 0 else 0
        if not seller['name'] or seller['name'].strip() == ' ':
            seller['name'] = seller['username']
    
    context = {
        'period': period,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'average_ticket': average_ticket,
        'conversion_rate': conversion_rate,
        'sales_variation': sales_variation,
        'revenue_variation': revenue_variation,
        'ticket_variation': ticket_variation,
        'conversion_variation': conversion_variation,
        'sales_by_date': sales_by_date,
        'top_products': top_products,
        'sellers': sellers,
    }
    
    return render(request, 'sales/sales_report.html', context)
