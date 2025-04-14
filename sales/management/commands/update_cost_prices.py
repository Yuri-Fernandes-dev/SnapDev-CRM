from django.core.management.base import BaseCommand
from sales.models import SaleItem
from django.db.models import F, Q

class Command(BaseCommand):
    help = 'Atualiza cost_price para todos os itens de venda com base no custo atual do produto'

    def handle(self, *args, **options):
        # Buscar todos os itens que têm cost_price nulo ou zerado
        items_to_update = SaleItem.objects.filter(
            Q(cost_price__isnull=True) | Q(cost_price=0)
        )
        
        count = 0
        for item in items_to_update:
            if item.product and item.product.cost:
                item.cost_price = item.product.cost
                item.save()
                count += 1
                self.stdout.write(f"Atualizado item #{item.id}: produto {item.product.name}, custo {item.cost_price}")
        
        # Informações sobre itens atualizados
        self.stdout.write(self.style.SUCCESS(f"{count} itens de venda atualizados com sucesso!"))
        
        # Verificar se ainda existem itens sem custo
        remaining = SaleItem.objects.filter(
            Q(cost_price__isnull=True) | Q(cost_price=0)
        ).count()
        
        if remaining > 0:
            self.stdout.write(self.style.WARNING(f"Ainda existem {remaining} itens sem custo definido."))
        else:
            self.stdout.write(self.style.SUCCESS("Todos os itens de venda agora têm custo definido.")) 