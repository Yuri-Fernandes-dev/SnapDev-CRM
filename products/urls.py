from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('novo/', views.product_create, name='product_create'),
    path('<int:pk>/editar/', views.product_update, name='product_update'),
    path('<int:pk>/excluir/', views.product_delete, name='product_delete'),
    
    path('categorias/', views.category_list, name='category_list'),
    path('categorias/nova/', views.category_create, name='category_create'),
    path('categorias/nova/ajax/', views.category_create_ajax, name='category_create_ajax'),
    
    # URLs para gerenciamento de tamanhos
    path('tamanhos/', views.size_list, name='size_list'),
    path('tamanhos/novo/', views.size_create, name='size_create'),
    path('tamanhos/<int:pk>/editar/', views.size_update, name='size_update'),
    path('tamanhos/<int:pk>/excluir/', views.size_delete, name='size_delete'),
    
    # URLs para gerenciamento de cores
    path('cores/', views.color_list, name='color_list'),
    path('cores/nova/', views.color_create, name='color_create'),
    path('cores/<int:pk>/editar/', views.color_update, name='color_update'),
    
    # URL para gerenciamento de variações
    path('<int:product_id>/variacoes/criar/ajax/', views.variation_create_ajax, name='variation_create_ajax'),
    
    # URL para criar tamanhos e cores de exemplo
    path('criar-exemplos/', views.create_sample_sizes_and_colors, name='create_sample_sizes_and_colors'),
] 