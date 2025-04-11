from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Sale, SaleItem, PaymentMethod
from products.models import Product
from customers.models import Customer
from django.db.models import Q, Sum
from django.core.paginator import Paginator
import json
from decimal import Decimal

@login_required
def sale_list(request):
    """
    View para listar vendas com filtros e paginação
    """
    query = request.GET.get('query', '')
    status = request.GET.get('status', '')
    payment_method = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    sales = Sale.objects.all()
    
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
    
    context = {
        'products': products,
        'categories': categories,
        'payment_methods': payment_methods,
        'customers': customers,
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
        data = json.loads(request.body)
        
        customer_id = data.get('customer_id')
        payment_method_id = data.get('payment_method_id')
        items_data = data.get('items', [])
        discount = data.get('discount', 0)
        notes = data.get('notes', '')
        
        # Criar a venda
        sale = Sale.objects.create(
            customer_id=customer_id if customer_id else None,
            payment_method_id=payment_method_id,
            discount=Decimal(discount),
            notes=notes,
            status='pending'
        )
        
        # Adicionar itens à venda
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')
            price = item_data.get('price')
            
            product = get_object_or_404(Product, pk=product_id)
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                price=Decimal(price)
            )
        
        # Finalizar a venda
        sale.status = 'paid'
        sale.save()
        
        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'total': float(sale.total)
        })
    
    return JsonResponse({'success': False}, status=400)

@login_required
def sales_report(request):
    """
    View para relatório de vendas com gráficos
    """
    # Dados para o relatório
    total_sales = Sale.objects.filter(status='paid').count()
    total_revenue = Sale.objects.filter(status='paid').aggregate(total=Sum('total'))['total'] or 0
    
    # Mais dados para gráficos seriam processados aqui
    
    context = {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'sales/sales_report.html', context)
