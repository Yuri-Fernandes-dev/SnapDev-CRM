from django.urls import path
from . import views

urlpatterns = [
    path('', views.customer_list, name='customer_list'),
    path('<int:pk>/', views.customer_detail, name='customer_detail'),
    path('novo/', views.customer_create, name='customer_create'),
    path('<int:pk>/editar/', views.customer_update, name='customer_update'),
    path('<int:pk>/excluir/', views.customer_delete, name='customer_delete'),
] 