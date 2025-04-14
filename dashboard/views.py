from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from .models import ExpenseCategory, Expense
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
            sale__status='paid', 
            sale__created_at__date__gte=start_date,
            sale__created_at__date__lte=end_date
        )
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
    View para dashboard de estoque
    """
    # Produtos com estoque baixo - filtrar por empresa
    low_stock_products = Product.objects.filter(
        company=request.user.company,
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')
    
    # Valor total do estoque - filtrar por empresa
    stock_value = Product.objects.filter(
        company=request.user.company
    ).aggregate(
        total_value=Sum(F('stock_quantity') * F('cost'))
    )['total_value'] or 0
    
    # Produtos por categoria - filtrar por empresa
    products_by_category = (
        Product.objects
        .filter(company=request.user.company)
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
    
    # Vendas por mês - filtrar por empresa
    monthly_sales = (
        Sale.objects
        .filter(
            company=request.user.company,
            status='paid', 
            created_at__date__gte=start_date
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('month')
    )
    
    # Vendas por método de pagamento - filtrar por empresa
    sales_by_payment = (
        Sale.objects
        .filter(
            company=request.user.company,
            status='paid', 
            created_at__date__gte=start_date
        )
        .values('payment_method__name')
        .annotate(total=Sum('total'), count=Count('id'))
        .order_by('-total')
    )
    
    # Ticket médio - filtrar por empresa
    avg_ticket = (
        Sale.objects
        .filter(
            company=request.user.company,
            status='paid', 
            created_at__date__gte=start_date
        )
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
    # Clientes que mais compram - filtrar por empresa
    top_customers = (
        Sale.objects
        .filter(
            company=request.user.company,
            status='paid'
        )
        .values('customer__name')
        .annotate(total_spent=Sum('total'), order_count=Count('id'))
        .filter(customer__isnull=False)
        .order_by('-total_spent')[:10]
    )
    
    # Clientes por cidade - filtrar por empresa
    customers_by_city = (
        Customer.objects
        .filter(company=request.user.company)
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

@login_required
def expenses_dashboard(request):
    """
    View para dashboard de gerenciamento de despesas
    """
    # Obter dados das despesas do banco de dados
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Buscar categorias de despesas da empresa
    categories = ExpenseCategory.objects.filter(company=request.user.company)
    
    # Se não existirem categorias, criar as padrões
    if not categories.exists():
        default_categories = [
            {'name': 'Aluguel e Taxas', 'icon': 'fa-building', 'color': 'primary'},
            {'name': 'Funcionários', 'icon': 'fa-users', 'color': 'info'},
            {'name': 'Compra de Estoque', 'icon': 'fa-boxes', 'color': 'warning'},
            {'name': 'Operacionais', 'icon': 'fa-bolt', 'color': 'success'},
        ]
        
        for cat in default_categories:
            ExpenseCategory.objects.create(
                name=cat['name'],
                icon=cat['icon'],
                color=cat['color'],
                company=request.user.company
            )
        
        # Recarregar categorias
        categories = ExpenseCategory.objects.filter(company=request.user.company)
    
    # Filtrar despesas do mês atual
    expenses = Expense.objects.filter(
        company=request.user.company,
        date__month=current_month,
        date__year=current_year
    )
    
    # Calcular total de despesas
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Calcular valores e percentuais por categoria
    expenses_categories = []
    for category in categories:
        category_expenses = expenses.filter(category=category)
        category_total = category_expenses.aggregate(total=Sum('amount'))['total'] or 0
        percentage = (category_total / total_expenses * 100) if total_expenses > 0 else 0
        
        expenses_categories.append({
            'id': category.id,
            'name': category.name,
            'amount': category_total,
            'percentage': round(percentage, 1),
            'icon': category.icon,
            'color': category.color,
            'expenses_count': category_expenses.count()
        })
    
    # Formato do mês e ano para exibição
    month_year = timezone.now().strftime('%B %Y')
    
    # Buscar receitas do mês atual
    total_revenue = Sale.objects.filter(
        company=request.user.company,
        status='paid',
        created_at__month=current_month,
        created_at__year=current_year
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Calcular lucro total (receitas - despesas)
    total_profit = float(total_revenue) - float(total_expenses)
    profit_margin = (total_profit / float(total_revenue) * 100) if total_revenue > 0 else 0
    
    # Adicionar o valor absoluto da margem para usar quando negativa
    profit_margin_abs = abs(profit_margin)
    
    context = {
        'expenses_categories': expenses_categories,
        'total_expenses': total_expenses,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'profit_margin_abs': profit_margin_abs,
        'month_year': month_year,
        'expenses': expenses,
    }
    
    return render(request, 'dashboard/expenses_dashboard.html', context)

@login_required
def add_expense(request):
    """
    View para adicionar uma nova despesa
    """
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            
            # Certifica que o valor é processado corretamente
            if amount:
                # Verificar se é entrada direta de números ou formato brasileiro
                # O frontend pode enviar 1500.00 (formato backend) ou 1.500,00 (formato usuário)
                if ',' in amount:
                    # Formato brasileiro: primeiro remover pontos, depois substituir vírgula
                    amount = amount.replace('.', '').replace(',', '.')
                
                amount = float(amount)
            
            date = request.POST.get('date')
            is_paid = 'is_paid' in request.POST
            is_recurring = 'is_recurring' in request.POST
            
            recurrence_period = request.POST.get('recurrence_period')
            
            if not category_id:
                messages.error(request, "Categoria é obrigatória")
                return redirect('dashboard:expenses')
            
            category = ExpenseCategory.objects.get(id=category_id, company=request.user.company)
            date = timezone.datetime.strptime(date, '%Y-%m-%d').date() if date else timezone.now().date()
            
            expense = Expense.objects.create(
                category=category,
                amount=amount,
                description=description,
                date=date,
                is_recurring=is_recurring,
                recurrence_period=recurrence_period if is_recurring else '',
                company=request.user.company
            )
            
            messages.success(request, 'Despesa adicionada com sucesso!')
            return redirect('dashboard:expenses')
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar despesa: {str(e)}')
    
    return redirect('dashboard:expenses')

@login_required
def edit_expense(request, expense_id):
    """
    View para editar uma despesa existente
    """
    expense = get_object_or_404(Expense, id=expense_id, company=request.user.company)
    
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            description = request.POST.get('description')
            amount = request.POST.get('amount')
            
            # Certifica que o valor é processado corretamente
            if amount:
                # Verificar se é entrada direta de números ou formato brasileiro
                # O frontend pode enviar 1500.00 (formato backend) ou 1.500,00 (formato usuário)
                if ',' in amount:
                    # Formato brasileiro: primeiro remover pontos, depois substituir vírgula
                    amount = amount.replace('.', '').replace(',', '.')
                
                amount = float(amount)
            
            date = request.POST.get('date')
            is_paid = 'is_paid' in request.POST
            is_recurring = 'is_recurring' in request.POST
            
            recurrence_period = request.POST.get('recurrence_period')
            
            expense.category = ExpenseCategory.objects.get(id=category_id, company=request.user.company)
            expense.amount = amount
            expense.description = description
            
            if date:
                expense.date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
                
            expense.is_recurring = is_recurring
            expense.recurrence_period = recurrence_period if is_recurring else ''
            expense.save()
            
            messages.success(request, 'Despesa atualizada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar despesa: {str(e)}')
    
    # Para chamadas AJAX que solicitam informações da despesa
    elif request.method == 'GET' and 'format' in request.GET and request.GET['format'] == 'json':
        data = {
            'id': expense.id,
            'category_id': expense.category.id,
            'description': expense.description,
            'amount': float(expense.amount),
            'date': expense.date.strftime('%Y-%m-%d'),
            'is_recurring': expense.is_recurring,
            'recurrence_period': expense.recurrence_period
        }
        return JsonResponse(data)
    
    return redirect('dashboard:expenses')

@login_required
def delete_expense(request, expense_id):
    """
    View para excluir uma despesa
    """
    expense = get_object_or_404(Expense, id=expense_id, company=request.user.company)
    
    try:
        expense.delete()
        messages.success(request, 'Despesa excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir despesa: {str(e)}')
    
    return redirect('dashboard:expenses')

@login_required
def add_expense_category(request):
    """
    View para adicionar uma nova categoria de despesa
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', 'fa-building')
        color = request.POST.get('color', 'primary')
        
        if not name:
            messages.error(request, 'O nome da categoria é obrigatório.')
            return redirect('dashboard:expenses')
        
        try:
            ExpenseCategory.objects.create(
                name=name,
                icon=icon,
                color=color,
                company=request.user.company
            )
            
            messages.success(request, 'Categoria de despesa adicionada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao adicionar categoria: {str(e)}')
    
    return redirect('dashboard:expenses')

@login_required
def edit_expense_category(request, category_id):
    """
    View para editar uma categoria de despesa existente
    """
    category = get_object_or_404(ExpenseCategory, id=category_id, company=request.user.company)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', 'fa-building')
        color = request.POST.get('color', 'primary')
        
        if not name:
            messages.error(request, 'O nome da categoria é obrigatório.')
            return redirect('dashboard:expenses')
        
        try:
            category.name = name
            category.icon = icon
            category.color = color
            category.save()
            
            messages.success(request, 'Categoria de despesa atualizada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar categoria: {str(e)}')
    
    return redirect('dashboard:expenses')

@login_required
def delete_expense_category(request, category_id):
    """
    View para excluir uma categoria de despesa
    """
    category = get_object_or_404(ExpenseCategory, id=category_id, company=request.user.company)
    
    # Verificar se existem despesas nesta categoria
    if Expense.objects.filter(category=category).exists():
        messages.error(request, 'Não é possível excluir uma categoria que possui despesas.')
        return redirect('dashboard:expenses')
    
    try:
        category.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir categoria: {str(e)}')
    
    return redirect('dashboard:expenses')
