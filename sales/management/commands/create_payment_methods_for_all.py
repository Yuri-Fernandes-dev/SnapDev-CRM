from django.core.management.base import BaseCommand
from core.models import Company
from sales.models import PaymentMethod

class Command(BaseCommand):
    help = 'Cria os métodos de pagamento padrão para todas as empresas'

    def handle(self, *args, **kwargs):
        companies = Company.objects.all()
        
        payment_methods = [
            {'name': 'Dinheiro', 'description': 'Pagamento em espécie'},
            {'name': 'Cartão de Crédito', 'description': 'Pagamento com cartão de crédito'},
            {'name': 'Cartão de Débito', 'description': 'Pagamento com cartão de débito'},
            {'name': 'PIX', 'description': 'Pagamento via PIX'}
        ]

        for company in companies:
            self.stdout.write(f'Criando métodos de pagamento para {company.name}...')
            
            for method in payment_methods:
                payment_method, created = PaymentMethod.objects.get_or_create(
                    company=company,
                    name=method['name'],
                    defaults={'description': method['description']}
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Método de pagamento "{method["name"]}" criado para a empresa {company.name}!')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Método de pagamento "{method["name"]}" já existe para a empresa {company.name}.')
                    )
            
            self.stdout.write(self.style.SUCCESS(f'Métodos de pagamento criados com sucesso para {company.name}!')) 