from django.urls import path
from . import views

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('pdv/', views.point_of_sale, name='point_of_sale'),
    path('busca-produto/', views.product_search, name='product_search'),
    path('criar/', views.create_sale, name='create_sale'),
    path('relatorio/', views.sales_report, name='sales_report'),
] 