from django.core.management.base import BaseCommand
from sales.models import PaymentMethod
from core.models import Company

class Command(BaseCommand):
    help = 'Cria os métodos de pagamento padrão para uma empresa'

    def add_arguments(self, parser):
        parser.add_argument('company_id', type=int, help='ID da empresa')

    def handle(self, *args, **kwargs):
        try:
            company = Company.objects.get(pk=kwargs['company_id'])
        except Company.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Empresa com ID {kwargs["company_id"]} não encontrada.'))
            return

        payment_methods = [
            {'name': 'Dinheiro', 'description': 'Pagamento em espécie'},
            {'name': 'Cartão de Crédito', 'description': 'Pagamento com cartão de crédito'},
            {'name': 'Cartão de Débito', 'description': 'Pagamento com cartão de débito'},
            {'name': 'PIX', 'description': 'Pagamento via PIX'}
        ]

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