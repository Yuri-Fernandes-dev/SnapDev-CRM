from django.urls import path
from . import views

urlpatterns = [
    # URLs do sistema (todas agora sob /sistema/)
    path('', views.dashboard, name='dashboard'),  # Dashboard como página inicial do sistema
    path('perfil/', views.profile, name='profile'),
    path('empresa/', views.company_settings, name='company_settings'),
    path('assinatura/', views.subscription, name='subscription'),
    path('planos/', views.subscription_plans, name='subscription_plans'),
    path('atualizar-assinatura/<str:plan>/', views.update_subscription, name='update_subscription'),
    path('suporte/', views.support, name='support'),
]