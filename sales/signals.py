from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Company
from .models import PaymentMethod

@receiver(post_save, sender=Company)
def create_default_payment_methods(sender, instance, created, **kwargs):
    """
    Cria os métodos de pagamento padrão quando uma nova empresa é criada
    """
    if created:
        payment_methods = [
            {'name': 'Dinheiro', 'description': 'Pagamento em espécie'},
            {'name': 'Cartão de Crédito', 'description': 'Pagamento com cartão de crédito'},
            {'name': 'Cartão de Débito', 'description': 'Pagamento com cartão de débito'},
            {'name': 'PIX', 'description': 'Pagamento via PIX'}
        ]

        for method in payment_methods:
            PaymentMethod.objects.create(
                company=instance,
                name=method['name'],
                description=method['description']
            ) 