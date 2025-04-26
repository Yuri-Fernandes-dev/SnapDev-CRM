from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, Count, Avg, F, DecimalField, CharField, Value, ExpressionWrapper, Min, Max
from django.db.models.functions import Concat, TruncDate, ExtractHour, ExtractWeekDay
from django.core.paginator import Paginator
from django.utils import timezone
from django.template.exceptions import TemplateDoesNotExist
from datetime import timedelta
import json
import numpy as np
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from .models import Sale, SaleItem, PaymentMethod
from products.models import Product
from customers.models import Customer
from django.urls import reverse
from django.db import transaction
from django.core.exceptions import ValidationError

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
    # OSError pode ocorrer se as bibliotecas de sistema necessárias estiverem ausentes
    print("WeasyPrint não está disponível. A geração de PDF será desativada.")
    # Criar uma classe HTML dummy como um placeholder
    class HTML:
        def __init__(self, *args, **kwargs):
            pass
        def render(self, *args, **kwargs):
            return None
        def write_pdf(self, *args, **kwargs):
            return None

from django.views.decorators.csrf import csrf_exempt

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

@csrf_exempt
@login_required
def adicionar_item(request):
    """
    View para adicionar item ao carrinho via AJAX
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    # Log dos dados recebidos para debug
    logger.debug(f"Dados recebidos: {request.POST}")
    
    # Obter e validar produto_id
    try:
        produto_id = request.POST.get('produto_id')
        if not produto_id:
            return JsonResponse({'error': 'ID do produto não fornecido'}, status=400)
        
        # Verificar se o produto existe
        produto = get_object_or_404(Product, id=produto_id, company=request.user.company)
        
        # Validar quantidade
        try:
            quantidade = int(request.POST.get('quantidade', 1))
            if quantidade <= 0:
                return JsonResponse({'error': 'Quantidade deve ser maior que zero'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Quantidade inválida'}, status=400)
            
        # Verificar estoque
        if produto.stock_quantity < quantidade:
            return JsonResponse({'error': f'Estoque insuficiente. Disponível: {produto.stock_quantity}'}, status=400)
        
        # Inicializar carrinho na sessão se não existir
        if 'carrinho' not in request.session:
            request.session['carrinho'] = []
        
        carrinho = request.session['carrinho']
        
        # Verificar se o produto já está no carrinho
        for item in carrinho:
            if item['produto_id'] == produto_id:
                # Atualizar quantidade
                item['quantidade'] += quantidade
                break
        else:
            # Adicionar novo item
            carrinho.append({
                'produto_id': produto_id,
                'nome': produto.name,
                'preco': str(produto.price),  # Usar str para Decimal
                'codigo': produto.code,
                'quantidade': quantidade
            })
        
        # Salvar carrinho atualizado na sessão
        request.session['carrinho'] = carrinho
        request.session.modified = True
        
        logger.debug(f"Carrinho após adição: {carrinho}")
        
        # Renderizar a tabela de itens atualizada
        # Tentativa 1: Template padrão do app
        try:
            return render(request, 'sales/itens_venda.html', {'carrinho': carrinho})
        except TemplateDoesNotExist:
            # Tentativa 2: Template do sistema (caminho alternativo)
            try:
                return render(request, 'sistema/vendas/itens_venda.html', {'carrinho': carrinho})
            except TemplateDoesNotExist:
                # Último recurso: retornar JSON
                return JsonResponse({
                    'success': True,
                    'message': 'Item adicionado ao carrinho, mas o template não foi encontrado.'
                })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar item: {str(e)}")
        return JsonResponse({'error': f'Erro ao adicionar item: {str(e)}'}, status=500)

@login_required
def create_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar dados básicos
            if not data.get('items'):
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhum item foi adicionado à venda'
                }, status=400)

            # Verificar estoque de todos os itens primeiro (antes de iniciar a transação)
            stock_errors = []
            for item in data['items']:
                try:
                    product = Product.objects.get(id=item['product_id'], company=request.user.company)
                    if product.stock_quantity < item['quantity']:
                        stock_errors.append(f'Estoque insuficiente para o produto {product.name}. Disponível: {product.stock_quantity}, Requisitado: {item["quantity"]}')
                except Product.DoesNotExist:
                    stock_errors.append(f'Produto não encontrado: {item["product_id"]}')
            
            # Se houver algum erro de estoque, retornar imediatamente
            if stock_errors:
                return JsonResponse({
                    'success': False,
                    'error': '\n'.join(stock_errors)
                }, status=400)

            # Criar a venda
            with transaction.atomic():
                sale = Sale.objects.create(
                    company=request.user.company,
                    customer_id=data.get('customer_id'),
                    payment_method_id=data['payment_method'],
                    total=Decimal('0'),
                    discount=Decimal(str(data.get('discount', '0'))),
                    notes=data.get('notes', ''),
                    created_by=request.user,
                    status='paid'
                )

                # Processar itens
                total = Decimal('0')
                for item in data['items']:
                    try:
                        # Usar SELECT FOR UPDATE para bloquear a linha do produto durante a transação
                        product = Product.objects.select_for_update().get(id=item['product_id'], company=request.user.company)
                        
                        # Garantir que a quantidade do pedido seja um inteiro positivo
                        quantity = max(1, int(item['quantity']))
                        
                        # Verificar novamente o estoque com a linha bloqueada
                        if product.stock_quantity < quantity:
                            # Erro dentro da transação, causará rollback automático
                            raise ValidationError(f'Estoque insuficiente para o produto {product.name}. Disponível: {product.stock_quantity}, Requisitado: {quantity}')
                            
                        price = Decimal(str(item['price']))
                        subtotal = price * quantity
                        
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            price=price,
                            cost_price=product.cost,
                            subtotal=subtotal
                        )
                        
                        total += subtotal
                        
                        # Atualizar estoque - método seguro para evitar o erro de CombinedExpression
                        new_stock = product.stock_quantity - quantity
                        product.stock_quantity = max(0, new_stock)  # Garantir que não fique negativo
                        product.save()
                        
                    except Product.DoesNotExist:
                        # Erro dentro da transação, causará rollback automático
                        raise ValidationError(f'Produto não encontrado: {item["product_id"]}')

                # Atualizar o total da venda
                sale.total = total - sale.discount
                sale.save()

                # Se tiver cliente, adicionar pontos de fidelidade
                if sale.customer:
                    sale.customer.add_points(sale.total)
                    sale.customer.save()

                return JsonResponse({
                    'success': True, 
                    'sale_id': sale.id,
                    'has_phone': bool(sale.customer and sale.customer.phone) if sale.customer else False
                })

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Dados da venda inválidos'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erro ao processar a venda: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Método não permitido'
    }, status=405)

@login_required
def sales_report(request):
    """
    View para exibir relatórios de vendas com análises detalhadas
    """
    period = request.GET.get('period', '30')
    days = int(period)
    category = request.GET.get('category', '')
    sort = request.GET.get('sort', 'date')
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Query base de vendas
    sales_query = Sale.objects.filter(
        company=request.user.company,
        status='paid',
        created_at__gte=start_date
    )
    
    # Análise por método de pagamento
    payment_analysis = (
        sales_query
        .values('payment_method__name')
        .annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            avg_ticket=ExpressionWrapper(
                Sum('total') / Count('id'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        .order_by('-total_revenue')
    )
    
    # Análise de horários de pico
    peak_hours = (
        sales_query
        .annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total')
        )
        .order_by('hour')
    )
    
    # Análise de dias da semana
    weekday_analysis = (
        sales_query
        .annotate(weekday=ExtractWeekDay('created_at'))
        .values('weekday')
        .annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total')
        )
        .order_by('weekday')
    )
    
    # Análise de recorrência de clientes
    customer_recurrence = (
        sales_query
        .values('customer')
        .annotate(
            purchase_count=Count('id'),
            total_spent=Sum('total'),
            avg_ticket=Avg('total'),
            first_purchase=Min('created_at'),
            last_purchase=Max('created_at')
        )
        .filter(customer__isnull=False)
        .order_by('-purchase_count')
    )
    
    # Calcular outros indicadores importantes
    totals = sales_query.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('total'),
        total_items=Sum('items__quantity'),
        total_cost=Sum(F('items__quantity') * F('items__cost_price')),
        avg_items_per_sale=Avg('items__quantity')
    )
    
    total_sales = totals['total_sales'] or 0
    total_revenue = totals['total_revenue'] or 0
    total_items = totals['total_items'] or 0
    total_cost = totals['total_cost'] or 0
    avg_items_per_sale = totals['avg_items_per_sale'] or 0
    
    # Calcular métricas de performance
    average_ticket = total_revenue / total_sales if total_sales > 0 else 0
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Produtos e categorias mais vendidos
    top_products = (
        SaleItem.objects
        .filter(sale__in=sales_query)
        .values('product__name', 'product__code')
        .annotate(
            name=F('product__name'),
            code=F('product__code'),
            quantity=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price')),
            profit=Sum(F('quantity') * (F('price') - F('cost_price'))),
            margin=ExpressionWrapper(
                Sum(F('quantity') * (F('price') - F('cost_price'))) / Sum(F('quantity') * F('price')) * 100,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        .order_by('-quantity' if sort == 'quantity' else '-revenue')[:10]
    )
    
    # Análise de vendas por dia com tendência
    sales_by_date = (
        sales_query
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            items_sold=Sum('items__quantity'),
            avg_ticket=Avg('total')
        )
        .order_by('date')
    )
    
    # Dados para o gráfico
    chart_data = {
        'labels': [sale['date'].strftime('%d/%m') for sale in sales_by_date],
        'values': [float(sale['total_revenue']) for sale in sales_by_date],
        'items': [int(sale['items_sold'] or 0) for sale in sales_by_date],
        'sales_count': [int(sale['total_sales']) for sale in sales_by_date],
        'avg_tickets': [float(sale['avg_ticket'] or 0) for sale in sales_by_date]
    }
    
    context = {
        'period': period,
        'category': category,
        'sort': sort,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'average_ticket': average_ticket,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'avg_items_per_sale': avg_items_per_sale,
        'sales_by_date': sales_by_date,
        'top_products': top_products,
        'payment_analysis': payment_analysis,
        'peak_hours': peak_hours,
        'weekday_analysis': weekday_analysis,
        'customer_recurrence': customer_recurrence,
        'chart_data': json.dumps(chart_data, cls=DjangoJSONEncoder)
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

@login_required
def send_whatsapp_message(request, pk):
    """
    Envia uma mensagem de agradecimento para o WhatsApp do cliente
    """
    try:
        sale = get_object_or_404(Sale, pk=pk, company=request.user.company)
        
        # Verificar se o cliente tem telefone
        if not sale.customer or not sale.customer.phone:
            messages.warning(request, "O cliente não possui número de telefone cadastrado.")
            return redirect('sales:sale_receipt', pk=pk)
        
        # Preparar número de telefone para WhatsApp
        phone = ''.join(filter(str.isdigit, sale.customer.phone))
        if not phone.startswith('55'):
            phone = '55' + phone
        
        # Obter o domínio completo da aplicação
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()
        
        # Criar URL absoluta do recibo público
        receipt_url = f"{protocol}://{domain}/r/{sale.access_token}/"
        
        # Criar mensagem personalizada de agradecimento
        company_name = request.user.company.name
        
        # Formatar a lista de produtos
        items_text = ""
        for i, item in enumerate(sale.items.all()[:3], 1):
            items_text += f"\n{i}. {item.product.name} x{item.quantity}"
        
        if sale.items.count() > 3:
            items_text += f"\n... e mais {sale.items.count() - 3} item(ns)"
            
        # Montar mensagem completa
        message = (
            f"Olá {sale.customer.name}! 😊\n\n"
            f"Obrigado pela sua compra no valor de *R$ {sale.total:.2f}* em *{company_name}*.\n\n"
            f"*Resumo do pedido:*{items_text}\n\n"
            f"Seu recibo está disponível em:\n{receipt_url}\n\n"
            f"Agradecemos a preferência! - {company_name} 👋"
        )
        
        # Montar URL do WhatsApp
        whatsapp_url = f"https://wa.me/{phone}?text={quote(message)}"
        
        # Redirecionar para o WhatsApp
        return redirect(whatsapp_url)
        
    except Exception as e:
        messages.error(request, f"Erro ao enviar mensagem: {str(e)}")
        return redirect('sales:sale_receipt', pk=pk)

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

def public_receipt(request, token):
    """
    View para recibo público, acessível sem login
    """
    # Encontrar a venda pelo token de acesso
    try:
        sale = Sale.objects.get(access_token=token)
        items = sale.items.all().select_related('product')
        
        context = {
            'sale': sale,
            'items': items,
            'is_public': True,
            'company': sale.company
        }
        
        return render(request, 'sales/public_receipt.html', context)
    except Sale.DoesNotExist:
        # Se o token for inválido, mostrar uma página de erro
        context = {
            'error_message': 'O recibo solicitado não foi encontrado ou expirou.'
        }
        return render(request, 'sales/receipt_error.html', context)

@login_required
def check_stock(request):
    """
    View para verificar se há estoque disponível para um produto
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'ID do produto não fornecido'
            }, status=400)
        
        try:
            product = Product.objects.get(id=product_id, company=request.user.company)
            
            if product.stock_quantity < quantity:
                return JsonResponse({
                    'success': False,
                    'error': f'Estoque insuficiente para o produto {product.name}',
                    'available': product.stock_quantity,
                    'requested': quantity
                }, status=200)  # Retornamos 200 mesmo com erro para processamento no frontend
            
            return JsonResponse({
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'available': product.stock_quantity,
                    'requested': quantity
                }
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Produto não encontrado'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao verificar estoque: {str(e)}'
        }, status=500)
