from django.core.management.base import BaseCommand
from sales.models import PaymentMethod

class Command(BaseCommand):
    help = 'Cria os métodos de pagamento padrão'

    def handle(self, *args, **kwargs):
        payment_methods = [
            'Dinheiro',
            'Cartão de Crédito',
            'Cartão de Débito',
            'PIX'
        ]

        for method in payment_methods:
            PaymentMethod.objects.get_or_create(name=method)
            self.stdout.write(self.style.SUCCESS(f'Método de pagamento "{method}" criado com sucesso!')) 