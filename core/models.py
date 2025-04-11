from django.db import models
from django.utils import timezone

# Create your models here.

class Company(models.Model):
    name = models.CharField('Nome da Empresa', max_length=100)
    cnpj = models.CharField('CNPJ', max_length=18, blank=True, null=True)
    email = models.EmailField('E-mail', max_length=100, blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    address = models.CharField('Endereço', max_length=200, blank=True, null=True)
    city = models.CharField('Cidade', max_length=100, blank=True, null=True)
    state = models.CharField('Estado', max_length=2, blank=True, null=True)
    zipcode = models.CharField('CEP', max_length=9, blank=True, null=True)
    logo = models.ImageField('Logo', upload_to='company_logos/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        address_parts = [part for part in [self.address, self.city, self.state, self.zipcode] if part]
        return ', '.join(address_parts) if address_parts else ''

class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Ativa'),
        ('pending', 'Pendente'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    )
    
    PLAN_CHOICES = (
        ('basic', 'Básico'),
        ('standard', 'Padrão'),
        ('premium', 'Premium'),
    )
    
    company = models.OneToOneField(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='subscription')
    plan = models.CharField('Plano', max_length=20, choices=PLAN_CHOICES, default='basic')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField('Data de Início', null=True, blank=True)
    end_date = models.DateField('Data de Término', null=True, blank=True)
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'
    
    def __str__(self):
        return f'{self.company.name} - {self.get_plan_display()}'
    
    def is_active(self):
        today = timezone.now().date()
        return (
            self.status == 'active' and
            self.start_date and 
            self.end_date and
            self.start_date <= today <= self.end_date
        )
