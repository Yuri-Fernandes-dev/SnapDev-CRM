from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer
from .forms import CustomerForm
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from sales.models import Sale

@login_required
def customer_list(request):
    """
    View para listar clientes com filtros e paginação
    """
    query = request.GET.get('query', '')
    
    customers = Customer.objects.all()
    
    # Filtro por busca
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(address__icontains=query) |
            Q(city__icontains=query)
        )
    
    # Ordenação
    customers = customers.order_by('name')
    
    # Paginação
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page', 1)
    customers_page = paginator.get_page(page_number)
    
    context = {
        'customers': customers_page,
        'query': query,
    }
    
    return render(request, 'customers/customer_list.html', context)

@login_required
def customer_detail(request, pk):
    """
    View para detalhes de um cliente e histórico de compras
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    # Histórico de vendas
    sales = Sale.objects.filter(customer=customer).order_by('-created_at')
    
    # Resumo de compras
    total_purchases = sales.filter(status='paid').count()
    total_spent = sales.filter(status='paid').aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'customer': customer,
        'sales': sales,
        'total_purchases': total_purchases,
        'total_spent': total_spent,
    }
    
    return render(request, 'customers/customer_detail.html', context)

@login_required
def customer_create(request):
    """
    View para criar um cliente
    """
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'customers/customer_form.html', {'form': form})

@login_required
def customer_update(request, pk):
    """
    View para atualizar um cliente
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'customers/customer_form.html', {'form': form, 'object': customer})

@login_required
def customer_delete(request, pk):
    """
    View para excluir um cliente
    """
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Cliente excluído com sucesso!')
        return redirect('customer_list')
    
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})
