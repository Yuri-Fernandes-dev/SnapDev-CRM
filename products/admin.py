from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'cost', 'stock_quantity', 'is_stock_low', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'barcode')
    autocomplete_fields = ('category',)
    date_hierarchy = 'created_at'
    list_editable = ('price', 'stock_quantity', 'is_active')
    
    def is_stock_low(self, obj):
        return obj.is_stock_low()
    
    is_stock_low.boolean = True
    is_stock_low.short_description = 'Estoque Baixo'
