from django.urls import path
from . import views

# Rotas públicas que não precisam de autenticação
urlpatterns = [
    path('recibo/<str:token>/', views.public_receipt, name='public_receipt'),
    path('r/<str:token>/', views.public_receipt, name='public_receipt_short'),
] 