from django.contrib import admin
from .models import Company, Subscription

class SubscriptionInline(admin.StackedInline):
    model = Subscription
    can_delete = False
    verbose_name_plural = 'Assinatura'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'city', 'state')
    search_fields = ('name', 'email', 'phone', 'address', 'city')
    inlines = [SubscriptionInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'cnpj', 'email', 'phone', 'logo')
        }),
        ('Endereço', {
            'fields': ('address', 'city', 'state', 'zipcode')
        }),
    )

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('company', 'plan', 'status', 'start_date', 'end_date', 'price')
    list_filter = ('plan', 'status', 'start_date', 'end_date')
    search_fields = ('company__name',)
    autocomplete_fields = ('company',)
    date_hierarchy = 'start_date'
