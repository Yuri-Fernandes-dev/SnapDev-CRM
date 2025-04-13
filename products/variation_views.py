from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Product, Size, Color, ProductVariation
import json

@login_required
def variation_create_ajax(request, product_id):
    """
    View para criar uma variação de produto via AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            size_name = data.get('size_name')
            color_name = data.get('color_name')
            stock_quantity = data.get('stock_quantity', 0)
            
            if not size_name or not color_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Tamanho e cor são obrigatórios'
                }, status=400)
            
            product = get_object_or_404(Product, pk=product_id, company=request.user.company)
            
            # Buscar ou criar o tamanho
            size, size_created = Size.objects.get_or_create(
                name=size_name.upper(),
                company=request.user.company,
                defaults={
                    'tipo': 'roupa',
                    'ordem': 0  # Valor padrão
                }
            )
            
            # Buscar ou criar a cor
            color, color_created = Color.objects.get_or_create(
                name=color_name.capitalize(),
                company=request.user.company,
                defaults={
                    'code': '#6c757d'  # Cor cinza padrão
                }
            )
            
            # Verificar se já existe uma variação com esse tamanho e cor
            existing = ProductVariation.objects.filter(
                product=product,
                size=size,
                color=color
            ).exists()
            
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': f'Já existe uma variação com o tamanho {size_name} e cor {color_name}'
                }, status=400)
            
            # Criar a variação
            variation = ProductVariation.objects.create(
                product=product,
                size=size,
                color=color,
                stock_quantity=stock_quantity
            )
            
            # Garantir que o produto está marcado como tendo variações
            if not product.has_variations:
                product.has_variations = True
                product.save()
            
            return JsonResponse({
                'success': True,
                'variation': {
                    'id': variation.id,
                    'size': size.name,
                    'color': color.name,
                    'stock_quantity': variation.stock_quantity
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'error': 'Método não permitido'
    }, status=405) 