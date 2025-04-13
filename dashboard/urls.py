from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('estoque/', views.inventory_dashboard, name='inventory_dashboard'),
    path('vendas/', views.sales_dashboard, name='sales_dashboard'),
    path('clientes/', views.customers_dashboard, name='customers_dashboard'),
] 