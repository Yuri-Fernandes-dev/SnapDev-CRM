from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Size, Color, ProductVariation
from .forms import ProductForm, CategoryForm, SizeForm, ColorForm
from django.db.models import Q, F
from django.core.paginator import Paginator
import json
from django.http import JsonResponse
from .variation_views import variation_create_ajax

# Create your views here.

@login_required
def product_list(request):
    """
    View para listar produtos com filtros e paginação
    """
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('stock_status', '')
    
    products = Product.objects.filter(company=request.user.company)
    
    # Filtro por busca
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(barcode__icontains=query)
        )
    
    # Filtro por categoria
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filtro por status de estoque
    if stock_status == 'low':
        products = products.filter(stock_quantity__lte=F('min_stock_quantity'))
    
    # Ordenação
    products = products.order_by('name')
    
    # Paginação
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)
    
    # Contexto
    categories = Category.objects.filter(company=request.user.company)
    
    context = {
        'products': products_page,
        'categories': categories,
        'query': query,
        'category_id': category_id,
        'stock_status': stock_status,
    }
    
    return render(request, 'products/product_list.html', context)

@login_required
def product_detail(request, pk):
    """
    View para detalhes de um produto
    """
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    # Calcula a margem de lucro
    if product.cost and product.cost > 0:
        margin = ((product.price - product.cost) / product.cost) * 100
    else:
        margin = 0
    
    context = {
        'product': product,
        'margin': round(margin, 2)
    }
    
    return render(request, 'products/product_detail.html', context)

@login_required
def product_create(request):
    """
    View para criar um produto
    """
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.company = request.user.company
            
            # Verificar status de variações
            has_variations = request.POST.get('has_variations') == 'on'
            product.has_variations = has_variations
            
            product.save()
            
            # Processar campos de tamanho e cor se tiver variações
            if has_variations:
                size_input = request.POST.get('size', '').strip()
                color_input = request.POST.get('color', '').strip()
                
                if size_input and color_input:
                    # Dividir as entradas por vírgula
                    sizes = [s.strip().upper() for s in size_input.split(',') if s.strip()]
                    colors = [c.strip().capitalize() for c in color_input.split(',') if c.strip()]
                    
                    # Criar variações para cada combinação
                    for size_name in sizes:
                        # Buscar ou criar o tamanho
                        size, _ = Size.objects.get_or_create(
                            name=size_name,
                            company=request.user.company,
                            defaults={
                                'tipo': 'roupa',
                                'ordem': 0
                            }
                        )
                        
                        for color_name in colors:
                            # Buscar ou criar a cor
                            color, _ = Color.objects.get_or_create(
                                name=color_name,
                                company=request.user.company,
                                defaults={
                                    'code': '#6c757d'  # Cor cinza padrão
                                }
                            )
                            
                            # Criar variação
                            ProductVariation.objects.create(
                                product=product,
                                size=size,
                                color=color,
                                stock_quantity=0  # Valor padrão
                            )
            
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('products:product_list')
    else:
        form = ProductForm()
    
    # Buscar tamanhos e cores disponíveis para o contexto
    sizes = Size.objects.filter(company=request.user.company)
    colors = Color.objects.filter(company=request.user.company)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'sizes': sizes,
        'colors': colors
    })

@login_required
def product_update(request, pk):
    """
    View para atualizar um produto
    """
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            
            # Atualizar o status de variações
            has_variations = request.POST.get('has_variations') == 'on'
            product.has_variations = has_variations
            product.save()
            
            # Processar campos de tamanho e cor se tiver variações
            if has_variations:
                size_input = request.POST.get('size', '').strip()
                color_input = request.POST.get('color', '').strip()
                
                if size_input and color_input:
                    # Limpar variações existentes
                    ProductVariation.objects.filter(product=product).delete()
                    
                    # Dividir as entradas por vírgula
                    sizes = [s.strip().upper() for s in size_input.split(',') if s.strip()]
                    colors = [c.strip().capitalize() for c in color_input.split(',') if c.strip()]
                    
                    # Criar variações para cada combinação
                    for size_name in sizes:
                        # Buscar ou criar o tamanho
                        size, _ = Size.objects.get_or_create(
                            name=size_name,
                            company=request.user.company,
                            defaults={
                                'tipo': 'roupa',
                                'ordem': 0
                            }
                        )
                        
                        for color_name in colors:
                            # Buscar ou criar a cor
                            color, _ = Color.objects.get_or_create(
                                name=color_name,
                                company=request.user.company,
                                defaults={
                                    'code': '#6c757d'  # Cor cinza padrão
                                }
                            )
                            
                            # Criar variação
                            ProductVariation.objects.create(
                                product=product,
                                size=size,
                                color=color,
                                stock_quantity=0  # Valor padrão
                            )
            
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('products:product_detail', pk=product.id)
    else:
        form = ProductForm(instance=product)
    
    # Buscar tamanhos e cores disponíveis para o contexto
    sizes = Size.objects.filter(company=request.user.company)
    colors = Color.objects.filter(company=request.user.company)
    
    # Preparar valores de tamanho e cor para o template
    size_value = ""
    color_value = ""
    
    if product.has_variations:
        product_sizes = product.variations.values_list('size__name', flat=True).distinct()
        product_colors = product.variations.values_list('color__name', flat=True).distinct()
        
        size_value = ", ".join(product_sizes)
        color_value = ", ".join(product_colors)
    
    return render(request, 'products/product_form.html', {
        'form': form, 
        'object': product,
        'sizes': sizes,
        'colors': colors,
        'size_value': size_value,
        'color_value': color_value
    })

@login_required
def product_delete(request, pk):
    """
    View para excluir um produto
    """
    product = get_object_or_404(Product, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('products:product_list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})

@login_required
def category_list(request):
    """
    View para listar categorias
    """
    categories = Category.objects.filter(company=request.user.company)
    return render(request, 'products/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    """
    View para criar uma categoria
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.company = request.user.company
            category.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('products:category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'products/category_form.html', {'form': form})

@login_required
def category_create_ajax(request):
    """
    View para criar uma categoria via AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'O nome da categoria é obrigatório'
                }, status=400)
            
            category = Category.objects.create(
                company=request.user.company,
                name=name,
                description=description
            )
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name
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

@login_required
def size_list(request):
    """Lista todos os tamanhos cadastrados"""
    sizes = Size.objects.filter(company=request.user.company)
    return render(request, 'products/size_list.html', {'sizes': sizes})

@login_required
def size_create(request):
    """Cria um novo tamanho"""
    if request.method == 'POST':
        form = SizeForm(request.POST)
        if form.is_valid():
            size = form.save(commit=False)
            size.company = request.user.company
            size.save()
            messages.success(request, 'Tamanho criado com sucesso!')
            return redirect('products:size_list')
    else:
        form = SizeForm()
    return render(request, 'products/size_form.html', {'form': form})

@login_required
def size_update(request, pk):
    """Atualiza um tamanho existente"""
    size = get_object_or_404(Size, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = SizeForm(request.POST, instance=size)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tamanho atualizado com sucesso!')
            return redirect('products:size_list')
    else:
        form = SizeForm(instance=size)
    return render(request, 'products/size_form.html', {'form': form, 'size': size})

@login_required
def size_delete(request, pk):
    """
    View para excluir um tamanho
    """
    size = get_object_or_404(Size, pk=pk, company=request.user.company)
    
    if request.method == 'POST':
        size.delete()
        messages.success(request, 'Tamanho excluído com sucesso!')
        return redirect('products:size_list')
    
    return render(request, 'products/size_confirm_delete.html', {'size': size})

@login_required
def color_list(request):
    """Lista todas as cores cadastradas"""
    colors = Color.objects.filter(company=request.user.company)
    return render(request, 'products/color_list.html', {'colors': colors})

@login_required
def color_create(request):
    """Cria uma nova cor"""
    if request.method == 'POST':
        form = ColorForm(request.POST)
        if form.is_valid():
            color = form.save(commit=False)
            color.company = request.user.company
            color.save()
            messages.success(request, 'Cor criada com sucesso!')
            return redirect('products:color_list')
    else:
        form = ColorForm()
    return render(request, 'products/color_form.html', {'form': form})

@login_required
def color_update(request, pk):
    """Atualiza uma cor existente"""
    color = get_object_or_404(Color, pk=pk, company=request.user.company)
    if request.method == 'POST':
        form = ColorForm(request.POST, instance=color)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cor atualizada com sucesso!')
            return redirect('products:color_list')
    else:
        form = ColorForm(instance=color)
    return render(request, 'products/color_form.html', {'form': form, 'color': color})

@login_required
def variation_create_ajax(request, product_id):
    """
    View para criar uma variação de produto via AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            size_id = data.get('size_id')
            color_id = data.get('color_id')
            stock_quantity = data.get('stock_quantity', 0)
            
            if not size_id or not color_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Tamanho e cor são obrigatórios'
                }, status=400)
            
            product = get_object_or_404(Product, pk=product_id, company=request.user.company)
            size = get_object_or_404(Size, pk=size_id, company=request.user.company)
            color = get_object_or_404(Color, pk=color_id, company=request.user.company)
            
            # Verificar se já existe uma variação com esse tamanho e cor
            existing = ProductVariation.objects.filter(
                product=product,
                size=size,
                color=color
            ).exists()
            
            if existing:
                return JsonResponse({
                    'success': False,
                    'error': 'Já existe uma variação com esse tamanho e cor'
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

@login_required
def create_sample_sizes_and_colors(request):
    """
    View para criar tamanhos e cores de exemplo
    """
    # Criar tamanhos de exemplo
    tamanhos_exemplo = ['PP', 'P', 'M', 'G', 'GG', 'XG']
    for nome in tamanhos_exemplo:
        if not Size.objects.filter(name=nome, company=request.user.company).exists():
            Size.objects.create(
                name=nome,
                tipo='roupa',
                ordem=tamanhos_exemplo.index(nome) + 1,
                company=request.user.company
            )
    
    # Criar cores de exemplo
    cores_exemplo = [
        {'nome': 'Preto', 'codigo': '#000000'},
        {'nome': 'Branco', 'codigo': '#FFFFFF'},
        {'nome': 'Vermelho', 'codigo': '#FF0000'},
        {'nome': 'Azul', 'codigo': '#0000FF'},
        {'nome': 'Verde', 'codigo': '#00FF00'},
        {'nome': 'Amarelo', 'codigo': '#FFFF00'}
    ]
    
    for cor in cores_exemplo:
        if not Color.objects.filter(name=cor['nome'], company=request.user.company).exists():
            Color.objects.create(
                name=cor['nome'],
                code=cor['codigo'],
                company=request.user.company
            )
    
    messages.success(request, 'Tamanhos e cores de exemplo criados com sucesso!')
    
    # Redirecionar de volta para a página de edição do produto
    if 'product_id' in request.GET:
        return redirect('products:product_update', pk=request.GET['product_id'])
    
    return redirect('products:product_list')
