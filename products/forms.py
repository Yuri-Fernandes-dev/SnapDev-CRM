from django import forms
from .models import Product, Category, Size, Color

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'code',
            'description',
            'category',
            'price',
            'cost',
            'stock_quantity',
            'stock_alert_level',
            'barcode',
            'image',
            'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SizeForm(forms.ModelForm):
    class Meta:
        model = Size
        fields = ['name', 'tipo', 'ordem']
        labels = {
            'name': 'Nome',
            'tipo': 'Tipo',
            'ordem': 'Ordem'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: P, M, G ou 38, 39, 40'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Vestuário, Calçado'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ordem de exibição'})
        }

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'code']
        labels = {
            'name': 'Nome',
            'code': 'Código da Cor'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Azul, Vermelho, Verde'}),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': 'Selecione a cor'
            })
        } 