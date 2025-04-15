from django.urls import path
from . import views
from sales.views import sales_report

urlpatterns = [
    path('', views.home, name='home'),
    path('sobre/', views.about, name='about'),
    path('precos/', views.pricing, name='pricing'),
    path('cadastro/', views.register, name='register'),
    path('perfil/', views.profile, name='profile'),
    path('empresa/', views.company_settings, name='company_settings'),
    path('relatorios/', sales_report, name='reports'),
    path('assinatura/', views.subscription, name='subscription'),
    path('planos/', views.subscription_plans, name='subscription_plans'),
    path('atualizar-assinatura/<str:plan>/', views.update_subscription, name='update_subscription'),
    path('suporte/', views.support, name='support'),
] 