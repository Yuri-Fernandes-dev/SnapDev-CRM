from django.core.management.base import BaseCommand
from sales.models import Sale

class Command(BaseCommand):
    help = 'Gera tokens de acesso para todas as vendas existentes'

    def handle(self, *args, **options):
        # Obter todas as vendas sem token
        sales_without_token = Sale.objects.filter(access_token__isnull=True)
        count = sales_without_token.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('Todas as vendas já possuem tokens de acesso.'))
            return
        
        # Gerar token para cada venda
        for sale in sales_without_token:
            sale.access_token = sale.generate_access_token()
            sale.save(update_fields=['access_token'])
        
        self.stdout.write(self.style.SUCCESS(f'Tokens de acesso gerados para {count} vendas.')) 