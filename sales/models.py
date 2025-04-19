from django.db import models
from django.utils import timezone
from django.conf import settings
from customers.models import Customer
from products.models import Product
from decimal import Decimal
from core.models import Company
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
import uuid
import hashlib

class PaymentMethod(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='payment_methods')
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', default=timezone.now)
    updated_at = models.DateTimeField('Atualizado em', default=timezone.now)
    
    class Meta:
        verbose_name = 'Método de Pagamento'
        verbose_name_plural = 'Métodos de Pagamento'
        ordering = ['name']
        unique_together = ['company', 'name']  # Prevent duplicate payment methods within same company
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

class Sale(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendente'),
        ('paid', 'Pago'),
        ('cancelled', 'Cancelado'),
    )
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='sales')
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales'
    )
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, verbose_name='Método de Pagamento', related_name='sales')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, verbose_name='Criado por', related_name='sales_created')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField('Desconto', max_digits=10, decimal_places=2, default=0)
    cost_total = models.DecimalField('Custo Total', max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField('Lucro', max_digits=10, decimal_places=2, default=0)
    profit_margin = models.DecimalField('Margem de Lucro', max_digits=5, decimal_places=2, default=0)
    notes = models.TextField('Observações', blank=True, null=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    is_canceled = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='canceled_sales'
    )
    access_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    class Meta:
        verbose_name = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Venda #{self.id}'
    
    def get_items_count(self):
        return self.items.count()
    
    def calculate_total(self):
        if not self.id:  # Se a venda ainda não foi salva, retorna 0
            return Decimal('0')
        total = sum(item.subtotal for item in self.items.all())
        return total - self.discount if total else Decimal('0')

    def save(self, *args, **kwargs):
        if not self.pk:  # Se é uma nova venda
            self.access_token = uuid.uuid4()
        
        # Recalcular totais se houver itens
        if self.pk:
            # Custo total
            self.cost_total = self.items.aggregate(
                total=Sum(F('quantity') * F('cost_price'))
            )['total'] or Decimal('0')
            
            # Lucro
            self.profit = self.total - self.cost_total
            
            # Margem de lucro
            if self.total > 0:
                self.profit_margin = (self.profit / self.total) * 100
            else:
                self.profit_margin = Decimal('0')
        
        super().save(*args, **kwargs)

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name='Venda', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Produto', related_name='sale_items')
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    cost_price = models.DecimalField('Custo', max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'
    
    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
    
    def save(self, *args, **kwargs):
        # Atualizar preço de custo do produto
        self.cost_price = self.product.cost
        
        # Calcular subtotal
        self.subtotal = self.quantity * self.price
        
        super(SaleItem, self).save(*args, **kwargs)
        
        # Recalcular totais da venda
        self.sale.save()
        
        # Atualizar estoque do produto apenas se a venda estiver paga
        if self.sale.status == 'paid':
            if self.product.has_variations:
                # Se o produto tem variações, deve ser tratado de forma diferente
                pass  # TODO: Implementar lógica para produtos com variações
            else:
                # Ler o valor atual do estoque antes de atualizar
                current_stock = Product.objects.get(pk=self.product.pk).stock_quantity
                # Calcular novo valor do estoque
                new_stock = max(0, current_stock - self.quantity)
                # Atualizar o estoque
                self.product.stock_quantity = new_stock
                self.product.save()
