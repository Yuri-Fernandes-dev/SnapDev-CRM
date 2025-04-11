from django.contrib import admin
from .models import Sale, SaleItem, PaymentMethod

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    autocomplete_fields = ('product',)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'total', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('customer__name', 'notes')
    autocomplete_fields = ('customer', 'payment_method')
    readonly_fields = ('total',)
    date_hierarchy = 'created_at'
    inlines = [SaleItemInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('customer', 'status', 'payment_method')
        }),
        ('Valores', {
            'fields': ('total', 'discount')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
    )
