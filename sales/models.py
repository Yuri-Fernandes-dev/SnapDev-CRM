from django.db import models
from django.utils import timezone
from django.conf import settings
from customers.models import Customer
from products.models import Product
from decimal import Decimal
from core.models import Company
from django.contrib.auth import get_user_model
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
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Cliente', related_name='sales')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Método de Pagamento')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Criado por')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField('Desconto', max_digits=10, decimal_places=2, default=0)
    notes = models.TextField('Observações', blank=True, null=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    is_canceled = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    canceled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='canceled_sales'
    )
    access_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    
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
        if not self.access_token:
            self.access_token = self.generate_access_token()
        super().save(*args, **kwargs)
    
    def generate_access_token(self):
        """Gera um token único para acesso ao recibo"""
        unique_id = uuid.uuid4().hex
        return hashlib.sha256(unique_id.encode()).hexdigest()

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, verbose_name='Venda', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produto')
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
        # Capturar o custo do produto no momento da venda
        if not self.id or not self.cost_price:  # Verificar na criação ou se cost_price estiver vazio
            self.cost_price = self.product.cost
            
        # Calcular subtotal
        self.subtotal = self.price * self.quantity
        super(SaleItem, self).save(*args, **kwargs)
        
        # Atualizar estoque do produto apenas se a venda estiver paga
        if self.sale.status == 'paid':
            self.product.stock_quantity -= self.quantity
            self.product.save()
