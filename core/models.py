from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Company(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Proprietário', null=True, blank=True)
    name = models.CharField('Nome da Empresa', max_length=100)
    cnpj = models.CharField('CNPJ', max_length=18, blank=True, null=True)
    email = models.EmailField('E-mail', max_length=100, blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    address = models.CharField('Endereço', max_length=200, blank=True, null=True)
    city = models.CharField('Cidade', max_length=100, blank=True, null=True)
    state = models.CharField('Estado', max_length=2, blank=True, null=True)
    zipcode = models.CharField('CEP', max_length=9, blank=True, null=True)
    logo = models.ImageField('Logo', upload_to='company_logos/', blank=True, null=True)
    is_active = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField('Criado em', default=timezone.now)
    updated_at = models.DateTimeField('Atualizado em', default=timezone.now)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        address_parts = [part for part in [self.address, self.city, self.state, self.zipcode] if part]
        return ', '.join(address_parts) if address_parts else ''
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Se é uma nova instância
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

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

@receiver(post_save, sender=User)
def create_company_for_user(sender, instance, created, **kwargs):
    """
    Signal para criar automaticamente uma empresa e assinatura para novos usuários
    """
    if created and not hasattr(instance, 'company'):
        # Criar empresa
        company = Company.objects.create(
            owner=instance,
            name=f'Empresa de {instance.username}',
            email=instance.email
        )
        
        # Criar assinatura básica
        Subscription.objects.create(
            company=company,
            plan='basic',
            status='active',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30),
            price=0  # Trial gratuito de 30 dias
        )
