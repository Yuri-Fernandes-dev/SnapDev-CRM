from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from core.models import Company

class LoyaltyTier(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='loyalty_tiers')
    name = models.CharField('Nome', max_length=100)
    min_points = models.IntegerField('Pontos Mínimos')
    discount_percentage = models.DecimalField('Desconto (%)', max_digits=5, decimal_places=2)
    description = models.TextField('Descrição', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Nível de Fidelidade'
        verbose_name_plural = 'Níveis de Fidelidade'
        ordering = ['min_points']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return self.name

class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='customers')
    name = models.CharField('Nome', max_length=100)
    email = models.EmailField('E-mail', max_length=100, blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    address = models.CharField('Endereço', max_length=200, blank=True, null=True)
    city = models.CharField('Cidade', max_length=100, blank=True, null=True)
    state = models.CharField('Estado', max_length=2, blank=True, null=True)
    zipcode = models.CharField('CEP', max_length=9, blank=True, null=True)
    notes = models.TextField('Observações', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Campos de fidelidade
    loyalty_points = models.IntegerField('Pontos de Fidelidade', default=0)
    loyalty_tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Nível de Fidelidade')
    birthday = models.DateField('Data de Nascimento', null=True, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']
        unique_together = [['company', 'email'], ['company', 'phone']]  # Prevent duplicate contacts within same company
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        address_parts = [part for part in [self.address, self.city, self.state, self.zipcode] if part]
        return ', '.join(address_parts) if address_parts else ''
    
    @property
    def total_purchases(self):
        """Retorna o total de compras pagas do cliente"""
        from sales.models import Sale
        total = Sale.objects.filter(
            customer=self,
            status='paid'
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        return total
    
    @property
    def total_purchases_count(self):
        """Retorna o número de compras pagas do cliente"""
        from sales.models import Sale
        return Sale.objects.filter(customer=self, status='paid').count()
    
    def add_points(self, amount):
        """Adiciona pontos baseado no valor da compra"""
        points_to_add = int(amount)
        if self.loyalty_tier:
            points_to_add = int(points_to_add * self.loyalty_tier.points_multiplier)
        self.loyalty_points += points_to_add
        self.update_tier()
        self.save()
    
    def update_tier(self):
        """Atualiza o nível de fidelidade baseado nos pontos"""
        new_tier = LoyaltyTier.objects.filter(
            min_points__lte=self.loyalty_points
        ).order_by('-min_points').first()
        
        if new_tier != self.loyalty_tier:
            self.loyalty_tier = new_tier
            return True
        return False
    
    def get_available_discount(self):
        """Retorna o desconto disponível baseado no nível"""
        if self.loyalty_tier:
            return self.loyalty_tier.discount_percentage
        return Decimal('0.00')
    
    def is_birthday_month(self):
        """Verifica se é o mês de aniversário do cliente"""
        if self.birthday:
            return self.birthday.month == timezone.now().month
        return False

class LoyaltyTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('EARN', 'Ganhou Pontos'),
        ('REDEEM', 'Resgatou Pontos'),
        ('EXPIRE', 'Pontos Expirados'),
        ('BONUS', 'Pontos Bônus'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loyalty_transactions')
    points = models.IntegerField('Pontos')
    transaction_type = models.CharField('Tipo', max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField('Descrição', max_length=200)
    created_at = models.DateTimeField('Data', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transação de Pontos'
        verbose_name_plural = 'Transações de Pontos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.points} pontos'
