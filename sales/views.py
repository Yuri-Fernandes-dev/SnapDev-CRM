from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F, DecimalField, CharField, Value, ExpressionWrapper
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
from django.urls import reverse

# Adicionar imports para PDF
import io
from django.template.loader import get_template
from django.template import Context
from urllib.parse import quote

# Try to import WeasyPrint, but don't fail if it's not available
WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    # OSError can happen if the required system libraries are missing
    print("WeasyPrint is not available. PDF generation will be disabled.")
    # Create a dummy HTML class as a placeholder
    class HTML:
        def __init__(self, *args, **kwargs):
            pass
        def render(self, *args, **kwargs):
            return None
        def write_pdf(self, *args, **kwargs):
            return None

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
    sales = Sale.objects.filter(company=request.user.company).select_related('customer', 'payment_method')
    
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
    payment_methods = PaymentMethod.objects.filter(company=request.user.company)
    
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
    View para exibir detalhes de uma venda
    """
    sale = get_object_or_404(
        Sale.objects.select_related('customer', 'payment_method')
        .prefetch_related('items__product'),
        id=pk,
        company=request.user.company
    )
    
    context = {
        'sale': sale,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
    }
    
    return render(request, 'sales/sale_detail.html', context)

@login_required
def point_of_sale(request):
    """
    View principal do PDV (Ponto de Venda)
    """
    products = Product.objects.filter(company=request.user.company, is_active=True)
    categories = Product.objects.filter(company=request.user.company).values_list('category__name', flat=True).distinct()
    payment_methods = PaymentMethod.objects.filter(company=request.user.company)
    customers = Customer.objects.filter(company=request.user.company)
    
    # Preparar dados dos clientes para JSON
    customers_data = [
        {
            'id': c.id, 
            'name': c.name,
            'phone': c.phone if c.phone else None
        } 
        for c in customers
    ]
    
    context = {
        'products': products,
        'categories': categories,
        'payment_methods': payment_methods,
        'customers': customers,
        'customers_json': json.dumps(customers_data, cls=DjangoJSONEncoder),
        'weasyprint_available': WEASYPRINT_AVAILABLE,
    }
    
    return render(request, 'sales/point_of_sale.html', context)

@login_required
def product_search(request):
    """
    View para busca de produtos por AJAX
    """
    query = request.GET.get('query', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.filter(company=request.user.company, is_active=True)
    
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
            payment_method_id = data.get('payment_method')
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
                
                try:
                    product = Product.objects.get(pk=product_id)
                    if product.stock_quantity < quantity:
                        return JsonResponse({
                            'success': False,
                            'error': f'Estoque insuficiente para o produto {product.name}'
                        }, status=400)
                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Produto não encontrado (ID: {product_id})'
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
                company=request.user.company,
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
            
            # Construir a URL do recibo
            try:
                receipt_url = request.build_absolute_uri(
                    reverse('sales:sale_receipt', args=[sale.id])
                )
                
                # Verificar se o cliente tem telefone
                has_phone = False
                phone = None
                if sale.customer and sale.customer.phone:
                    has_phone = True
                    phone = ''.join(filter(str.isdigit, sale.customer.phone))
                    if not phone.startswith('55'):
                        phone = '55' + phone
            except Exception as e:
                print(f"Erro ao gerar URL de recibo: {str(e)}")
                receipt_url = None
                has_phone = False
                phone = None
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'total': float(sale.total),
                'receipt_url': receipt_url,
                'has_phone': has_phone,
                'customer_phone': phone
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
        company=request.user.company,
        created_at__gte=start_date,
        status='paid'
    )
    
    # Vendas no período anterior
    sales_previous = Sale.objects.filter(
        company=request.user.company,
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

    # Preparar dados para o gráfico
    chart_data = {
        'labels': [],
        'values': []
    }

    for sale in sales_by_date:
        chart_data['labels'].append(sale['date'].strftime('%d/%m'))
        chart_data['values'].append(float(sale['total_revenue']))

    # Converter para JSON
    sales_chart_data = json.dumps(chart_data)

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
    
    # Calcular lucro total e margem de lucro
    total_profit = SaleItem.objects.filter(
        sale__in=sales
    ).annotate(
        profit=ExpressionWrapper(
            (F('price') - F('product__cost')) * F('quantity'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).aggregate(
        total=Sum('profit')
    )['total'] or Decimal('0')

    # Calcular margem de lucro
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
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
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'sales_chart_data': sales_chart_data,
    }
    
    return render(request, 'sales/sales_report.html', context)

@login_required
def reports(request):
    """
    View para exibir relatórios de vendas
    """
    # Obtém o período selecionado (padrão: 30 dias)
    period = request.GET.get('period', '30')
    start_date = timezone.now().date() - timedelta(days=int(period))
    
    # Obtém as vendas do período
    sales = Sale.objects.filter(
        company=request.user.company,
        created_at__date__gte=start_date,
        status='paid'
    )
    
    # Calcula as métricas
    total_sales = sales.count()
    total_revenue = sales.aggregate(total=Sum('total'))['total'] or 0
    average_ticket = total_revenue / total_sales if total_sales > 0 else 0
    
    # Calcula o lucro total e margem
    total_cost = sales.aggregate(
        total=Sum(F('items__quantity') * F('items__cost_price'))
    )['total'] or 0
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Dados para o gráfico
    sales_by_date = sales.values('created_at__date').annotate(
        total_sales=Count('id'),
        total_revenue=Sum('total')
    ).order_by('created_at__date')
    
    chart_data = {
        'labels': [sale['created_at__date'].strftime('%d/%m/%Y') for sale in sales_by_date],
        'revenue': [float(sale['total_revenue']) for sale in sales_by_date],
        'sales': [sale['total_sales'] for sale in sales_by_date]
    }
    
    context = {
        'period': period,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'average_ticket': average_ticket,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'chart_data': chart_data
    }
    
    return render(request, 'sales/reports.html', context)

@login_required
def cancel_sale(request, sale_id):
    """
    View para cancelar uma venda
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
        
    sale = get_object_or_404(
        Sale,
        id=sale_id,
        company=request.user.company
    )
    
    if sale.status == 'cancelled':
        return JsonResponse({'error': 'Venda já está cancelada'}, status=400)
        
    # Retorna os produtos para o estoque
    for item in sale.items.all():
        item.product.quantity += item.quantity
        item.product.save()
        
    sale.status = 'cancelled'
    sale.save()
    
    return JsonResponse({'success': True})

@login_required
def sale_receipt(request, pk):
    """
    View para gerar recibo de venda
    """
    sale = get_object_or_404(Sale, pk=pk, company=request.user.company)
    items = sale.items.all().select_related('product')
    
    context = {
        'sale': sale,
        'items': items,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
    }
    
    return render(request, 'sales/sale_receipt.html', context)

@login_required
def sale_pdf(request, pk):
    """
    Trata solicitações de PDF/WhatsApp mesmo sem o WeasyPrint
    """
    try:
        sale = get_object_or_404(Sale, pk=pk, company=request.user.company)
        
        # Check if PDF generation is available
        if not WEASYPRINT_AVAILABLE and not request.GET.get('whatsapp') == 'true':
            messages.warning(request, "A geração de PDF está desativada. Faltam bibliotecas necessárias (WeasyPrint/GTK).")
            return redirect('sales:sale_receipt', pk=pk)
        
        # Verificar se deve enviar para WhatsApp
        if request.GET.get('whatsapp') == 'true' and sale.customer and sale.customer.phone:
            # Criar telefone para WhatsApp
            phone = ''.join(filter(str.isdigit, sale.customer.phone))
            if not phone.startswith('55'):
                phone = '55' + phone
                
            # Criar uma mensagem para o WhatsApp
            receipt_url = request.build_absolute_uri(
                reverse('sales:sale_receipt', args=[sale.id])
            )
            message = f"Olá {sale.customer.name}, segue o recibo da sua compra #{sale.id} no valor de R$ {sale.total:.2f}. Obrigado pela preferência! {receipt_url}"
            whatsapp_url = f"https://wa.me/{phone}?text={quote(message)}"
            
            return redirect(whatsapp_url)
        
        # Caso não seja WhatsApp, redireciona para a página de recibo
        return redirect('sales:sale_receipt', pk=pk)
        
    except Exception as e:
        print(f"Erro ao gerar PDF/WhatsApp: {str(e)}")
        messages.error(request, "Não foi possível gerar o PDF ou enviar por WhatsApp.")
        return redirect('sales:sale_receipt', pk=pk)
