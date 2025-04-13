from django.db import models
from django.utils import timezone
from django.conf import settings
from customers.models import Customer
from products.models import Product
from decimal import Decimal

class PaymentMethod(models.Model):
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', default=timezone.now)
    updated_at = models.DateTimeField('Atualizado em', default=timezone.now)
    
    class Meta:
        verbose_name = 'Método de Pagamento'
        verbose_name_plural = 'Métodos de Pagamento'
        ordering = ['name']
    
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
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Cliente', related_name='sales')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Método de Pagamento')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Criado por')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField('Desconto', max_digits=10, decimal_places=2, default=0)
    notes = models.TextField('Observações', blank=True, null=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
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

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name='Venda', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produto')
    quantity = models.PositiveIntegerField('Quantidade', default=1)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Item da Venda'
        verbose_name_plural = 'Itens da Venda'
    
    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
    
    def save(self, *args, **kwargs):
        # Calcular subtotal
        self.subtotal = self.price * self.quantity
        super(SaleItem, self).save(*args, **kwargs)
        
        # Atualizar estoque do produto apenas se a venda estiver paga
        if self.sale.status == 'paid':
            self.product.stock_quantity -= self.quantity
            self.product.save()
