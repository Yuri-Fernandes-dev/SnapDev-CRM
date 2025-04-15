from django.core.management.base import BaseCommand
from core.models import Subscription
from decimal import Decimal
from saas_crm.settings import SUBSCRIPTION_PLANS

class Command(BaseCommand):
    help = 'Atualiza os preços das assinaturas de acordo com as configurações em SUBSCRIPTION_PLANS'

    def handle(self, *args, **options):
        # Definir os preços corretos
        basic_price = SUBSCRIPTION_PLANS['basic']['price']
        standard_price = SUBSCRIPTION_PLANS['standard']['price']
        premium_price = SUBSCRIPTION_PLANS['premium']['price']
        
        # Atualizar assinaturas básicas
        basic_subscriptions = Subscription.objects.filter(plan='basic')
        basic_updated = basic_subscriptions.update(price=Decimal(str(basic_price)))
        
        # Atualizar assinaturas padrão
        standard_subscriptions = Subscription.objects.filter(plan='standard')
        standard_updated = standard_subscriptions.update(price=Decimal(str(standard_price)))
        
        # Atualizar assinaturas premium
        premium_subscriptions = Subscription.objects.filter(plan='premium')
        premium_updated = premium_subscriptions.update(price=Decimal(str(premium_price)))
        
        # Exibir resultados
        self.stdout.write(self.style.SUCCESS(f'Atualizados {basic_updated} planos básicos para R${basic_price}'))
        self.stdout.write(self.style.SUCCESS(f'Atualizados {standard_updated} planos padrão para R${standard_price}'))
        self.stdout.write(self.style.SUCCESS(f'Atualizados {premium_updated} planos premium para R${premium_price}'))
        self.stdout.write(self.style.SUCCESS(f'Total de {basic_updated + standard_updated + premium_updated} assinaturas atualizadas.')) 