from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/', views.home, name='home'),
    path('sobre/', views.about, name='about'),
    path('precos/', views.pricing, name='pricing'),
    path('cadastro/', views.register, name='register'),
    path('perfil/', views.profile, name='profile'),
    path('empresa/', views.company_settings, name='company_settings'),
] 