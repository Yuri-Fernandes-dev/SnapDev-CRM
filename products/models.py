from django.db import models
from django.utils import timezone
from core.models import Company
from django.core.validators import MinValueValidator

class Category(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='categories')
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True, null=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
        unique_together = ['company', 'name']  # Prevent duplicate category names within same company
    
    def __str__(self):
        return self.name

class Size(models.Model):
    TIPO_CHOICES = (
        ('roupa', 'Roupa'),
        ('calcado', 'Calçado'),
    )
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='sizes')
    name = models.CharField('Nome', max_length=10)  # PP, P, M, G, GG ou 36, 37, 38, etc
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default='roupa')
    ordem = models.IntegerField('Ordem de exibição', default=0)
    
    class Meta:
        verbose_name = 'Tamanho'
        verbose_name_plural = 'Tamanhos'
        ordering = ['ordem', 'name']
        unique_together = ['company', 'name', 'tipo']
    
    def __str__(self):
        return self.name

class Color(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='colors')
    name = models.CharField('Nome', max_length=50)
    code = models.CharField('Código Hex', max_length=7, help_text='Ex: #FF0000', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Cor'
        verbose_name_plural = 'Cores'
        ordering = ['name']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='Empresa', related_name='products')
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
    has_variations = models.BooleanField('Possui variações', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['name']
        unique_together = [['company', 'code'], ['company', 'barcode']]  # Prevent duplicate codes/barcodes within same company
    
    def __str__(self):
        return self.name
    
    def is_stock_low(self):
        if self.has_variations:
            return any(variation.is_stock_low() for variation in self.variations.all())
        return self.stock_quantity <= self.stock_alert_level

class ProductVariation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Produto', related_name='variations')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, verbose_name='Tamanho')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, verbose_name='Cor')
    stock_quantity = models.PositiveIntegerField('Quantidade em estoque', default=0)
    stock_alert_level = models.PositiveIntegerField('Nível de alerta de estoque', default=3)
    sku = models.CharField('SKU', max_length=100, unique=True, blank=True, null=True)
    price_adjustment = models.DecimalField('Ajuste de preço', max_digits=10, decimal_places=2, default=0,
                                         help_text='Valor a ser adicionado/subtraído do preço base do produto')
    
    class Meta:
        verbose_name = 'Variação de Produto'
        verbose_name_plural = 'Variações de Produtos'
        unique_together = ['product', 'size', 'color']
    
    def __str__(self):
        return f'{self.product.name} - {self.size} {self.color}'
    
    def is_stock_low(self):
        return self.stock_quantity <= self.stock_alert_level
    
    def get_final_price(self):
        return self.product.price + self.price_adjustment
