from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField('Categoria', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField('Nome', max_length=100)
    code = models.CharField('Código', max_length=50, unique=True, blank=True, null=True)
    description = models.TextField('Descrição', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoria', related_name='products')
    price = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    cost = models.DecimalField('Custo', max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField('Quantidade em estoque', default=0)
    stock_alert_level = models.PositiveIntegerField('Nível de alerta de estoque', default=10)
    barcode = models.CharField('Código de barras', max_length=100, blank=True, null=True)
    image = models.ImageField('Imagem', upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def is_stock_low(self):
        return self.stock_quantity <= self.stock_alert_level
