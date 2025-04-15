from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField
from django.core.exceptions import PermissionDenied
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib import messages
from decimal import Decimal
from .models import ExpenseCategory, Expense
from core.models import Subscription, Company
import datetime
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.contrib import messages
from decimal import Decimal
from .models import ExpenseCategory, Expense
from core.models import Subscription
import datetime

# Restringir acesso ao Django Admin apenas para superusuários (admin)
def restrict_admin(request, extra_context=None):
    # Permitir acesso à página de login
    if not request.path.startswith('/admin/login/'):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise PermissionDenied()
    return admin.site.__class__.login(admin.site, request, extra_context)

admin.site.login = restrict_admin

# Adicionar configurações do Jazzmin
from saas_crm import settings

# Administração das Despesas da Plataforma SaaS
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'company', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'company', 'is_paid', 'is_recurring')
    list_filter = ('is_paid', 'is_recurring', 'date', 'category', 'company', 'company__name')
    search_fields = ('description', 'category__name')
    ordering = ('-date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('category', 'amount', 'description', 'date')
        }),
        ('Status', {
            'fields': ('is_paid', 'is_recurring', 'recurrence_period')
        }),
        ('Empresa', {
            'fields': ('company',)
        }),
        ('Informações do Sistema', {
            'fields': ('created_at', 'updated_at')
        }),
    )

# Adicionando a função de dashboard administrativo personalizado
def saas_dashboard_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    # Obter período selecionado (mês e ano) dos parâmetros GET ou usar o atual
    today = datetime.date.today()
    
    try:
        selected_month = int(request.GET.get('month', today.month))
        selected_year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        selected_month = today.month
        selected_year = today.year
    
    # Garantir que o mês seja válido (entre 1 e 12)
    if selected_month < 1 or selected_month > 12:
        selected_month = today.month
    
    # Lista de anos disponíveis (do ano de fundação até o atual)
    start_year = 2020  # Ano de fundação do sistema, ajuste conforme necessário
    available_years = list(range(start_year, today.year + 1))
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Calculate user growth over time
    current_period_start = datetime.date(selected_year, selected_month, 1)
    
    # Determinar o último dia do mês selecionado
    if selected_month == 12:
        next_month = 1
        next_year = selected_year + 1
    else:
        next_month = selected_month + 1
        next_year = selected_year
    
    current_period_end = datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)
    
    # Se for o mês atual, usar hoje como data final
    if selected_month == today.month and selected_year == today.year:
        current_period_end = today
    
    # Períodos anteriores para comparação
    last_week = today - datetime.timedelta(days=7)
    last_month = today - datetime.timedelta(days=30)
    
    new_users_week = User.objects.filter(date_joined__gte=last_week).count()
    new_users_month = User.objects.filter(date_joined__gte=current_period_start, 
                                         date_joined__lte=current_period_end).count()
    
    # Calculate conversion rate (users with subscriptions)
    companies_with_subscriptions = Subscription.objects.filter(
        status='active'
    ).values('company').distinct().count()
    
    conversion_rate = (companies_with_subscriptions / total_users) * 100 if total_users > 0 else 0
    
    # Filtrar por mês e ano selecionados
    # Primeiro, verificamos as despesas diretas com company=None
    direct_expenses = Expense.objects.filter(
        company__isnull=True,
        date__month=selected_month,
        date__year=selected_year
    ).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    # Verificar também despesas da empresa "Sistema"
    system_company = Company.objects.filter(name="Sistema").first()
    system_expenses = Decimal('0.00')
    if system_company:
        system_expenses = Expense.objects.filter(
            company=system_company,
            date__month=selected_month,
            date__year=selected_year
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
    
    total_expenses = direct_expenses + system_expenses
    
    # Adicionar log para depuração
    print(f"DEBUG - Despesas: Diretas={direct_expenses}, Sistema={system_expenses}, Total={total_expenses}")
    print(f"DEBUG - Filtros: Mês={selected_month}, Ano={selected_year}")
    
    # Listar todas as despesas para debug
    all_expenses = Expense.objects.all().order_by('-date')[:10]  # últimas 10 despesas
    print("DEBUG - Últimas despesas cadastradas:")
    for exp in all_expenses:
        print(f"  ID: {exp.id}, Data: {exp.date}, Valor: {exp.amount}, Empresa: {exp.company}, Categoria: {exp.category.name}")
    
    # Adicionar despesas recorrentes
    # Buscar despesas recorrentes sem empresa
    recurring_expenses_direct = Expense.objects.filter(
        company__isnull=True,
        is_recurring=True
    )
    
    # Buscar despesas recorrentes da empresa Sistema
    recurring_expenses_system = Expense.objects.filter(
        company=system_company,
        is_recurring=True
    ) if system_company else []
    
    # Combinando as duas consultas
    recurring_expenses = list(recurring_expenses_direct) + list(recurring_expenses_system)
    
    # Para cada despesa recorrente, verificar se ela se aplica ao período selecionado
    for expense in recurring_expenses:
        # Skip recurring expenses that are already counted in the current month
        if expense.date.month == selected_month and expense.date.year == selected_year:
            print(f"DEBUG - Pulando despesa recorrente que já foi contada: ID={expense.id}, Valor={expense.amount}")
            continue
            
        if expense.date.month <= selected_month and expense.date.year <= selected_year:
            # Verificar se a recorrência se aplica neste mês
            if expense.recurrence_period == 'monthly':
                # Despesa mensal, sempre conta
                total_expenses += expense.amount
                print(f"DEBUG - Despesa recorrente mensal aplicada: ID={expense.id}, Valor={expense.amount}")
            elif expense.recurrence_period == 'quarterly' and (selected_month - expense.date.month) % 3 == 0:
                # Despesa trimestral, conta a cada 3 meses
                total_expenses += expense.amount
                print(f"DEBUG - Despesa recorrente trimestral aplicada: ID={expense.id}, Valor={expense.amount}")
            elif expense.recurrence_period == 'semiannual' and (selected_month - expense.date.month) % 6 == 0:
                # Despesa semestral, conta a cada 6 meses
                total_expenses += expense.amount
                print(f"DEBUG - Despesa recorrente semestral aplicada: ID={expense.id}, Valor={expense.amount}")
            elif expense.recurrence_period == 'annual' and selected_month == expense.date.month:
                # Despesa anual, conta apenas no mesmo mês de criação
                total_expenses += expense.amount
                print(f"DEBUG - Despesa recorrente anual aplicada: ID={expense.id}, Valor={expense.amount}")
    
    # Get expense categories for the SaaS platform
    expense_categories = ExpenseCategory.objects.filter(company__isnull=True)
    if not expense_categories.exists():
        # Se não houver categorias sem empresa, buscar categorias da empresa "Sistema"
        system_company = Company.objects.filter(name="Sistema").first()
        if system_company:
            expense_categories = ExpenseCategory.objects.filter(company=system_company)
    
    # Calculate expenses by category for the platform
    expenses_by_category = []
    categories_totals = {}  # Store category totals to avoid double counting
    
    # First calculate regular expenses by category
    for category in expense_categories:
        # Primeiro verificamos despesas sem empresa
        direct_category_total = Expense.objects.filter(
            company__isnull=True,
            category=category,
            date__month=selected_month,
            date__year=selected_year
        ).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Também verificamos despesas da empresa Sistema
        system_category_total = Decimal('0.00')
        if system_company:
            system_category_total = Expense.objects.filter(
                company=system_company,
                category=category,
                date__month=selected_month,
                date__year=selected_year
            ).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
        
        # Somamos os dois totais
        category_total = direct_category_total + system_category_total
        categories_totals[category.id] = category_total
    
    # Now add recurring expenses by category, avoiding double-counting
    for expense in recurring_expenses:
        # Skip recurring expenses that are already counted in the current month
        if expense.date.month == selected_month and expense.date.year == selected_year:
            continue
            
        if expense.date.month <= selected_month and expense.date.year <= selected_year:
            # Apply only if recurrence pattern matches
            should_apply = False
            
            if expense.recurrence_period == 'monthly':
                should_apply = True
            elif expense.recurrence_period == 'quarterly' and (selected_month - expense.date.month) % 3 == 0:
                should_apply = True
            elif expense.recurrence_period == 'semiannual' and (selected_month - expense.date.month) % 6 == 0:
                should_apply = True
            elif expense.recurrence_period == 'annual' and selected_month == expense.date.month:
                should_apply = True
                
            if should_apply:
                category_id = expense.category.id
                if category_id in categories_totals:
                    categories_totals[category_id] += expense.amount
                else:
                    categories_totals[category_id] = expense.amount
    
    # Finally, build the expenses_by_category list for display
    for category in expense_categories:
        category_total = categories_totals.get(category.id, Decimal('0.00'))
        
        if category_total > 0:
            expenses_by_category.append({
                'category': category.name,
                'icon': category.icon,
                'amount': category_total,
                'percentage': (category_total / total_expenses) * 100 if total_expenses > 0 else 0
            })
            print(f"DEBUG - Categoria {category.name}: Total={category_total}")
    
    # Calculate revenue (from subscription payments)
    total_revenue = Subscription.objects.filter(
        status='active'
    ).aggregate(
        total=Sum('price')
    )['total'] or Decimal('0.00')
    
    # Calculate profit
    profit = total_revenue - total_expenses
    
    # Calculate profit margin
    profit_margin = (profit / total_revenue) * 100 if total_revenue > 0 else 0
    
    # Contagem das assinaturas por tipo de plano
    basic_count = Subscription.objects.filter(status='active', plan='basic').count()
    standard_count = Subscription.objects.filter(status='active', plan='standard').count()
    premium_count = Subscription.objects.filter(status='active', plan='premium').count()
    total_subscribers = basic_count + standard_count + premium_count
    
    # Cálculo da receita detalhada por plano
    from saas_crm.settings import SUBSCRIPTION_PLANS
    
    basic_price = SUBSCRIPTION_PLANS['basic']['price']
    standard_price = SUBSCRIPTION_PLANS['standard']['price'] 
    premium_price = SUBSCRIPTION_PLANS['premium']['price']
    
    basic_revenue = basic_count * Decimal(str(basic_price))
    standard_revenue = standard_count * Decimal(str(standard_price))
    premium_revenue = premium_count * Decimal(str(premium_price))
    
    # Adicionar informações detalhadas ao log para debugging
    print(f"DEBUG: Assinaturas Básicas: {basic_count} x R${basic_price} = R${basic_revenue}")
    print(f"DEBUG: Assinaturas Padrão: {standard_count} x R${standard_price} = R${standard_revenue}")
    print(f"DEBUG: Assinaturas Premium: {premium_count} x R${premium_price} = R${premium_revenue}")
    print(f"DEBUG: Receita Total: R${total_revenue}")
    print(f"DEBUG: Despesas Totais: R${total_expenses}")
    print(f"DEBUG: Lucro: R${profit}")
    
    context = {
        'title': 'SaaS Dashboard',
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'new_users_week': new_users_week,
        'new_users_month': new_users_month,
        'users_with_subscriptions': companies_with_subscriptions,
        'conversion_rate': conversion_rate,
        'total_expenses': total_expenses,
        'total_revenue': total_revenue,
        'profit': profit,
        'profit_margin': profit_margin,
        'expenses_by_category': expenses_by_category,
        'expense_categories': expense_categories,
        'basic_count': basic_count,
        'standard_count': standard_count,
        'premium_count': premium_count,
        'total_subscribers': total_subscribers,
        'basic_revenue': basic_revenue,
        'standard_revenue': standard_revenue,
        'premium_revenue': premium_revenue,
        'today': today,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
    }
    
    return TemplateResponse(request, 'admin/saas_dashboard.html', context)

# Função para adicionar despesa direto do dashboard
def add_saas_expense_view(request):
    """
    Adiciona uma nova despesa diretamente do dashboard SaaS
    """
    if not request.user.is_superuser:
        raise PermissionDenied
    
    if request.method == 'POST':
        description = request.POST.get('description', '')  # Campo opcional, default vazio
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        category_id = request.POST.get('category')
        new_category = request.POST.get('new_category')
        category_icon = request.POST.get('category_icon')
        category_color = request.POST.get('category_color')
        is_recurring = request.POST.get('is_recurring') == 'on'
        recurrence_period = request.POST.get('recurrence_period') or 'monthly'
        
        # Validar campos obrigatórios - removendo descrição
        if not amount or not date:
            messages.error(request, 'Os campos de valor e data são obrigatórios.')
            return HttpResponseRedirect(reverse('admin:saas_dashboard'))
        
        try:
            # Formatar valor monetário
            amount = amount.replace('R$', '').replace('.', '').replace(',', '.')
            amount = Decimal(amount)
            
            # Escolher ou criar categoria
            if new_category:
                # Verificar se o modelo de categoria aceita company=None
                try:
                    # Primeiro verificar se o modelo tem company como nullable
                    if ExpenseCategory._meta.get_field('company').null:
                        # O campo aceita nulo
                        category = ExpenseCategory.objects.create(
                            name=new_category,
                            icon=category_icon or 'fas fa-tag',
                            color=category_color or '#6c757d',
                            company=None  # Sem empresa associada (categoria da plataforma)
                        )
                    else:
                        # O campo não aceita nulo, então precisamos criar uma lógica diferente
                        # Podemos usar uma "empresa do sistema" específica para isso
                        system_company, _ = Company.objects.get_or_create(
                            name="Sistema", 
                            defaults={"address": "Sistema", "phone": "Sistema", "email": "sistema@sistema.com"}
                        )
                        category = ExpenseCategory.objects.create(
                            name=new_category,
                            icon=category_icon or 'fas fa-tag',
                            color=category_color or '#6c757d',
                            company=system_company
                        )
                except Exception as e:
                    print(f"Erro ao criar categoria: {e}")
                    # Se falhar, tente usar a primeira categoria disponível
                    category = ExpenseCategory.objects.filter(company__isnull=True).first()
                    if not category:
                        # Se não houver categorias sem empresa, use a primeira disponível
                        category = ExpenseCategory.objects.first()
                    
                    if not category:
                        # Se ainda não houver categorias, crie uma associada à empresa do sistema
                        system_company, _ = Company.objects.get_or_create(
                            name="Sistema", 
                            defaults={"address": "Sistema", "phone": "Sistema", "email": "sistema@sistema.com"}
                        )
                        category = ExpenseCategory.objects.create(
                            name="Outros",
                            icon='fas fa-tag',
                            color='#6c757d',
                            company=system_company
                        )
            else:
                # Usar categoria existente
                category = ExpenseCategory.objects.get(id=category_id)
            
            # Verificar se o modelo Expense aceita company=None
            try:
                # Garantir que a data esteja no formato correto
                if isinstance(date, str):
                    try:
                        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                    except ValueError:
                        date_obj = datetime.date.today()
                else:
                    date_obj = date
                
                # Verificar se a empresa Sistema já existe
                system_company = Company.objects.filter(name="Sistema").first()
                if not system_company:
                    system_company = Company.objects.create(
                        name="Sistema", 
                        address="Sistema", 
                        phone="Sistema", 
                        email="sistema@sistema.com"
                    )
                
                # Sempre usar a empresa Sistema para despesas da plataforma
                # para garantir consistência nos filtros
                expense = Expense.objects.create(
                    description=description,
                    amount=amount,
                    date=date_obj,
                    category=category,
                    is_recurring=is_recurring,
                    recurrence_period=recurrence_period if is_recurring else None,
                    company=system_company,
                    is_paid=True   # Por padrão, considerar como paga
                )
                
                # Registrar sucesso
                print(f"Despesa criada com sucesso: ID={expense.id}, Valor={amount}, Categoria={category.name}, Empresa={system_company.name}")
                
            except Exception as e:
                print(f"Erro ao criar despesa: {e}")
                messages.error(request, f'Erro ao adicionar despesa: {str(e)}')
            
            messages.success(request, f'Despesa da plataforma "{description}" adicionada com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao adicionar despesa: {str(e)}')
        
        return HttpResponseRedirect(reverse('admin:saas_dashboard'))
    
    # Se não for POST, redirecionar para o dashboard
    return HttpResponseRedirect(reverse('admin:saas_dashboard'))

# Salvar o método original
if not hasattr(admin.site, '_get_urls'):
    admin.site._get_urls = admin.site.get_urls

# Criar uma classe AdminSite personalizada para adicionar a view do dashboard
class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('saas-dashboard/', self.admin_view(saas_dashboard_view), name='saas_dashboard'),
            path('saas-despesas/adicionar/', self.admin_view(add_saas_expense_view), name='add_saas_expense'),
        ]
        return custom_urls + urls

# Substituir temporariamente o admin.site com nossa versão personalizada
admin_site = admin.site
admin.site = CustomAdminSite(name=admin.site.name)
admin.site._registry = admin_site._registry

# Restaurar todas as propriedades importantes do admin site original
for attr in dir(admin_site):
    if not attr.startswith('_') and attr not in ['get_urls', 'urls']:
        if not hasattr(admin.site, attr):
            setattr(admin.site, attr, getattr(admin_site, attr))

# Configuração do UserAdmin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'company_name', 'product_count', 'total_sales', 'total_profit', 'subscription_plan', 'subscription_status', 'is_active', 'date_joined', 'actions_buttons')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'company__name')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined', 'product_count', 'total_sales', 'total_profit')
    actions = ['activate_users', 'deactivate_users', 'reset_password', 'update_plan_basic', 'update_plan_standard', 'update_plan_premium']
    
    # Enable all fields to be clickable for detail view and add CSS
    list_display_links = ('username',)
    
    # Add JavaScript to initialize sorting for total_profit column
    class Media:
        js = ('admin/js/custom_sortable.js',)
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Informações da Empresa', {'fields': ('product_count', 'total_sales', 'total_profit')}),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<id>/reset-password/',
                self.admin_site.admin_view(self.reset_user_password),
                name='user-reset-password',
            ),
            path(
                '<id>/impersonate/',
                self.admin_site.admin_view(self.impersonate_user),
                name='user-impersonate',
            ),
        ]
        return custom_urls + urls
    
    def reset_user_password(self, request, id):
        if not request.user.is_superuser:
            raise PermissionDenied
            
        user = User.objects.get(pk=id)
        # Gera uma senha aleatória
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()
        
        messages.success(request, f'Senha para {user.username} foi redefinida: {new_password}')
        return HttpResponseRedirect("../")
    
    def impersonate_user(self, request, id):
        if not request.user.is_superuser:
            raise PermissionDenied
            
        # Apenas para fins de desenvolvimento - não usar em produção sem segurança adicional
        user = User.objects.get(pk=id)
        request.session['impersonate_user_id'] = user.id
        messages.success(request, f'Agora você está navegando como {user.username}')
        return HttpResponseRedirect("/")
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Nome Completo'
    
    def company_name(self, obj):
        try:
            return obj.company.name
        except:
            return '-'
    company_name.short_description = 'Empresa'

    def product_count(self, obj):
        try:
            count = obj.company.products.count()
            # Armazenar para permitir ordenação em memória
            obj._cached_product_count = count
            return count
        except:
            obj._cached_product_count = 0
            return 0
    product_count.short_description = 'Produtos Cadastrados'

    def total_profit(self, obj):
        """
        Calcula o lucro total (receita - custo dos produtos - despesas) para um usuário.
        """
        try:
            if not hasattr(obj, 'company') or obj.company is None:
                return '-'
                
            # Recupera a empresa do usuário
            company = obj.company
            
            from django.db.models import Sum, F
            from django.db.models.functions import Coalesce
            from decimal import Decimal
            
            # Importa os modelos necessários
            from sales.models import Sale, SaleItem
            from dashboard.models import Expense
            
            # Recupera o total de vendas da empresa (receita bruta)
            total_sales = Sale.objects.filter(
                company=company,
                status='paid'
            ).aggregate(
                total=Coalesce(Sum('total'), Decimal('0.00'))
            )['total'] or Decimal('0.00')
            
            # Recupera o custo dos produtos vendidos (COGS)
            cost_of_goods = SaleItem.objects.filter(
                sale__company=company,
                sale__status='paid'
            ).aggregate(
                total=Coalesce(Sum(F('quantity') * F('cost_price')), Decimal('0.00'))
            )['total'] or Decimal('0.00')
            
            # Recupera o total de despesas da empresa
            total_expenses = Expense.objects.filter(
                company=company,
                is_paid=True
            ).aggregate(
                total=Coalesce(Sum('amount'), Decimal('0.00'))
            )['total'] or Decimal('0.00')
            
            # Calcula o lucro bruto (receita - custo dos produtos)
            gross_profit = total_sales - cost_of_goods
            
            # Calcula o lucro líquido (lucro bruto - despesas)
            net_profit = gross_profit - total_expenses
            
            # Adiciona informações de debug
            print(f"DEBUG - Calculando lucro para {obj.username} (empresa: {company.name})")
            print(f"DEBUG - Total de vendas: {total_sales}")
            print(f"DEBUG - Custo dos produtos: {cost_of_goods}")
            print(f"DEBUG - Lucro bruto: {gross_profit}")
            print(f"DEBUG - Total de despesas: {total_expenses}")
            print(f"DEBUG - Lucro líquido: {net_profit}")
            
            # Formata o valor para exibição
            formatted_value = self._format_decimal_br(net_profit, with_color=(net_profit < 0))
            
            # Retorna apenas o valor formatado sem link
            return formatted_value
            
        except Exception as e:
            print(f"Erro ao calcular lucro: {e}")
            return '-'
            
    total_profit.short_description = 'Lucro Total'
    
    def total_sales(self, obj):
        """
        Calcula o total de vendas para um usuário.
        """
        try:
            if not hasattr(obj, 'company') or obj.company is None:
                return '-'
                
            # Obter a empresa do usuário
            company = obj.company
            
            from django.db.models import Sum
            from django.db.models.functions import Coalesce
            from decimal import Decimal
            from sales.models import Sale
            
            # Calcular o total de vendas
            total_sales = Sale.objects.filter(
                company=company,
                status='paid'
            ).aggregate(
                total=Coalesce(Sum('total'), Decimal('0.00'))
            )['total'] or Decimal('0.00')
            
            # Formatar o valor para exibição
            formatted_value = self._format_decimal_br(total_sales, with_color=False)
            
            # Retorna apenas o valor formatado sem link
            return formatted_value
                
        except Exception as e:
            print(f"Erro ao calcular vendas: {e}")
            return '-'
            
    total_sales.short_description = 'Total em Vendas'

    def subscription_plan(self, obj):
        """
        Retorna o plano de assinatura do usuário.
        
        Args:
            obj (User): Objeto usuário
            
        Returns:
            str: Nome do plano ou '-' se não houver
        """
        try:
            if not hasattr(obj, 'company') or obj.company is None:
                return '-'
                
            # Buscar diretamente na tabela de assinaturas
            from core.models import Subscription
            
            subscription = Subscription.objects.filter(
                company=obj.company,
                status='active'
            ).first()
            
            if subscription:
                # Formatar nome do plano para display
                plan_names = {
                    'basic': 'Básico',
                    'standard': 'Padrão',
                    'premium': 'Premium'
                }
                return plan_names.get(subscription.plan, subscription.plan.title())
            return '-'
        except Exception as e:
            print(f"Erro ao obter plano: {e}")
            return '-'
            
    subscription_plan.short_description = 'Plano'
    
    def subscription_status(self, obj):
        """
        Retorna o status da assinatura do usuário.
        
        Args:
            obj (User): Objeto usuário
            
        Returns:
            str: Status formatado com HTML
        """
        try:
            if not hasattr(obj, 'company') or obj.company is None:
                return '-'
                
            # Buscar diretamente na tabela de assinaturas
            from core.models import Subscription
            
            subscription = Subscription.objects.filter(
                company=obj.company
            ).first()
            
            if not subscription:
                return '-'
                
            status_map = {
                'active': ('Ativa', 'success'),
                'pending': ('Pendente', 'warning'),
                'canceled': ('Cancelada', 'danger'),
                'expired': ('Expirada', 'danger')
            }
            
            text, color = status_map.get(subscription.status, ('Desconhecido', 'secondary'))
            return format_html('<span class="badge badge-{}">{}</span>', color, text)
        except Exception as e:
            print(f"Erro ao obter status: {e}")
            return '-'
            
    subscription_status.short_description = 'Status'
    
    def actions_buttons(self, obj):
        """
        Renderiza botões de ação para o usuário.
        
        Args:
            obj (User): Objeto usuário
            
        Returns:
            str: HTML com os botões de ação
        """
        try:
            reset_url = reverse('admin:user-reset-password', args=[obj.pk])
            impersonate_url = reverse('admin:user-impersonate', args=[obj.pk])
            
            buttons = f"""
            <a href="{reset_url}" class="btn btn-warning btn-sm" title="Redefinir senha">
                <i class="fas fa-key"></i>
            </a>
            <a href="{impersonate_url}" class="btn btn-info btn-sm" title="Acessar como este usuário">
                <i class="fas fa-user-secret"></i>
            </a>
            """
            return format_html(buttons)
        except Exception as e:
            print(f"Erro ao renderizar botões: {e}")
            return '-'
            
    actions_buttons.short_description = 'Ações'

    def products_count(self, obj):
        """
        Retorna a contagem de produtos ativos cadastrados para a empresa do usuário.
        
        Args:
            obj (User): Objeto de usuário
            
        Returns:
            str: Número de produtos cadastrados
        """
        try:
            # Verifica se o usuário possui empresa
            if not hasattr(obj, 'company') or obj.company is None:
                return '-'
                
            # Importa o modelo de Produto
            from products.models import Product
            
            # Conta produtos ativos desta empresa
            count = Product.objects.filter(
                company=obj.company,
                is_active=True
            ).count()
            
            # Debug para usuário específico
            if obj.username == 'lekyuri':
                print(f"DEBUG - Contagem de produtos para {obj.username}: {count}")
                
            # Armazena valor para permitir ordenação
            obj._cached_products_count = count
            
            return count
            
        except Exception as e:
            import traceback
            print(f"Erro ao contar produtos para {obj.username}: {e}")
            print(traceback.format_exc())
            return '-'
            
    products_count.short_description = 'Produtos Cadastrados'

    # Formata valores decimais no padrão brasileiro
    def _format_decimal_br(self, value, decimal_places=2, with_color=True, prefix='R$ '):
        """
        Formata um valor decimal no padrão brasileiro.
        
        Args:
            value (Decimal): Valor a ser formatado
            decimal_places (int): Número de casas decimais a exibir (padrão: 2)
            with_color (bool): Se deve adicionar código de cores HTML (padrão: True)
            prefix (str): Prefixo para o valor formatado (padrão: 'R$ ')
            
        Returns:
            str: String formatada com ou sem código de cores HTML
        """
        try:
            from django.contrib.humanize.templatetags.humanize import intcomma
            
            # Se não há valor, retorna traço
            if value is None:
                return '-'
                
            # Converte para Decimal se não for
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
                
            # Determina a cor baseada no valor
            is_negative = value < 0
            
            # Obtém o valor absoluto para formatação
            value_abs = abs(value)
            
            # Formata o número com separador de milhares
            try:
                integer_part, decimal_part = str(value_abs).split('.')
                # Ajusta casas decimais
                decimal_part = decimal_part[:decimal_places].ljust(decimal_places, '0')
                # Adiciona separador de milhares no formato brasileiro
                formatted_value = f"{intcomma(integer_part).replace(',', '.')},{decimal_part}"
            except ValueError:
                # Se não tiver casa decimal
                formatted_value = f"{intcomma(str(value_abs)).replace(',', '.')},{'0' * decimal_places}"
                
            # Adiciona sinal negativo se necessário
            if is_negative:
                formatted_value = f"-{formatted_value}"
                
            # Adiciona prefixo (normalmente R$)
            formatted_value = f"{prefix}{formatted_value}"
            
            # Adiciona cor se solicitado
            if with_color:
                if is_negative:
                    return format_html('<span class="text-danger">{}</span>', formatted_value)
                else:
                    return formatted_value  # Sem cor especial para valores positivos
            else:
                return formatted_value
                
        except Exception as e:
            import traceback
            print(f"Erro ao formatar valor: {e}")
            print(traceback.format_exc())
            return format_html('<span class="text-danger">Erro</span>')

# Desregistrar o UserAdmin padrão e registrar nosso CustomUserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Configurar o site admin
admin.site.site_header = "SnapDev CRM - Administração Master"
admin.site.site_title = "SnapDev CRM Admin"
admin.site.index_title = "Painel de Controle do Administrador - <a href='/admin/saas-dashboard/' class='btn btn-success btn-sm' style='margin-left: 10px;'><i class='fas fa-tachometer-alt'></i> Acessar Dashboard SaaS</a>"
