from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta, datetime
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from .models import ExpenseCategory, Expense
import json
import logging
import traceback
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

# Função para verificar a autenticação do usuário via AJAX
@require_http_methods(["GET"])
def check_auth(request):
    """
    View para verificar se o usuário está autenticado via AJAX
    Retorna um JSON com o status de autenticação
    """
    return JsonResponse({
        'authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None
    })

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
    
    # Configuração do filtro de data
    end_date = timezone.now().date()
    
    if days == 1:
        # Se o período for de 1 dia, filtra apenas o dia atual
        start_date = end_date
    else:
        # Para outros períodos, subtrai os dias
        start_date = end_date - timedelta(days=days-1)
    
    # Métricas de vendas - filtrar por empresa
    sales_data = Sale.objects.filter(
        company=request.user.company,
        status='paid', 
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    total_sales = sales_data.count()
    total_revenue = float(sales_data.aggregate(total=Sum('total'))['total'] or 0)
    
    # Buscar despesas no período selecionado
    expenses_data = Expense.objects.filter(
        company=request.user.company,
        date__gte=start_date,
        date__lte=end_date
    )
    total_expenses = float(expenses_data.aggregate(total=Sum('amount'))['total'] or 0)
    
    # Produtos mais vendidos - filtrar por empresa
    top_products = (
        SaleItem.objects
        .filter(
            sale__company=request.user.company,
            sale__status='paid', 
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=end_date,
            product__company=request.user.company
        )
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
        colors = ['#4c6ef5', '#38d6ae', '#f59f00', '#fa5252', '#be4bdb']
        
        for i, product in enumerate(top_products):
            product['percentage'] = (product['total_qty'] / max_qty * 100) if max_qty > 0 else 0
            product['color'] = colors[i % len(colors)]  # Adicionar cor para o gráfico
    
    # Produtos com estoque baixo - filtrar por empresa
    low_stock_products = Product.objects.filter(
        company=request.user.company,
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')[:5]
    
    # Add stock value calculation for each product
    for product in low_stock_products:
        product.stock_value = float(product.stock_quantity * product.cost)
    
    # Total de clientes - filtrar por empresa
    total_customers = Customer.objects.filter(company=request.user.company).count()
    
    # Novos clientes nos últimos 30 dias - filtrar por empresa
    new_customers = Customer.objects.filter(
        company=request.user.company,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    # Dados para o gráfico de vendas
    sales_chart_data = []
    for i in range(days):
        date = end_date - timedelta(days=days-i-1)
        
        # Contar vendas do dia - filtrar por empresa
        day_sales = Sale.objects.filter(
            company=request.user.company,
            status='paid',
            created_at__date=date
        ).count()
        
        sales_chart_data.append({
            'date': date.strftime('%d/%m'),
            'sales': day_sales
        })
    
    # Calcular ticket médio
    average_ticket = total_revenue / total_sales if total_sales > 0 else 0
    
    # Cálculo da lucratividade (baseada no custo dos produtos)
    profit_data = (
        SaleItem.objects
        .filter(
            sale__company=request.user.company,
            sale__status='paid', 
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=end_date
        )
        .annotate(
            profit=ExpressionWrapper(
                (F('price') - F('cost_price')) * F('quantity'),
                output_field=DecimalField()
            )
        )
        .aggregate(total_profit=Sum('profit'))
    )
    
    total_profit = float(profit_data['total_profit'] or 0)
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Adicionar o valor absoluto da margem para usar quando negativa
    profit_margin_abs = abs(profit_margin)
    
    context = {
        'period': period,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'profit_margin_abs': profit_margin_abs,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'sales_chart_data': sales_chart_data,
        'average_ticket': average_ticket,
        'total_expenses': total_expenses,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def inventory_dashboard(request):
    """
    View do dashboard de estoque com resumo dos produtos e níveis de estoque
    """
    # Obter período de filtro (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Configuração do filtro de data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Produtos com estoque baixo - filtrar por empresa
    low_stock_products = Product.objects.filter(
        company=request.user.company,
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')[:10]
    
    # Produtos com maior valor em estoque - filtrar por empresa
    high_value_products = Product.objects.filter(
        company=request.user.company,
    ).annotate(
        stock_value=ExpressionWrapper(
            F('stock_quantity') * F('cost'), 
            output_field=DecimalField()
        )
    ).order_by('-stock_value')[:10]
    
    # Cálculo do valor total em estoque
    inventory_value = Product.objects.filter(
        company=request.user.company
    ).annotate(
        value=ExpressionWrapper(
            F('stock_quantity') * F('cost'),
            output_field=DecimalField()
        )
    ).aggregate(total=Sum('value'))['total'] or 0
    
    # Produtos mais vendidos no período - filtrar por empresa
    top_selling_products = (
        SaleItem.objects
        .filter(
            sale__company=request.user.company,
            sale__status='paid', 
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=end_date
        )
        .values('product__name', 'product__id', 'product__stock_quantity')
        .annotate(
            total_qty=Sum('quantity'),
            total_sales=Sum(ExpressionWrapper(
                F('price') * F('quantity'),
                output_field=DecimalField()
            ))
        )
        .order_by('-total_qty')[:10]
    )
    
    # Calcular a média de vendas diárias para estimar tempo até esgotamento do estoque
    for product in top_selling_products:
        daily_avg_sales = product['total_qty'] / days if days > 0 else 0
        if daily_avg_sales > 0 and product['product__stock_quantity'] > 0:
            days_remaining = int(product['product__stock_quantity'] / daily_avg_sales)
            product['days_remaining'] = days_remaining
        else:
            product['days_remaining'] = None
    
    context = {
        'period': period,
        'low_stock_products': low_stock_products,
        'high_value_products': high_value_products,
        'inventory_value': inventory_value,
        'top_selling_products': top_selling_products,
    }
    
    return render(request, 'dashboard/inventory_dashboard.html', context)

@login_required
def sales_dashboard(request):
    """
    View do dashboard de vendas com análise detalhada de vendas
    """
    # Obter período de filtro (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Configuração do filtro de data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Métricas de vendas - filtrar por empresa
    sales_data = Sale.objects.filter(
        company=request.user.company,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Total de vendas e receita por status
    sales_by_status = sales_data.values('status').annotate(
        count=Count('id'),
        total=Sum('total')
    )
    
    # Formatar dados para dashboard
    status_dict = {
        'paid': {'label': 'Pagas', 'count': 0, 'total': 0, 'color': '#38d6ae'},
        'pending': {'label': 'Pendentes', 'count': 0, 'total': 0, 'color': '#f59f00'},
        'cancelled': {'label': 'Canceladas', 'count': 0, 'total': 0, 'color': '#fa5252'},
    }
    
    for item in sales_by_status:
        if item['status'] in status_dict:
            status_dict[item['status']]['count'] = item['count']
            status_dict[item['status']]['total'] = float(item['total'] or 0)
    
    # Vendas por dia para o gráfico
    sales_by_day = sales_data.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        total=Sum('total')
    ).order_by('date')
    
    # Formatar para o gráfico
    sales_chart_data = []
    for item in sales_by_day:
        sales_chart_data.append({
            'date': item['date'].strftime('%d/%m'),
            'count': item['count'],
            'total': float(item['total'] or 0)
        })
    
    # Top vendedores (se aplicável)
    if hasattr(Sale, 'created_by'):
        top_sellers = sales_data.values('created_by__username').annotate(
            count=Count('id'),
            total=Sum('total')
        ).order_by('-total')[:5]
    else:
        top_sellers = []
    
    # Ticket médio
    total_sales = sales_data.filter(status='paid').count()
    total_revenue = float(sales_data.filter(status='paid').aggregate(total=Sum('total'))['total'] or 0)
    average_ticket = total_revenue / total_sales if total_sales > 0 else 0
    
    context = {
        'period': period,
        'status_dict': status_dict,
        'sales_chart_data': json.dumps(sales_chart_data),
        'top_sellers': top_sellers,
        'average_ticket': average_ticket,
    }
    
    return render(request, 'dashboard/sales_dashboard.html', context)

@login_required
def customers_dashboard(request):
    """
    View do dashboard de clientes com análise detalhada dos clientes
    """
    # Obter período de filtro (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Configuração do filtro de data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Filtrar clientes da empresa do usuário
    customers = Customer.objects.filter(company=request.user.company)
    
    # Total de clientes
    total_customers = customers.count()
    
    # Novos clientes no período
    new_customers = customers.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).count()
    
    # Clientes por nível de fidelidade
    customers_by_tier = customers.values(
        'loyalty_tier__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Dados para o gráfico de novos clientes por dia
    customer_chart_data = []
    for i in range(days):
        date = end_date - timedelta(days=days-i-1)
        
        # Contar novos clientes do dia
        day_customers = customers.filter(
            created_at__date=date
        ).count()
        
        customer_chart_data.append({
            'date': date.strftime('%d/%m'),
            'customers': day_customers
        })
    
    # Clientes mais ativos (com mais compras)
    active_customers = customers.annotate(
        total_purchases=Count('sale')
    ).order_by('-total_purchases')[:10]
    
    # Clientes de maior valor (com maior valor em compras)
    valuable_customers = customers.annotate(
        total_spent=Sum('sale__total')
    ).order_by('-total_spent')[:10]
    
    context = {
        'period': period,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'customers_by_tier': customers_by_tier,
        'customer_chart_data': json.dumps(customer_chart_data),
        'active_customers': active_customers,
        'valuable_customers': valuable_customers,
    }
    
    return render(request, 'dashboard/customers_dashboard.html', context)

@login_required
def diagnose_payment_status_issue(request, expense_id=None):
    """
    Função de diagnóstico para identificar problemas com a atualização de status de pagamento
    
    Esta função verifica e registra:
    1. O estado atual da despesa
    2. Possíveis problemas com permissões
    3. Erros na requisição
    4. Problemas com cálculos associados
    """
    # Informações de diagnóstico para registrar
    diagnostic_info = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': request.user.id,
        'user_email': request.user.email,
        'company_id': request.user.company.id if hasattr(request.user, 'company') else None,
        'expense_id': expense_id,
        'headers': dict(request.headers),
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
        'method': request.method,
        'errors': []
    }
    
    # Verificação de autenticação e permissões
    if not request.user.is_authenticated:
        diagnostic_info['errors'].append('Usuário não autenticado')
        return JsonResponse({'success': False, 'error': 'Não autorizado', 'diagnostic': diagnostic_info}, status=401)
    
    try:
        if expense_id:
            # Verificar se a despesa existe
            try:
                expense = Expense.objects.get(id=expense_id)
                diagnostic_info['expense_status'] = {
                    'exists': True,
                    'amount': float(expense.amount),
                    'is_paid': expense.is_paid,
                    'expense_company_id': expense.company.id if hasattr(expense, 'company') else None
                }
                
                # Verificar permissões
                if hasattr(expense, 'company') and hasattr(request.user, 'company'):
                    if expense.company.id != request.user.company.id:
                        diagnostic_info['errors'].append('Usuário não tem permissão para acessar esta despesa')
            except Expense.DoesNotExist:
                diagnostic_info['expense_status'] = {'exists': False}
                diagnostic_info['errors'].append(f'Despesa com ID {expense_id} não encontrada')
        
        # Verificar se há erros no banco de dados
        try:
            # Testar cálculos para identificar possíveis erros
            company = request.user.company
            total_expenses = Expense.objects.filter(company=company).aggregate(Sum('amount'))['amount__sum'] or 0
            paid_expenses = Expense.objects.filter(company=company, is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0
            
            diagnostic_info['calculations'] = {
                'total_expenses': float(total_expenses),
                'paid_expenses': float(paid_expenses)
            }
        except Exception as calc_error:
            diagnostic_info['errors'].append(f'Erro nos cálculos: {str(calc_error)}')
            
        # Verificar se há problemas com CSRF
        if request.method == 'POST' and not request.POST.get('csrfmiddlewaretoken'):
            diagnostic_info['errors'].append('Token CSRF ausente')
            
    except Exception as e:
        diagnostic_info['errors'].append(f'Erro não esperado: {str(e)}')
    
    # Adicionar sugestão de correção com base nos erros encontrados
    if diagnostic_info['errors']:
        diagnostic_info['suggestions'] = [
            'Verifique se o usuário está logado e tem permissão para esta despesa',
            'Confirme se o formato da requisição está correto (headers, CSRF token)',
            'Verifique se a despesa existe e pertence à empresa do usuário',
            'Verifique erros nos cálculos (divisão por zero, valores nulos)'
        ]
    
    # Registrar as informações de diagnóstico em log
    logger = logging.getLogger('dashboard.expenses')
    logger.info(f"Diagnóstico de atualização de pagamento: {json.dumps(diagnostic_info, default=str)}")
    
    # Retornar as informações de diagnóstico
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'diagnostic': diagnostic_info})
    else:
        messages.info(request, f"Diagnóstico concluído. Verifique o log para detalhes.")
        return redirect('dashboard:expenses')

def diagnose_payment_update_issue(request, expense_id):
    """
    Função para diagnosticar problemas na atualização do status de pagamento de despesas.
    Retorna informações detalhadas sobre o estado atual da despesa e possíveis problemas.
    """
    try:
        # Verificar se a despesa existe
        try:
            expense = Expense.objects.get(id=expense_id)
        except Expense.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Despesa com ID {expense_id} não encontrada',
                'diagnostic': {
                    'issue_type': 'not_found',
                    'solution': 'Verifique se a despesa não foi excluída recentemente'
                }
            }, status=404)
            
        # Verificar permissões do usuário
        if expense.company != request.user.company:
            return JsonResponse({
                'success': False,
                'error': 'Você não tem permissão para modificar esta despesa',
                'diagnostic': {
                    'issue_type': 'permission',
                    'solution': 'Esta despesa pertence a outra empresa'
                }
            }, status=403)
            
        # Verificar estado do banco de dados
        try:
            # Tentar uma operação simples para verificar conexão com DB
            Expense.objects.filter(id=expense_id).exists()
        except Exception as db_error:
            return JsonResponse({
                'success': False,
                'error': f'Erro de conexão com o banco de dados: {str(db_error)}',
                'diagnostic': {
                    'issue_type': 'database',
                    'solution': 'Verifique a conexão com o banco de dados ou contate o administrador'
                }
            }, status=500)
            
        # Informações sobre o estado atual da despesa
        current_state = {
            'id': expense.id,
            'description': expense.description,
            'amount': float(expense.amount),
            'is_paid': expense.is_paid,
            'due_date': expense.due_date.strftime('%Y-%m-%d') if expense.due_date else None,
            'company_id': expense.company.id,
            'company_name': expense.company.name
        }
        
        return JsonResponse({
            'success': True,
            'current_state': current_state,
            'diagnostic': {
                'issue_type': 'none',
                'solution': 'A despesa está em um estado válido e pode ser atualizada'
            }
        })
        
    except Exception as e:
        logger = logging.getLogger('dashboard.expenses')
        logger.error(
            f"ERRO ao diagnosticar despesa: ID={expense_id}, "
            f"Usuário={request.user.email}, Erro={str(e)}", 
            exc_info=True
        )
        return JsonResponse({
            'success': False,
            'error': f'Erro ao diagnosticar despesa: {str(e)}',
            'diagnostic': {
                'issue_type': 'unknown',
                'solution': 'Erro interno do servidor, contate o administrador',
                'details': traceback.format_exc()
            }
        }, status=500)

@require_http_methods(["POST"])
def toggle_expense_payment(request, expense_id):
    """Função para alternar o status de pagamento de uma despesa"""
    try:
        expense = Expense.objects.get(id=expense_id)
        
        # Verificar permissões do usuário
        if expense.company != request.user.company:
            return JsonResponse({
                'success': False, 
                'error': 'Você não tem permissão para modificar esta despesa',
                'diagnostic_url': f'/dashboard/despesas/diagnostico/{expense_id}/'
            }, status=403)
            
        # Registrar o valor anterior
        old_status = expense.is_paid
        
        # Alternar o status
        expense.is_paid = not expense.is_paid
        expense.save()
        
        # Registrar a operação em log
        logger = logging.getLogger('dashboard.expenses')
        logger.info(
            f"STATUS DE PAGAMENTO ALTERADO: Despesa ID={expense.id}, "
            f"Valor={expense.amount}, Antigo={old_status}, Novo={expense.is_paid}, "
            f"Usuário={request.user.email}, Empresa={request.user.company.name}"
        )
        
        # Recalcular totais para o dashboard
        company = request.user.company
        total_expenses = float(Expense.objects.filter(company=company).aggregate(Sum('amount'))['amount__sum'] or 0)
        paid_expenses = float(Expense.objects.filter(company=company, is_paid=True).aggregate(Sum('amount'))['amount__sum'] or 0)
        pending_expenses = total_expenses - paid_expenses
        
        # Calcular percentual de pagamento para evitar divisão por zero
        payment_percentage = 0
        if total_expenses > 0:
            payment_percentage = (paid_expenses / total_expenses) * 100
        
        # Calcular lucratividade atualizada - últimos 30 dias
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        
        # Calcular receita total
        sales_data = Sale.objects.filter(
            company=company,
            status='paid', 
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        total_revenue = float(sales_data.aggregate(total=Sum('total'))['total'] or 0)
        
        # Cálculo da lucratividade baseada no custo dos produtos
        profit_data = (
            SaleItem.objects
            .filter(
                sale__company=company,
                sale__status='paid', 
                sale__created_at__date__gte=start_date,
                sale__created_at__date__lte=end_date
            )
            .annotate(
                profit=ExpressionWrapper(
                    (F('price') - F('cost_price')) * F('quantity'),
                    output_field=DecimalField()
                )
            )
            .aggregate(total_profit=Sum('profit'))
        )
        
        total_profit = float(profit_data['total_profit'] or 0)
        
        # Calcular lucro descontando as despesas
        profit_after_expenses = total_profit - paid_expenses  # Usar apenas despesas pagas
        
        # Calcular margem de lucro
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        margin_after_expenses = (profit_after_expenses / total_revenue * 100) if total_revenue > 0 else 0
        
        return JsonResponse({
            'success': True,
            'is_paid': expense.is_paid,
            'total_expenses': total_expenses,
            'paid_expenses': paid_expenses,
            'pending_expenses': pending_expenses,
            'payment_percentage': payment_percentage,
            'total_revenue': total_revenue,
            'total_profit': total_profit,
            'profit_after_expenses': profit_after_expenses,
            'profit_margin': profit_margin,
            'margin_after_expenses': margin_after_expenses
        })
    except Expense.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Despesa não encontrada',
            'diagnostic_url': f'/dashboard/despesas/diagnostico/{expense_id}/'
        }, status=404)
    except Exception as e:
        # Registrar erro detalhado em log
        logger = logging.getLogger('dashboard.expenses')
        logger.error(
            f"ERRO ao alternar status de pagamento: Despesa ID={expense_id}, "
            f"Usuário={request.user.email}, Erro={str(e)}", 
            exc_info=True
        )
        return JsonResponse({
            'success': False, 
            'error': f'Erro ao atualizar pagamento: {str(e)}',
            'details': traceback.format_exc(),
            'diagnostic_url': f'/dashboard/despesas/diagnostico/{expense_id}/'
        }, status=500)

@login_required
def expenses_dashboard_simple(request):
    """
    View do dashboard de despesas com visualização simplificada
    """
    # Obter período de filtro (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Configuração do filtro de data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Filtrar despesas da empresa do usuário
    expenses = Expense.objects.filter(
        company=request.user.company,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Total de despesas no período
    total_expenses = float(expenses.aggregate(total=Sum('amount'))['total'] or 0)
    
    # Despesas pagas vs não pagas
    paid_expenses = float(expenses.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0)
    unpaid_expenses = float(expenses.filter(is_paid=False).aggregate(total=Sum('amount'))['total'] or 0)
    
    # Despesas por categoria
    expenses_by_category = expenses.values(
        'category__name'
    ).annotate(
        total=Sum('amount'),
        paid=Sum('amount', filter=models.Q(is_paid=True)),
        pending=Sum('amount', filter=models.Q(is_paid=False))
    ).order_by('-total')
    
    # Calcular porcentagens para o gráfico
    for item in expenses_by_category:
        item['percentage'] = (float(item['total']) / total_expenses * 100) if total_expenses > 0 else 0
        # Garantir que os valores não sejam None
        item['total'] = float(item['total'] or 0)
        item['paid'] = float(item['paid'] or 0)
        item['pending'] = float(item['pending'] or 0)
    
    # Dados para o gráfico de despesas diárias
    expense_chart_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        # Somar despesas do dia
        day_expenses = expenses.filter(date=date)
        day_total = float(day_expenses.aggregate(total=Sum('amount'))['total'] or 0)
        
        expense_chart_data.append({
            'date': date.strftime('%d/%m'),
            'total': day_total
        })
    
    # Obter todas as categorias de despesas para o formulário de adição
    categories = ExpenseCategory.objects.filter(company=request.user.company)
    
    # Calcular o lucro estimado (baseado em vendas recentes)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Obter total de vendas pagas no período
    sales_data = Sale.objects.filter(
        company=request.user.company,
        status='paid',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    total_revenue = float(sales_data.aggregate(total=Sum('total'))['total'] or 0)
    
    # Calcular lucro bruto
    profit_data = SaleItem.objects.filter(
        sale__company=request.user.company,
        sale__status='paid',
        sale__created_at__date__gte=start_date,
        sale__created_at__date__lte=end_date
    ).annotate(
        profit=ExpressionWrapper(
            (F('price') - F('cost_price')) * F('quantity'),
            output_field=DecimalField()
        )
    ).aggregate(total_profit=Sum('profit'))
    
    total_profit = float(profit_data['total_profit'] or 0)
    profit_after_expenses = total_profit - paid_expenses
    
    # Adicionar 'name' como um alias para 'category__name' para facilitar o acesso no JavaScript
    expenses_by_category_list = list(expenses_by_category.values())
    
    # Preparar dados específicos para o gráfico de categorias
    chart_labels = []
    chart_data = []
    chart_colors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#5a5c69', '#6610f2', '#6f42c1', '#fd7e14', '#20c9a6'
    ]
    
    for index, item in enumerate(expenses_by_category):
        category_name = item.get('category__name', 'Sem categoria')
        if category_name:
            chart_labels.append(category_name)
            chart_data.append(float(item['total']))
    
    # Garantir que haja pelo menos um item para evitar gráfico vazio
    if not chart_labels:
        chart_labels = ['Sem despesas']
        chart_data = [0]
    
    # Limitar as cores ao número de categorias
    chart_colors = chart_colors[:len(chart_labels)]
    
    # Dados formatados para o gráfico
    chart_data_json = {
        'labels': chart_labels,
        'values': chart_data,
        'colors': chart_colors,
        'chart_type': 'bar'  # Alterado para gráfico de barras
    }
    
    context = {
        'period': period,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'paid_expenses': paid_expenses,
        'unpaid_expenses': unpaid_expenses,
        'expenses_by_category': expenses_by_category,
        'expenses_by_category_json': json.dumps(expenses_by_category_list, cls=DjangoJSONEncoder),
        'expense_chart_data': json.dumps(expense_chart_data),
        'categories': categories,
        'expenses': expenses.order_by('-date'),  # Todas as despesas para a visualização simplificada
        'recent_expenses': expenses.order_by('-date'),  # Usado no template para lista principal
        'total_profit': profit_after_expenses,  # Lucro após despesas pagas
        
        # Dados específicos para o gráfico de categorias
        'chart_data_json': json.dumps(chart_data_json, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'dashboard/expenses_dashboard_simple.html', context)

@login_required
def expenses_dashboard(request):
    """
    View do dashboard de despesas com resumo e análise de gastos
    """
    # Obter período de filtro (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Configuração do filtro de data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Filtrar despesas da empresa do usuário
    expenses = Expense.objects.filter(
        company=request.user.company,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Total de despesas no período
    total_expenses = float(expenses.aggregate(total=Sum('amount'))['total'] or 0)
    
    # Despesas pagas vs não pagas
    paid_expenses = float(expenses.filter(is_paid=True).aggregate(total=Sum('amount'))['total'] or 0)
    unpaid_expenses = float(expenses.filter(is_paid=False).aggregate(total=Sum('amount'))['total'] or 0)
    
    # Despesas por categoria
    expenses_by_category = expenses.values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Calcular porcentagens para o gráfico
    for item in expenses_by_category:
        item['percentage'] = (float(item['total']) / total_expenses * 100) if total_expenses > 0 else 0
    
    # Dados para o gráfico de despesas diárias
    expense_chart_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        # Somar despesas do dia
        day_expenses = expenses.filter(date=date)
        day_total = float(day_expenses.aggregate(total=Sum('amount'))['total'] or 0)
        
        expense_chart_data.append({
            'date': date.strftime('%d/%m'),
            'total': day_total
        })
    
    # Obter todas as categorias de despesas para o formulário de adição
    categories = ExpenseCategory.objects.filter(company=request.user.company)
    
    context = {
        'period': period,
        'total_expenses': total_expenses,
        'paid_expenses': paid_expenses,
        'unpaid_expenses': unpaid_expenses,
        'expenses_by_category': expenses_by_category,
        'expense_chart_data': json.dumps(expense_chart_data),
        'categories': categories,
        'expenses': expenses.order_by('-date')[:20],  # Últimas 20 despesas
    }
    
    return render(request, 'dashboard/expenses_dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def add_expense(request):
    """
    Adicionar uma nova despesa
    """
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            new_category = request.POST.get('new_category', '').strip()
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            date_str = request.POST.get('date')
            is_paid = request.POST.get('is_paid') == 'true'
            is_recurring = request.POST.get('is_recurring') == 'on'
            recurrence_period = request.POST.get('recurrence_period', '')
            
            # Validar campos obrigatórios
            if not description or not amount or not date_str:
                messages.error(request, 'Descrição, valor e data são obrigatórios.')
                return redirect('dashboard:expenses')
            
            # Verificar categoria ou criar nova
            if category_id == 'nova' and new_category:
                # Criar nova categoria
                category, created = ExpenseCategory.objects.get_or_create(
                    company=request.user.company,
                    name=new_category
                )
            elif category_id:
                # Obter categoria existente
                try:
                    category = ExpenseCategory.objects.get(id=category_id, company=request.user.company)
                except ExpenseCategory.DoesNotExist:
                    messages.error(request, 'Categoria não encontrada.')
                    return redirect('dashboard:expenses')
            else:
                messages.error(request, 'Selecione ou crie uma categoria.')
                return redirect('dashboard:expenses')
            
            # Processar a data
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Formato de data inválido.')
                return redirect('dashboard:expenses')
            
            # Processar o valor
            try:
                amount = float(amount.replace(',', '.'))
            except ValueError:
                messages.error(request, 'Valor inválido.')
                return redirect('dashboard:expenses')
            
            # Criar a despesa
            Expense.objects.create(
                company=request.user.company,
                category=category,
                description=description,
                amount=amount,
                date=expense_date,
                is_paid=is_paid,
                is_recurring=is_recurring,
                recurrence_period=recurrence_period if is_recurring else ''
            )
            
            messages.success(request, 'Despesa adicionada com sucesso!')
            return redirect('dashboard:expenses')
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar despesa: {str(e)}')
            return redirect('dashboard:expenses')
    
    # Para requisições GET, redirecionar para o dashboard de despesas
    return redirect('dashboard:expenses')


@login_required
@require_http_methods(["GET", "POST"])
def edit_expense(request, expense_id):
    """
    Editar uma despesa existente
    """
    # Obter a despesa e verificar permissões
    expense = get_object_or_404(Expense, id=expense_id, company=request.user.company)
    
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            date_str = request.POST.get('date')
            is_paid = request.POST.get('is_paid') == 'true'
            is_recurring = request.POST.get('is_recurring') == 'on'
            recurrence_period = request.POST.get('recurrence_period', '')
            
            # Validar campos obrigatórios
            if not all([category_id, description, amount, date_str]):
                messages.error(request, 'Todos os campos são obrigatórios.')
                return redirect('dashboard:expenses')
            
            # Processar a data
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Formato de data inválido.')
                return redirect('dashboard:expenses')
            
            # Processar o valor
            try:
                amount = float(amount.replace(',', '.'))
            except ValueError:
                messages.error(request, 'Valor inválido.')
                return redirect('dashboard:expenses')
            
            # Obter a categoria
            try:
                category = ExpenseCategory.objects.get(id=category_id, company=request.user.company)
            except ExpenseCategory.DoesNotExist:
                messages.error(request, 'Categoria não encontrada.')
                return redirect('dashboard:expenses')
            
            # Atualizar a despesa
            expense.category = category
            expense.description = description
            expense.amount = amount
            expense.date = expense_date
            expense.is_paid = is_paid
            expense.is_recurring = is_recurring
            expense.recurrence_period = recurrence_period if is_recurring else ''
            expense.save()
            
            messages.success(request, 'Despesa atualizada com sucesso!')
            return redirect('dashboard:expenses')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar despesa: {str(e)}')
            return redirect('dashboard:expenses')
    
    # Para requisições GET, carregar o formulário com os dados da despesa
    categories = ExpenseCategory.objects.filter(company=request.user.company)
    
    context = {
        'expense': expense,
        'categories': categories,
    }
    
    return render(request, 'dashboard/edit_expense.html', context)


@login_required
def delete_expense(request, expense_id):
    """
    Excluir uma despesa
    """
    # Obter a despesa e verificar permissões
    expense = get_object_or_404(Expense, id=expense_id, company=request.user.company)
    
    try:
        expense.delete()
        messages.success(request, 'Despesa excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir despesa: {str(e)}')
    
    return redirect('dashboard:expenses')


@login_required
@require_http_methods(["GET", "POST"])
def add_expense_category(request):
    """
    Adicionar uma nova categoria de despesa
    """
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            
            # Validar campos obrigatórios
            if not name:
                messages.error(request, 'O nome da categoria é obrigatório.')
                return redirect('dashboard:expenses')
            
            # Verificar se já existe uma categoria com o mesmo nome
            if ExpenseCategory.objects.filter(name=name, company=request.user.company).exists():
                messages.error(request, 'Já existe uma categoria com este nome.')
                return redirect('dashboard:expenses')
            
            # Criar a categoria
            ExpenseCategory.objects.create(
                company=request.user.company,
                name=name
            )
            
            messages.success(request, 'Categoria de despesa adicionada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar categoria: {str(e)}')
    
    return redirect('dashboard:expenses')


@login_required
@require_http_methods(["GET", "POST"])
def edit_expense_category(request, category_id):
    """
    Editar uma categoria de despesa existente
    """
    # Obter a categoria e verificar permissões
    category = get_object_or_404(ExpenseCategory, id=category_id, company=request.user.company)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            
            # Validar campos obrigatórios
            if not name:
                messages.error(request, 'O nome da categoria é obrigatório.')
                return redirect('dashboard:expenses')
            
            # Verificar se já existe outra categoria com o mesmo nome
            if ExpenseCategory.objects.filter(name=name, company=request.user.company).exclude(id=category_id).exists():
                messages.error(request, 'Já existe outra categoria com este nome.')
                return redirect('dashboard:expenses')
            
            # Atualizar a categoria
            category.name = name
            category.save()
            
            messages.success(request, 'Categoria de despesa atualizada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
    
    # Para requisições GET, carregar o formulário com os dados da categoria
    context = {
        'category': category,
    }
    
    return render(request, 'dashboard/edit_expense_category.html', context)


@login_required
def delete_expense_category(request, category_id):
    """
    Excluir uma categoria de despesa
    """
    # Obter a categoria e verificar permissões
    category = get_object_or_404(ExpenseCategory, id=category_id, company=request.user.company)
    
    try:
        # Verificar se existem despesas associadas a esta categoria
        if Expense.objects.filter(category=category).exists():
            messages.error(request, 'Não é possível excluir esta categoria pois existem despesas associadas a ela.')
            return redirect('dashboard:expenses')
        
        category.delete()
        messages.success(request, 'Categoria de despesa excluída com sucesso!')
        
    except Exception as e:
        messages.error(request, f'Erro ao excluir categoria: {str(e)}')
    
    return redirect('dashboard:expenses')


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["GET", "POST"])
def add_saas_expense(request):
    """
    Adicionar uma despesa da plataforma SaaS (apenas para administradores)
    """
    if request.method == 'POST':
        try:
            company_id = request.POST.get('company')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            date_str = request.POST.get('date')
            is_paid = request.POST.get('is_paid', '') == 'on'
            
            from core.models import Company
            
            # Validar campos obrigatórios
            if not all([company_id, description, amount, date_str]):
                messages.error(request, 'Todos os campos são obrigatórios.')
                return redirect('admin:dashboard_expense_changelist')
            
            # Processar a data
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Formato de data inválido.')
                return redirect('admin:dashboard_expense_changelist')
            
            # Processar o valor
            try:
                amount = float(amount.replace(',', '.'))
            except ValueError:
                messages.error(request, 'Valor inválido.')
                return redirect('admin:dashboard_expense_changelist')
            
            # Obter a empresa
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                messages.error(request, 'Empresa não encontrada.')
                return redirect('admin:dashboard_expense_changelist')
            
            # Obter ou criar categoria SaaS
            saas_category, created = ExpenseCategory.objects.get_or_create(
                company=company,
                name='Plataforma SaaS'
            )
            
            # Criar a despesa
            Expense.objects.create(
                company=company,
                category=saas_category,
                description=description,
                amount=amount,
                date=expense_date,
                is_paid=is_paid
            )
            
            messages.success(request, 'Despesa SaaS adicionada com sucesso!')
            return redirect('admin:dashboard_expense_changelist')
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar despesa SaaS: {str(e)}')
            return redirect('admin:dashboard_expense_changelist')
    
    # Para requisições GET, exibir o formulário
    from core.models import Company
    companies = Company.objects.all()
    
    context = {
        'companies': companies,
    }
    
    return render(request, 'dashboard/add_saas_expense.html', context)
