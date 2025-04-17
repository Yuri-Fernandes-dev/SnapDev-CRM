from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('estoque/', views.inventory_dashboard, name='inventory_dashboard'),
    path('vendas/', views.sales_dashboard, name='sales_dashboard'),
    path('clientes/', views.customers_dashboard, name='customers_dashboard'),
    path('despesas/', views.expenses_dashboard, name='expenses'),
    path('despesas/adicionar/', views.add_expense, name='add_expense'),
    path('despesas/editar/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('despesas/excluir/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('despesas/toggle-payment/<int:expense_id>/', views.toggle_expense_payment, name='toggle_expense_payment'),
    path('despesas/categorias/adicionar/', views.add_expense_category, name='add_expense_category'),
    path('despesas/categorias/editar/<int:category_id>/', views.edit_expense_category, name='edit_expense_category'),
    path('despesas/categorias/excluir/<int:category_id>/', views.delete_expense_category, name='delete_expense_category'),
    # URL for SaaS platform expenses (admin only)
    path('admin/saas-despesas/adicionar/', views.add_saas_expense, name='add_saas_expense'),
]