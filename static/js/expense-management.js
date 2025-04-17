/**
 * Arquivo: expense-management.js
 * Descrição: Gerencia as funcionalidades de despesas, incluindo exclusão e alteração de status
 */

// Função para alternar o status de pagamento de uma despesa
function togglePaymentStatus(expenseId, element) {
    // Verificar se o elemento existe
    if (!element) return;

    // Obter o status atual (boolean)
    const isPaid = element.getAttribute('data-is-paid') === 'true';

    // Exibir um indicador de carregamento
    const originalContent = element.querySelector('.badge').innerHTML;
    element.querySelector('.badge').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';

    // Enviar requisição AJAX para o servidor
    fetch(`/dashboard/despesas/toggle-payment/${expenseId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na requisição');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Atualizar a interface com o novo status
            updatePaymentStatus(element, !isPaid);

            // Mostrar mensagem de sucesso
            showAlert('Status de pagamento atualizado com sucesso!', 'success');
            
            // Atualizar os totais se fornecidos na resposta
            updateTotals(data);
        } else {
            throw new Error(data.error || 'Não foi possível atualizar o status da despesa');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        
        // Restaurar conteúdo original
        element.querySelector('.badge').innerHTML = originalContent;
        
        // Mostrar mensagem de erro
        showAlert('Erro ao atualizar status de pagamento. Tente novamente.', 'danger');
    });
}

// Função para atualizar visualmente o status de pagamento
function updatePaymentStatus(element, isPaid) {
    const badge = element.querySelector('.badge');
    const tooltipText = element.querySelector('.tooltip-text');
    
    // Atualizar o atributo data-is-paid
    element.setAttribute('data-is-paid', isPaid);
    
    if (isPaid) {
        // Atualizar para pago
        badge.className = 'badge rounded-pill bg-success d-flex align-items-center justify-content-center';
        badge.innerHTML = '<i class="fas fa-check-circle me-1"></i> Pago <i class="fas fa-exchange-alt ms-2"></i>';
        tooltipText.textContent = 'Clique para marcar como "Não Pago"';
    } else {
        // Atualizar para não pago
        badge.className = 'badge rounded-pill bg-warning text-dark d-flex align-items-center justify-content-center';
        badge.innerHTML = '<i class="fas fa-clock me-1"></i> Pendente <i class="fas fa-exchange-alt ms-2"></i>';
        tooltipText.textContent = 'Clique para marcar como "Pago"';
    }
    
    // Adicionar animação de atualização
    badge.classList.add('text-pulse');
    setTimeout(() => {
        badge.classList.remove('text-pulse');
    }, 1500);
}

// Função para excluir uma despesa
function deleteExpense(expenseId) {
    if (!confirm('Tem certeza que deseja excluir esta despesa?')) {
        return;
    }
    
    // Enviar requisição AJAX para excluir a despesa
    fetch(`/dashboard/despesas/excluir/${expenseId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na requisição');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Encontrar e remover a linha da tabela
            const row = document.querySelector(`button[data-expense-id="${expenseId}"]`).closest('tr');
            row.classList.add('fade-out');
            
            setTimeout(() => {
                row.remove();
                
                // Verificar se não há mais despesas
                const tbody = document.querySelector('.table tbody');
                if (tbody && tbody.children.length === 0) {
                    // Mostrar mensagem de "sem despesas"
                    showNoExpensesMessage();
                }
                
                // Mostrar mensagem de sucesso
                showAlert('Despesa excluída com sucesso!', 'success');
                
                // Atualizar os totais se fornecidos na resposta
                updateTotals(data);
            }, 300);
        } else {
            throw new Error(data.error || 'Não foi possível excluir a despesa');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showAlert('Erro ao excluir despesa. Tente novamente.', 'danger');
    });
}

// Função para atualizar totais após mudanças nas despesas
function updateTotals(data) {
    if (!data) return;
    
    console.log('Dados recebidos para atualização:', data);
    
    // Atualizar valores totais se fornecidos na resposta
    if (data.total_expenses !== undefined) {
        const totalExpensesElement = document.querySelector('.summary-card.danger h3');
        if (totalExpensesElement) {
            totalExpensesElement.innerHTML = `R$ ${formatCurrency(data.total_expenses)}`;
            totalExpensesElement.classList.add('text-pulse');
            setTimeout(() => totalExpensesElement.classList.remove('text-pulse'), 1500);
        }
    }
    
    // Atualizar despesas pagas e pendentes
    if (data.paid_expenses !== undefined) {
        const paidExpensesElement = document.getElementById('paid-expenses-value');
        if (paidExpensesElement) {
            paidExpensesElement.textContent = formatCurrency(data.paid_expenses);
            paidExpensesElement.classList.add('text-pulse');
            setTimeout(() => paidExpensesElement.classList.remove('text-pulse'), 1500);
        }
        
        // Calcular e atualizar despesas pendentes
        if (data.total_expenses !== undefined) {
            const pendingExpensesElement = document.getElementById('pending-expenses-value');
            if (pendingExpensesElement) {
                const pendingExpenses = data.total_expenses - data.paid_expenses;
                pendingExpensesElement.textContent = formatCurrency(pendingExpenses);
                pendingExpensesElement.classList.add('text-pulse');
                setTimeout(() => pendingExpensesElement.classList.remove('text-pulse'), 1500);
            }
        }
    }
    
    // Atualizar percentual de pagamento
    if (data.payment_percentage !== undefined) {
        const paymentPercentageText = document.querySelector('.summary-card.danger .d-flex.justify-content-between span:last-child');
        const paymentPercentageBar = document.querySelector('.summary-card.danger .progress .progress-bar');
        
        if (paymentPercentageText && paymentPercentageBar) {
            const percentage = `${Math.round(data.payment_percentage)}%`;
            paymentPercentageText.textContent = percentage;
            paymentPercentageBar.style.width = percentage;
            paymentPercentageBar.setAttribute('aria-valuenow', data.payment_percentage);
            
            // Animar a barra de progresso
            paymentPercentageBar.classList.add('progress-bar-animated');
            setTimeout(() => {
                paymentPercentageBar.classList.remove('progress-bar-animated');
            }, 1500);
            
            // Destacar o card de despesas
            const expenseCard = document.querySelector('.summary-card.danger');
            if (expenseCard) {
                expenseCard.classList.add('highlight-update');
                setTimeout(() => {
                    expenseCard.classList.remove('highlight-update');
                }, 1500);
            }
        }
    }
    
    // Atualizar lucro bruto antes das despesas
    if (data.products_profit !== undefined) {
        const profitValueElement = document.getElementById('profit-value');
        if (profitValueElement) {
            profitValueElement.textContent = formatCurrency(data.products_profit);
            profitValueElement.classList.add('text-pulse');
            setTimeout(() => profitValueElement.classList.remove('text-pulse'), 1500);
        }
        
        // Atualizar percentual de margem de produto se disponível
        if (data.products_profit_percentage !== undefined) {
            const productsProfitPercentageText = document.getElementById('product-margin-percentage');
            if (productsProfitPercentageText) {
                productsProfitPercentageText.textContent = `${Math.round(data.products_profit_percentage)}%`;
                productsProfitPercentageText.classList.add('text-pulse');
                setTimeout(() => productsProfitPercentageText.classList.remove('text-pulse'), 1500);
            }
        }
    }
    
    // Atualizar lucro descontado (após as despesas)
    if (data.total_profit !== undefined) {
        const profitElement = document.getElementById('discounted-profit-value');
        if (profitElement) {
            profitElement.textContent = formatCurrency(data.total_profit);
            profitElement.classList.add('text-pulse');
            setTimeout(() => profitElement.classList.remove('text-pulse'), 1500);
            
            // Atualizar também a cor do card com base no valor do lucro
            updateProfitCardStyle(data.total_profit);
            
            // Adicionar efeito de trajetória do botão de pagamento para o card de lucro
            animatePaymentImpact();
        }
    }
    
    // Atualizar percentual de lucro
    if (data.profit_margin !== undefined) {
        const profitMarginText = document.querySelector('.summary-card.profit-card .d-flex.justify-content-between span:last-child');
        const profitMarginBar = document.querySelector('.summary-card.profit-card .progress .progress-bar');
        
        if (profitMarginText && profitMarginBar) {
            const profitMarginAbs = Math.abs(data.profit_margin);
            const percentage = `${Math.round(profitMarginAbs)}%`;
            profitMarginText.textContent = percentage;
            profitMarginBar.style.width = percentage;
            profitMarginBar.setAttribute('aria-valuenow', profitMarginAbs);
            
            // Animar a barra de progresso
            profitMarginBar.classList.add('progress-bar-animated');
            setTimeout(() => {
                profitMarginBar.classList.remove('progress-bar-animated');
            }, 1500);
            
            // Destacar o card de lucro para chamar atenção para a mudança
            const profitCard = document.querySelector('.summary-card.profit-card');
            if (profitCard) {
                profitCard.classList.add('highlight-update');
                setTimeout(() => {
                    profitCard.classList.remove('highlight-update');
                }, 1500);
            }
        }
    }
    
    // Atualizar totais de receita se disponível
    if (data.total_revenue !== undefined) {
        const revenueElement = document.getElementById('total-revenue-value');
        if (revenueElement) {
            revenueElement.textContent = formatCurrency(data.total_revenue);
            revenueElement.classList.add('text-pulse');
            setTimeout(() => revenueElement.classList.remove('text-pulse'), 1500);
        }
    }
}

// Função para atualizar o estilo do card de lucro com base no valor
function updateProfitCardStyle(totalProfit) {
    const profitCard = document.querySelector('.summary-card.profit-card');
    const progressBar = profitCard.querySelector('.progress-bar');
    
    if (!profitCard || !progressBar) return;
    
    // Remover classes existentes
    profitCard.classList.remove('negative-profit', 'low-profit', 'good-profit');
    progressBar.classList.remove('bg-danger', 'bg-warning', 'bg-success');
    
    if (totalProfit < 0) {
        // Lucro negativo (prejuízo)
        profitCard.classList.add('negative-profit');
        progressBar.classList.add('bg-danger');
    } else if (totalProfit >= 0 && totalProfit < 1000) {
        // Lucro baixo
        profitCard.classList.add('low-profit');
        progressBar.classList.add('bg-warning');
    } else {
        // Bom lucro
        profitCard.classList.add('good-profit');
        progressBar.classList.add('bg-success');
    }
}

// Função para animar o impacto do pagamento no card de lucro
function animatePaymentImpact(amount, isPaid) {
    const profitCard = document.querySelector('.card.profit-margin');
    if (!profitCard) return;
    
    const animation = document.createElement('div');
    animation.className = 'payment-impact-animation';
    
    // Define visual properties based on payment status
    if (isPaid) {
        animation.classList.add('positive');
        animation.textContent = '+R$ ' + amount.toFixed(2).replace('.', ',');
    } else {
        animation.classList.add('negative');
        animation.textContent = '-R$ ' + amount.toFixed(2).replace('.', ',');
    }
    
    // Append to the profit margin card
    profitCard.appendChild(animation);
    
    // Trigger animation
    setTimeout(() => {
        animation.classList.add('animate');
    }, 50);
    
    // Remove element after animation completes
    setTimeout(() => {
        animation.classList.remove('animate');
        setTimeout(() => {
            profitCard.removeChild(animation);
        }, 300);
    }, 2000);
}

// Formatar valores de moeda
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Exibir mensagem quando não há despesas
function showNoExpensesMessage() {
    const container = document.querySelector('.card-body');
    if (!container) return;
    
    // Remover tabela existente
    const table = container.querySelector('.table-responsive');
    if (table) table.remove();
    
    // Adicionar mensagem
    container.innerHTML = `
        <div class="text-center p-5">
            <div class="mb-4">
                <i class="fas fa-receipt text-muted" style="font-size: 4rem;"></i>
            </div>
            <h5 class="mb-3">Nenhuma despesa registrada neste mês</h5>
            <p class="mb-4 text-muted">Registre suas despesas para acompanhar seus gastos</p>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addExpenseModal">
                <i class="fas fa-plus me-2"></i> Adicionar Despesa
            </button>
        </div>
    `;
}

// Exibir alertas
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.setAttribute('role', 'alert');
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Inserir alerta no início da página
    const contentArea = document.querySelector('.container-fluid');
    if (contentArea) {
        const firstChild = contentArea.firstChild;
        contentArea.insertBefore(alertContainer, firstChild);
        
        // Remover após 5 segundos
        setTimeout(() => {
            alertContainer.classList.remove('show');
            setTimeout(() => alertContainer.remove(), 150);
        }, 5000);
    }
}

// Obter token CSRF
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return null;
}

// Inicialização quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Configurar evento de clique para todos os botões de exclusão de despesa
    document.querySelectorAll('.btn-delete-expense').forEach(button => {
        button.addEventListener('click', function() {
            const expenseId = this.getAttribute('data-expense-id');
            if (expenseId) {
                deleteExpense(expenseId);
            }
        });
    });
    
    // Adicionar estilo CSS para animação de remoção e outros efeitos visuais
    const style = document.createElement('style');
    style.textContent = `
        .fade-out {
            opacity: 0;
            transform: translateY(-10px);
            transition: opacity 0.3s, transform 0.3s;
        }

        .highlight-update {
            animation: card-highlight 1.5s ease;
        }

        @keyframes card-highlight {
            0% {
                box-shadow: 0 0 0 rgba(255, 255, 255, 0);
                transform: scale(1);
            }
            25% {
                box-shadow: 0 0 20px rgba(255, 255, 255, 0.6);
                transform: scale(1.03);
            }
            75% {
                box-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
                transform: scale(1.01);
            }
            100% {
                box-shadow: 0 0 0 rgba(255, 255, 255, 0);
                transform: scale(1);
            }
        }

        .text-pulse {
            animation: text-pulse 1.5s ease;
        }

        @keyframes text-pulse {
            0% {
                color: inherit;
            }
            25% {
                color: #ffffff;
                text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
            }
            100% {
                color: inherit;
            }
        }
        
        .payment-impact-animation {
            position: fixed;
            width: 20px;
            height: 20px;
            background: radial-gradient(circle, #ffffff 0%, #4CAF50 60%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transition: all 0.8s cubic-bezier(0.165, 0.84, 0.44, 1);
            opacity: 0.9;
        }
        
        .payment-impact-animation.animating {
            width: 10px;
            height: 10px;
            opacity: 0;
        }
        
        .progress-bar-animated {
            animation: progress-bar-stripes 1s linear infinite;
        }
        
        .card-updating {
            position: relative;
            overflow: hidden;
        }
        
        .card-updating::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 200%;
            height: 100%;
            background: linear-gradient(90deg, 
                transparent 0%, 
                rgba(255, 255, 255, 0.2) 25%, 
                rgba(255, 255, 255, 0.2) 50%, 
                transparent 100%);
            animation: card-shine 1.5s ease;
            pointer-events: none;
        }
        
        @keyframes card-shine {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .negative-profit {
            border-left: 4px solid #dc3545 !important;
        }
        
        .low-profit {
            border-left: 4px solid #ffc107 !important;
        }
        
        .good-profit {
            border-left: 4px solid #28a745 !important;
        }
    `;
    document.head.appendChild(style);

    // Adicionar ouvintes de eventos para botões de pagamento
    document.querySelectorAll('[data-is-paid]').forEach(element => {
        element.addEventListener('click', function() {
            const expenseId = this.getAttribute('data-expense-id');
            if (expenseId) {
                togglePaymentStatus(expenseId, this);
            }
        });
    });

    // Aplicar estilos iniciais aos cards
    const profitValue = parseFloat(document.getElementById('discounted-profit-value')?.textContent.replace(/[^\d,-]/g, '').replace(',', '.')) || 0;
    updateProfitCardStyle(profitValue);
});