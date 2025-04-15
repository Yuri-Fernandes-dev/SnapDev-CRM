from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Company, Subscription
from django.db.models import Sum, Count, Avg, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta
from sales.models import Sale, SaleItem
from products.models import Product
from customers.models import Customer
from django import forms

class CompanyRegistrationForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'email', 'phone']

class ExtendedUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

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
    View para exibir os planos e preços
    """
    return render(request, 'core/pricing.html')

def register(request):
    """
    View para registro de usuário e empresa
    """
    if request.method == 'POST':
        user_form = ExtendedUserCreationForm(request.POST)
        company_form = CompanyRegistrationForm(request.POST)
        
        if user_form.is_valid() and company_form.is_valid():
            # Criar usuário
            user = user_form.save()
            user.email = user_form.cleaned_data['email']
            user.save()
            
            # Criar empresa
            company = company_form.save(commit=False)
            company.owner = user
            company.save()
            
            # Criar assinatura básica
            subscription = Subscription.objects.create(
                company=company,
                plan='basic',
                status='active',
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timedelta(days=30),
                price=0  # Trial gratuito de 30 dias
            )
            
            # Fazer login
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Você tem 30 dias gratuitos para testar o sistema.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        user_form = ExtendedUserCreationForm()
        company_form = CompanyRegistrationForm()
    
    return render(request, 'core/register.html', {
        'user_form': user_form,
        'company_form': company_form
    })

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
    # Obter o período selecionado do request
    period = request.GET.get('period', '30')
    period = int(period)
    
    today = timezone.now().date()
    period_start = today - timedelta(days=period)
    
    # Vendas do período - garantir que todos os itens sejam da empresa
    sales = Sale.objects.filter(
        company=request.user.company,
        created_at__date__gte=period_start,
        created_at__date__lte=today,
        status='paid',
        items__product__company=request.user.company  # Garantir que os itens sejam da empresa
    ).distinct().select_related('customer', 'payment_method')
    
    # Cálculos gerais
    total_sales = sales.count()
    
    # Calcular receita total apenas dos itens da empresa
    sale_items = SaleItem.objects.filter(
        sale__in=sales,
        product__company=request.user.company
    ).select_related('product', 'sale')
    
    total_revenue = sum(item.subtotal for item in sale_items)
    total_cost = sum(item.quantity * item.product.cost for item in sale_items)
    
    total_profit = float(total_revenue) - float(total_cost)
    profit_margin = (total_profit / float(total_revenue) * 100) if total_revenue > 0 else 0
    average_ticket = float(total_revenue) / total_sales if total_sales > 0 else 0
    
    # Dados para o gráfico de evolução
    dates = []
    sales_data = []
    revenue_data = []
    
    # Gerar datas em ordem crescente
    for i in range(period - 1, -1, -1):
        date = today - timedelta(days=i)
        dates.append(date.strftime('%d/%m'))
        
        # Buscar vendas e itens do dia
        daily_items = SaleItem.objects.filter(
            sale__company=request.user.company,
            sale__created_at__date=date,
            sale__status='paid',
            product__company=request.user.company
        )
        
        # Contar vendas únicas e somar receita
        daily_sales = daily_items.values('sale').distinct().count()
        daily_revenue = sum(item.subtotal for item in daily_items)
        
        sales_data.append(daily_sales)
        revenue_data.append(float(daily_revenue))
    
    # Preparar dados do gráfico
    chart_data = {
        'labels': dates,
        'revenue': revenue_data,
        'sales': sales_data
    }
    
    # Top produtos - usando os itens já filtrados
    product_sales = {}
    for item in sale_items:
        if item.product_id not in product_sales:
            product_sales[item.product_id] = {
                'product__name': item.product.name,
                'product__id': item.product_id,
                'product__price': float(item.product.price),
                'total_qty': 0,
                'total_sales': 0
            }
        product_sales[item.product_id]['total_qty'] += item.quantity
        product_sales[item.product_id]['total_sales'] += float(item.subtotal)
    
    # Converter para lista e ordenar
    top_products = sorted(
        product_sales.values(),
        key=lambda x: x['total_sales'],
        reverse=True
    )[:5]
    
    # Calcular percentuais
    total_product_sales = sum(p['total_sales'] for p in top_products)
    for product in top_products:
        product['percentage'] = (product['total_sales'] / total_product_sales * 100) if total_product_sales > 0 else 0
    
    # Produtos com baixo estoque
    low_stock_products = Product.objects.filter(
        company=request.user.company,
        is_active=True,
        stock_quantity__lte=F('stock_alert_level')
    ).order_by('stock_quantity')[:5]
    
    # Clientes recentes
    recent_customers = Customer.objects.filter(
        company=request.user.company
    ).order_by('-created_at')[:5]
    
    context = {
        'period': period,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'average_ticket': average_ticket,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'chart_data': chart_data,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'recent_customers': recent_customers,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def subscription_plans(request):
    """
    View para exibir os planos de assinatura
    """
    plans = [
        {
            'name': 'Básico',
            'price': 49.90,
            'features': [
                'Até 100 produtos',
                'Até 500 vendas por mês',
                'Relatórios básicos',
                'Suporte por email'
            ]
        },
        {
            'name': 'Padrão',
            'price': 99.90,
            'features': [
                'Até 500 produtos',
                'Vendas ilimitadas',
                'Relatórios avançados',
                'Suporte prioritário',
                'Sistema de fidelidade'
            ]
        },
        {
            'name': 'Premium',
            'price': 199.90,
            'features': [
                'Produtos ilimitados',
                'Vendas ilimitadas',
                'Relatórios personalizados',
                'Suporte 24/7',
                'Sistema de fidelidade',
                'API de integração',
                'Multi-usuários'
            ]
        }
    ]
    
    return render(request, 'core/subscription_plans.html', {'plans': plans})

@login_required
def update_subscription(request, plan):
    """
    View para atualizar a assinatura
    """
    if plan not in ['basic', 'standard', 'premium']:
        messages.error(request, 'Plano inválido.')
        return redirect('subscription_plans')
    
    company = request.company
    subscription = company.subscription
    
    # Aqui você implementaria a integração com o gateway de pagamento
    # Por enquanto, vamos apenas atualizar o plano
    subscription.plan = plan
    subscription.status = 'active'
    subscription.start_date = timezone.now().date()
    subscription.end_date = timezone.now().date() + timedelta(days=30)
    
    if plan == 'basic':
        subscription.price = 49.90
    elif plan == 'standard':
        subscription.price = 99.90
    else:
        subscription.price = 199.90
    
    subscription.save()
    messages.success(request, f'Assinatura atualizada para o plano {subscription.get_plan_display()}!')
    return redirect('dashboard')

@login_required
def subscription(request):
    """
    View para mostrar detalhes da assinatura atual
    """
    # Obter a assinatura atual do usuário
    subscription = Subscription.objects.filter(
        company=request.user.company,
        status='active'
    ).first()
    
    # Definir detalhes dos planos disponíveis
    plans = {
        'basic': {
            'name': 'Básico',
            'price': 49.90,
            'features': [
                'Acesso ao sistema básico',
                'Até 100 produtos cadastrados',
                'Até 500 vendas por mês',
                'Relatórios básicos',
                'Suporte por email'
            ]
        },
        'standard': {
            'name': 'Padrão',
            'price': 99.90,
            'features': [
                'Tudo do plano Básico',
                'Até 500 produtos cadastrados',
                'Vendas ilimitadas',
                'Relatórios avançados',
                'Suporte prioritário'
            ]
        },
        'premium': {
            'name': 'Premium',
            'price': 199.90,
            'features': [
                'Tudo do plano Padrão',
                'Produtos ilimitados',
                'Vendas ilimitadas',
                'Múltiplos usuários',
                'Integrações com outros sistemas',
                'Suporte 24/7'
            ]
        }
    }
    
    context = {
        'subscription': subscription,
        'plans': plans,
        'current_plan': plans.get(subscription.plan if subscription else 'basic')
    }
    
    return render(request, 'core/subscription.html', context)

@login_required
def support(request):
    """
    View para a página de suporte ao usuário
    """
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Aqui você pode adicionar lógica para enviar o e-mail ou salvar a mensagem no banco de dados
        # Por enquanto, apenas mostramos uma mensagem de sucesso
        
        messages.success(request, 'Sua mensagem foi enviada com sucesso! Em breve entraremos em contato.')
        return redirect('support')
    
    return render(request, 'core/support.html')
