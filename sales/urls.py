from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('pdv/', views.point_of_sale, name='point_of_sale'),
    path('relatorios/', views.reports, name='reports'),  # Nova URL para relatórios
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:sale_id>/cancelar/', views.cancel_sale, name='cancel_sale'),
    path('<int:pk>/recibo/', views.sale_receipt, name='sale_receipt'),
    path('<int:pk>/recibo-pdf/', views.sale_pdf, name='sale_pdf'),
    path('<int:pk>/whatsapp/', views.send_whatsapp_message, name='send_whatsapp'),
    path('busca-produto/', views.product_search, name='product_search'),
    path('criar/', views.create_sale, name='create_sale'),
    path('api/criar-venda/', views.create_sale, name='sale_create_api'),
    path('confirmar-venda/', views.create_sale, name='confirm_sale'),
]