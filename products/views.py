from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category
from .forms import ProductForm, CategoryForm
from django.db.models import Q
from django.core.paginator import Paginator

# Create your views here.

@login_required
def product_list(request):
    """
    View para listar produtos com filtros e paginação
    """
    query = request.GET.get('query', '')
    category_id = request.GET.get('category', '')
    stock_status = request.GET.get('stock_status', '')
    
    products = Product.objects.all()
    
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
        products = [p for p in products if p.is_stock_low()]
    
    # Ordenação
    products = products.order_by('name')
    
    # Paginação
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)
    
    # Contexto
    categories = Category.objects.all()
    
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
    product = get_object_or_404(Product, pk=pk)
    
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
            form.save()
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_update(request, pk):
    """
    View para atualizar um produto
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {'form': form, 'object': product})

@login_required
def product_delete(request, pk):
    """
    View para excluir um produto
    """
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('product_list')
    
    return render(request, 'products/product_confirm_delete.html', {'product': product})

@login_required
def category_list(request):
    """
    View para listar categorias
    """
    categories = Category.objects.all()
    return render(request, 'products/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    """
    View para criar uma categoria
    """
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    
    return render(request, 'products/category_form.html', {'form': form})
