from django.contrib import admin
from .models import ExpenseCategory, Expense

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'company')
    list_filter = ('company',)
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date', 'is_recurring', 'company')
    list_filter = ('category', 'date', 'is_recurring', 'company')
    search_fields = ('description',)
    date_hierarchy = 'date'
