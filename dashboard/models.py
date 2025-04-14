from django.db import models
from django.utils import timezone

# Create your models here.

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="fa-building")
    color = models.CharField(max_length=20, default="primary")
    company = models.ForeignKey("core.Company", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Categoria de Despesa"
        verbose_name_plural = "Categorias de Despesas"
        ordering = ['name']

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    is_recurring = models.BooleanField(default=False)
    recurrence_period = models.CharField(max_length=20, blank=True, choices=[
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual')
    ])
    is_paid = models.BooleanField(default=False, verbose_name="Pago")
    company = models.ForeignKey("core.Company", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category.name}: R${self.amount}"
    
    def get_status_display(self):
        return "Pago" if self.is_paid else "Pendente"
    
    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ['-date']
