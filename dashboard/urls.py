from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('estoque/', views.inventory_dashboard, name='inventory'),
    path('vendas/', views.sales_dashboard, name='sales'),
    path('clientes/', views.customers_dashboard, name='customers'),
    
    # Despesas
    path('despesas/', views.expenses_dashboard, name='expenses'),
    path('despesas/nova/', views.add_expense, name='add_expense'),
    path('despesas/editar/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('despesas/excluir/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('despesas/toggle-payment/<int:expense_id>/', views.toggle_expense_payment, name='toggle_expense_payment'),
    
    # Categorias de despesas
    path('despesas/categorias/nova/', views.add_expense_category, name='add_expense_category'),
    path('despesas/categorias/editar/<int:category_id>/', views.edit_expense_category, name='edit_expense_category'),
    path('despesas/categorias/excluir/<int:category_id>/', views.delete_expense_category, name='delete_expense_category'),
    
    # SaaS Admin
    path('saas/despesa/nova/', views.add_saas_expense, name='add_saas_expense'),
    
    # Dashboards alternativos de despesas
    path('despesas/nova-interface/', views.expenses_dashboard_new, name='expenses_dashboard_new'),
    path('despesas/simplificada/', views.expenses_dashboard_simple, name='expenses_dashboard_simple'),
    
    # API para dados de gráficos
    path('api/despesas/grafico-dados/', views.expense_chart_data, name='expense_chart_data'),
]