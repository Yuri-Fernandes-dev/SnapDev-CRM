from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'city', 'state', 'created_at')
    list_filter = ('state', 'city', 'created_at')
    search_fields = ('name', 'email', 'phone', 'address', 'city')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Endereço', {
            'fields': ('address', 'city', 'state', 'zipcode')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
    )
