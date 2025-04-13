# Generated manually

from django.db import migrations
from django.utils import timezone

def create_companies_for_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Company = apps.get_model('core', 'Company')
    Subscription = apps.get_model('core', 'Subscription')
    
    for user in User.objects.filter(company__isnull=True):
        # Criar empresa
        company = Company.objects.create(
            owner=user,
            name=f'Empresa de {user.username}',
            email=user.email,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        # Criar assinatura básica
        Subscription.objects.create(
            company=company,
            plan='basic',
            status='active',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            price=0  # Trial gratuito de 30 dias
        )

def reverse_companies_for_users(apps, schema_editor):
    # Não precisamos reverter pois estamos apenas adicionando dados necessários
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_company_created_at_company_is_active_company_owner_and_more'),
    ]

    operations = [
        migrations.RunPython(create_companies_for_users, reverse_companies_for_users),
    ] 