/**
 * CORREÇÃO EMERGENCIAL - CLIQUE NOS PRODUTOS
 * Este arquivo deve ser incluído APÓS o pdv.js original
 */
(function() {
    console.log("Sistema PDV Inicializado - v1.0.3");
    
    // Função de depuração para elementos DOM
    function debugElemento(elemento, prefixo = "") {
        if (!elemento) {
            console.error(prefixo + " Elemento não encontrado");
            return;
        }
        
        console.log(prefixo, {
            id: elemento.id,
            tagName: elemento.tagName,
            classes: elemento.className,
            attributes: Array.from(elemento.attributes).map(attr => `${attr.name}="${attr.value}"`).join(', '),
            content: elemento.textContent?.trim().substring(0, 50) + (elemento.textContent?.length > 50 ? '...' : '')
        });
    }
    
    // Função para obter token CSRF
    function getCSRFToken() {
        // Tenta obter do input
        let token = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (token) return token.value;
        
        // Tenta obter do cookie
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        if (cookieValue) return cookieValue;
        
        // Tenta obter da meta tag
        token = document.querySelector('meta[name="csrf-token"]');
        if (token) return token.content;
        
        return null;
    }
    
    // Garantir que o token CSRF esteja presente
    function ensureCSRFToken() {
        let token = getCSRFToken();
        if (!token) {
            console.error("Token CSRF não encontrado! Criando um novo input...");
            
            // Tentar obter do cookie diretamente
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
                
            if (cookieValue) {
                console.log("Token CSRF encontrado no cookie:", cookieValue.substring(0, 5) + "...");
                
                // Criar input com o token
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrfmiddlewaretoken';
                input.value = cookieValue;
                
                // Verifica se há um formulário
                const form = document.querySelector('form');
                if (form) {
                    form.appendChild(input);
                    console.log("Input CSRF adicionado ao formulário existente.");
                } else {
                    // Adiciona ao body
                    document.body.appendChild(input);
                    console.log("Input CSRF adicionado ao body.");
                }
                
                return cookieValue;
            } else {
                console.error("CSRF token não pode ser encontrado nem mesmo nos cookies!");
                alert("Erro de segurança: Token CSRF não encontrado. A página será recarregada.");
                window.location.reload();
                return null;
            }
        } else {
            console.log("Token CSRF encontrado:", token.substring(0, 5) + "...");
            return token;
        }
    }
    
    // Função para adicionar ao carrinho via AJAX
    function adicionarAoCarrinhoAjax(produtoId, quantidade) {
        console.log(`Adicionando produto ID ${produtoId} com quantidade ${quantidade} ao carrinho`);
        
        // Validar parâmetros
        if (!produtoId || isNaN(parseInt(produtoId))) {
            console.error("ID de produto inválido:", produtoId);
            alert("Erro: ID de produto inválido.");
            return;
        }
        
        if (!quantidade || isNaN(parseInt(quantidade)) || parseInt(quantidade) <= 0) {
            console.warn("Quantidade inválida, definindo como 1:", quantidade);
            quantidade = 1;
        }
        
        // Garantir que temos o token CSRF
        const csrfToken = ensureCSRFToken();
        if (!csrfToken) {
            console.error("Não foi possível obter o token CSRF para enviar a requisição");
            return;
        }
        
        // Preparar dados
        const formData = new FormData();
        formData.append('produto_id', produtoId);
        formData.append('quantidade', quantidade);
        formData.append('csrfmiddlewaretoken', csrfToken);
        
        // Mostrar loading
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'alert alert-info text-center';
        loadingMessage.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Adicionando produto...';
        
        const cartItems = document.getElementById('cart-items');
        if (cartItems) {
            // Mostrar loading apenas se não houver itens
            if (cartItems.querySelector('.empty-cart') || cartItems.querySelector('#empty-cart-message')) {
                cartItems.innerHTML = '';
                cartItems.appendChild(loadingMessage);
            }
        }
        
        // Fazer requisição AJAX usando Fetch API
        fetch('/sistema/vendas/adicionar-item/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
                // Não definimos 'Content-Type' aqui porque o FormData configura automaticamente
            },
            body: formData,
            credentials: 'same-origin' // Importante para enviar cookies, incluindo o CSRF
        })
        .then(response => {
            console.log("Resposta recebida:", response.status);
            // Verificar o tipo de conteúdo da resposta
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json().then(data => {
                    return { isJson: true, data: data };
                });
            } else {
                return response.text().then(text => {
                    return { isJson: false, text: text };
                });
            }
        })
        .then(result => {
            // Fechar modal se estiver aberto
            const modalQuantidade = document.getElementById('modalQuantidade');
            if (modalQuantidade) {
                // Verificar se o Bootstrap está disponível
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const bsModal = bootstrap.Modal.getInstance(modalQuantidade);
                    if (bsModal) bsModal.hide();
                } else if (typeof jQuery !== 'undefined' && jQuery.fn.modal) {
                    // Fallback para jQuery
                    jQuery(modalQuantidade).modal('hide');
                } else {
                    // Fallback para manipulação direta de classes
                    modalQuantidade.classList.remove('show');
                    modalQuantidade.style.display = 'none';
                    document.body.classList.remove('modal-open');
                    
                    // Remove backdrop if exists
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) backdrop.remove();
                }
            }
            
            // Limpar o input de quantidade
            const quantityInput = document.getElementById('product-quantity');
            if (quantityInput) quantityInput.value = 1;
            
            // Atualizar carrinho de compras
            const cartItemsContainer = document.getElementById('cart-items') || 
                                       document.getElementById('items-cart-container') || 
                                       document.getElementById('itens_venda');
            
            if (cartItemsContainer) {
                console.log("Atualizando container de itens do carrinho:", cartItemsContainer.id);
                
                // Limpar mensagem de carrinho vazio se existir
                const emptyCartMessage = document.getElementById('empty-cart-message');
                if (emptyCartMessage) emptyCartMessage.style.display = 'none';
                
                if (result.isJson) {
                    // Processar resposta JSON
                    const data = result.data;
                    if (data.status === 'success') {
                        // Atualizar HTML do carrinho
                        if (data.html) {
                            cartItemsContainer.innerHTML = data.html;
                        } else if (data.items) {
                            // Renderizar itens manualmente se não tiver HTML pronto
                            let html = '';
                            data.items.forEach(item => {
                                html += `
                                    <div class="cart-item" data-id="${item.id}">
                                        <div class="d-flex justify-content-between">
                                            <div>
                                                <span class="item-quantity">${item.quantity}x</span>
                                                <span class="item-name">${item.name}</span>
                                            </div>
                                            <div class="text-end">
                                                <span class="item-price">R$ ${parseFloat(item.total).toFixed(2)}</span>
                                                <button class="btn btn-sm text-danger remove-item" 
                                                        onclick="removerItemCarrinho(${item.id})">
                                                    <i class="fas fa-times"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                `;
                            });
                            cartItemsContainer.innerHTML = html || '<div class="text-center py-3">Nenhum item no carrinho</div>';
                        }
                        
                        // Atualizar totais
                        if (data.subtotal) {
                            const subtotalElement = document.getElementById('subtotal');
                            if (subtotalElement) subtotalElement.textContent = `R$ ${parseFloat(data.subtotal).toFixed(2)}`;
                        }
                        
                        if (data.total) {
                            const totalElements = document.querySelectorAll('#total, #total-sale, #total_venda, .total-value');
                            totalElements.forEach(el => {
                                el.textContent = `R$ ${parseFloat(data.total).toFixed(2)}`;
                            });
                        }
                    } else {
                        console.error("Erro ao adicionar produto:", data.message);
                        alert("Erro: " + (data.message || "Não foi possível adicionar o produto ao carrinho."));
                    }
                } else {
                    // Resposta não é JSON, tratar como HTML
                    console.log("Resposta recebida como HTML/texto");
                    
                    // Tentar atualizar o carrinho com o HTML retornado
                    try {
                        cartItemsContainer.innerHTML = result.text;
                        
                        // Mostrar mensagem de sucesso
                        const successMessage = document.createElement('div');
                        successMessage.className = 'alert alert-success position-fixed top-0 end-0 m-3';
                        successMessage.innerHTML = '<i class="fas fa-check-circle me-2"></i>Produto adicionado ao carrinho!';
                        successMessage.style.zIndex = '9999';
                        document.body.appendChild(successMessage);
                        
                        // Remover mensagem após 3 segundos
                        setTimeout(() => {
                            successMessage.remove();
                        }, 3000);
                    } catch (error) {
                        console.error("Erro ao processar resposta HTML:", error);
                        
                        // Recarregar a página como último recurso
                        alert("Produto adicionado, atualizando a página...");
                        window.location.reload();
                    }
                }
            } else {
                console.warn("Container de itens do carrinho não encontrado");
                
                // Recarregar a página como fallback
                console.log("Recarregando página...");
                window.location.reload();
            }
        })
        .catch(error => {
            console.error("Erro na requisição:", error);
            
            // Fechar modal se estiver aberto
            const modalQuantidade = document.getElementById('modalQuantidade');
            if (modalQuantidade) {
                try {
                    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                        const bsModal = bootstrap.Modal.getInstance(modalQuantidade);
                        if (bsModal) bsModal.hide();
                    }
                } catch (e) {
                    console.error("Erro ao fechar modal:", e);
                }
            }
            
            // Tentar recarregar a página em caso de erro
            if (confirm("Erro ao adicionar produto ao carrinho. Deseja recarregar a página?")) {
                window.location.reload();
            }
        });
    }
    
    // Configurar botão Adicionar ao Carrinho
    function setupAddToCartButton() {
        console.log("Configurando botão de Adicionar ao Carrinho");
        
        const addToCartButton = document.getElementById('add-to-cart') ||
                               document.getElementById('add-to-cart-button') ||
                               document.querySelector('.add-to-cart-button') ||
                               document.querySelector('[data-action="add-to-cart"]');
        
        if (addToCartButton) {
            // Clonar e substituir para remover eventos anteriores
            const newButton = addToCartButton.cloneNode(true);
            addToCartButton.parentNode.replaceChild(newButton, addToCartButton);
            
            // Adicionar novo evento
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Obter o ID do produto diretamente do atributo data-id do botão
                const produtoId = this.getAttribute('data-id');
                
                // Obter a quantidade do input
                const quantidadeInput = document.getElementById('product-quantity');
                const quantidade = quantidadeInput ? quantidadeInput.value : 1;
                
                if (!produtoId) {
                    console.error("ID de produto não encontrado no botão!");
                    alert("Erro: Não foi possível identificar o produto.");
                    return;
                }
                
                console.log("Adicionando ao carrinho produto ID:", produtoId, "Quantidade:", quantidade);
                adicionarAoCarrinhoAjax(produtoId, quantidade);
            });
            
            console.log("Evento click configurado para o botão Adicionar ao Carrinho");
        } else {
            console.warn("Botão 'Adicionar ao Carrinho' não encontrado!");
        }
    }
    
    // Configurar cliques nos produtos
    function setupProductClicks() {
        console.log("Configurando cliques nos produtos");
        
        // Registra todos os modais disponíveis para diagnóstico
        const todosModais = document.querySelectorAll('.modal');
        console.log(`Total de modais encontrados: ${todosModais.length}`);
        todosModais.forEach(modal => {
            console.log(`Modal encontrado: ID=${modal.id}, Classes=${modal.className}`);
        });
        
        // Verificar se o modal de quantidade existe
        const modalQuantidade = document.getElementById('modalQuantidade');
        if (modalQuantidade) {
            console.log("Modal de quantidade encontrado:", modalQuantidade.id);
            debugElemento(modalQuantidade, "Modal de quantidade:");
        } else {
            console.error("Modal de quantidade NÃO encontrado! Verificar ID correto no HTML.");
        }
        
        // Tenta diferentes seletores para encontrar os produtos
        const produtoItems = document.querySelectorAll('.produto-item, tr.product-item, .product-card, [data-produto-id], [data-id]');
        
        if (produtoItems.length > 0) {
            console.log(`Encontrados ${produtoItems.length} produtos na página`);
            
            produtoItems.forEach(item => {
                // Clonar e substituir para remover eventos anteriores
                const newItem = item.cloneNode(true);
                item.parentNode.replaceChild(newItem, item);
                
                newItem.addEventListener('click', function(e) {
                    // Evitar que clique em links ou botões dentro do item dispare a ação
                    if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                        return;
                    }
                    
                    // Extração cuidadosa do ID do produto
                    let produtoId = null;
                    
                    // Tentar obter do atributo data-id primeiro (mais comum)
                    produtoId = this.getAttribute('data-id');
                    
                    // Se não encontrou, tentar outros atributos comuns
                    if (!produtoId) {
                        produtoId = this.getAttribute('data-produto-id') || 
                                    this.getAttribute('data-product-id') ||
                                    this.getAttribute('id')?.replace(/[^0-9]/g, '');
                    }
                    
                    // Se ainda não encontrou, procurar em elementos filhos
                    if (!produtoId) {
                        const idElement = this.querySelector('[data-id], [data-produto-id], [data-product-id]');
                        if (idElement) {
                            produtoId = idElement.getAttribute('data-id') || 
                                        idElement.getAttribute('data-produto-id') || 
                                        idElement.getAttribute('data-product-id');
                        }
                    }
                    
                    // Outros atributos para extração do produto
                    const produtoNome = this.getAttribute('data-nome') || 
                                       this.getAttribute('data-name') ||
                                       this.querySelector('.produto-nome, .product-name')?.textContent.trim();
                    
                    const produtoPreco = this.getAttribute('data-preco') || 
                                        this.getAttribute('data-price') ||
                                        this.querySelector('.produto-preco, .product-price')?.textContent.trim();
                    
                    const produtoEstoque = this.getAttribute('data-estoque') || 
                                          this.getAttribute('data-stock') ||
                                          this.querySelector('.produto-estoque, .product-stock')?.textContent.trim();
                    
                    console.log("Produto clicado:", {
                        id: produtoId,
                        nome: produtoNome,
                        preco: produtoPreco,
                        estoque: produtoEstoque
                    });
                    
                    if (!produtoId) {
                        console.error("ID do produto não encontrado no elemento clicado");
                        alert("Erro: Não foi possível identificar o produto. Por favor, tente outro produto ou recarregue a página.");
                        return;
                    }
                    
                    // Verificar estoque
                    if (produtoEstoque !== undefined && parseInt(produtoEstoque) <= 0) {
                        console.warn("Produto sem estoque!");
                        
                        // Usar SweetAlert se disponível, senão alert padrão
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                title: 'Produto Indisponível',
                                text: 'Este produto está sem estoque no momento.',
                                icon: 'warning',
                                confirmButtonText: 'OK'
                            });
                        } else {
                            alert('Produto sem estoque!');
                        }
                        return;
                    }
                    
                    // Verificar se o modal existe e está acessível
                    const modalQuantidade = document.getElementById('modalQuantidade');
                    
                    if (modalQuantidade) {
                        console.log("Modal encontrado, preparando para abrir");
                        
                        // Encontrar elementos do modal
                        const modalTitle = document.getElementById('modal-product-name') || 
                                         document.querySelector('#modalQuantidade .modal-title');
                        const addToCartBtn = document.getElementById('add-to-cart');
                        const quantidadeInput = document.getElementById('product-quantity');
                        
                        // Preencher dados no modal
                        if (modalTitle && produtoNome) {
                            modalTitle.textContent = produtoNome;
                        }
                        
                        // Configurar botão de adicionar ao carrinho com os dados do produto
                        if (addToCartBtn) {
                            addToCartBtn.setAttribute('data-id', produtoId);
                            addToCartBtn.setAttribute('data-name', produtoNome || '');
                            addToCartBtn.setAttribute('data-price', produtoPreco || '0');
                            console.log("Botão add-to-cart configurado com ID:", produtoId);
                        } else {
                            console.error("Botão add-to-cart não encontrado no modal");
                        }
                        
                        // Atualizar outros elementos do modal
                        const modalProductPrice = document.getElementById('modal-product-price');
                        if (modalProductPrice && produtoPreco) {
                            // Limpar o valor para garantir formatação consistente
                            const precoLimpo = produtoPreco.replace(/[^\d,.]/g, '').replace(',', '.');
                            modalProductPrice.textContent = `R$ ${parseFloat(precoLimpo).toFixed(2)}`;
                        }
                        
                        const modalProductStock = document.getElementById('modal-product-stock');
                        if (modalProductStock && produtoEstoque) {
                            modalProductStock.textContent = produtoEstoque;
                        }
                        
                        if (quantidadeInput) {
                            quantidadeInput.value = "1";
                            // Focar no input após abrir o modal
                            setTimeout(() => {
                                quantidadeInput.focus();
                                quantidadeInput.select();
                            }, 500);
                        }
                        
                        // Abrir o modal - tenta diferentes métodos
                        try {
                            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                                console.log("Abrindo modal via Bootstrap");
                                const modal = new bootstrap.Modal(modalQuantidade);
                                modal.show();
                            } else if (typeof $ !== 'undefined' && $.fn && $.fn.modal) {
                                console.log("Abrindo modal via jQuery");
                                $(modalQuantidade).modal('show');
                            } else {
                                // Fallback para CSS
                                console.log("Abrindo modal via CSS");
                                modalQuantidade.style.display = 'block';
                                modalQuantidade.classList.add('show');
                                document.body.classList.add('modal-open');
                                
                                // Adicionar backdrop se não existir
                                if (!document.querySelector('.modal-backdrop')) {
                                    const backdrop = document.createElement('div');
                                    backdrop.className = 'modal-backdrop show';
                                    document.body.appendChild(backdrop);
                                }
                            }
                        } catch (e) {
                            console.error("Erro ao abrir modal:", e);
                            // Se falhar ao abrir o modal, adiciona diretamente ao carrinho
                            if (confirm("Não foi possível abrir o modal. Deseja adicionar o produto diretamente ao carrinho com quantidade 1?")) {
                                adicionarAoCarrinhoAjax(produtoId, 1);
                            }
                        }
                    } else {
                        console.error("Modal de quantidade não encontrado! Adicionando diretamente ao carrinho.");
                        // Se não houver modal, adicionar diretamente ao carrinho
                        if (confirm("Modal não encontrado. Deseja adicionar o produto diretamente ao carrinho com quantidade 1?")) {
                            adicionarAoCarrinhoAjax(produtoId, 1);
                        }
                    }
                });
            });
            
            console.log("Eventos de clique configurados para todos os produtos");
        } else {
            console.warn("Nenhum produto encontrado na página para configurar cliques!");
            
            // Tenta encontrar produtos com outros seletores
            const altProdutos = document.querySelectorAll('[data-product], .item-produto, .produto');
            if (altProdutos.length > 0) {
                console.log(`Encontrados ${altProdutos.length} produtos com seletores alternativos`);
                
                altProdutos.forEach(item => {
                    // Adicionar evento de clique
                    item.addEventListener('click', function() {
                        const produtoId = this.getAttribute('data-id') || this.getAttribute('id')?.replace('produto-', '');
                        if (produtoId) {
                            console.log("Produto alternativo clicado, ID:", produtoId);
                            // Adicionar diretamente ao carrinho para garantir funcionalidade
                            adicionarAoCarrinhoAjax(produtoId, 1);
                        }
                    });
                });
            }
        }
    }
    
    // Configurar entrada de quantidade
    function setupQuantityInput() {
        console.log("Configurando input de quantidade");
        
        const quantityInput = document.getElementById('product-quantity');
        if (quantityInput) {
            // Clonar e substituir para remover eventos anteriores
            const newInput = quantityInput.cloneNode(true);
            quantityInput.parentNode.replaceChild(newInput, quantityInput);
            
            // Adicionar evento de tecla Enter
            newInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    
                    const addToCartButton = document.getElementById('add-to-cart') || 
                                          document.getElementById('add-to-cart-button') ||
                                          document.querySelector('.add-to-cart-button') ||
                                          document.querySelector('[data-action="add-to-cart"]');
                    
                    if (addToCartButton) {
                        console.log("Simulando clique no botão adicionar ao carrinho");
                        addToCartButton.click();
                    } else {
                        console.warn("Botão 'Adicionar ao Carrinho' não encontrado para simular clique");
                        
                        // Tenta adicionar diretamente ao carrinho
                        const produtoId = document.querySelector('#modalQuantidade [data-id]')?.getAttribute('data-id');
                        if (produtoId) {
                            adicionarAoCarrinhoAjax(produtoId, this.value);
                        } else {
                            console.error("Não foi possível determinar o ID do produto");
                        }
                    }
                }
            });
            
            // Configurar botões de incremento/decremento
            const decreaseBtn = document.getElementById('decrease-qty');
            const increaseBtn = document.getElementById('increase-qty');
            
            if (decreaseBtn) {
                decreaseBtn.addEventListener('click', function() {
                    const currentVal = parseInt(newInput.value) || 1;
                    newInput.value = Math.max(1, currentVal - 1);
                });
            }
            
            if (increaseBtn) {
                increaseBtn.addEventListener('click', function() {
                    const currentVal = parseInt(newInput.value) || 0;
                    newInput.value = currentVal + 1;
                });
            }
            
            console.log("Evento keydown e botões de quantidade configurados");
        } else {
            console.warn("Input de quantidade 'product-quantity' não encontrado!");
        }
    }
    
    // Configurar o formulário de pagamento
    function setupPaymentForm() {
        console.log("Configurando formulário de pagamento");
        
        // Elementos do formulário de pagamento
        let paymentMethodSelect = document.getElementById('metodo_pagamento');
        let cashPaymentSection = document.getElementById('change-container');
        
        // Tenta encontrar por outros seletores se não encontrar pelo ID padrão
        if (!paymentMethodSelect) {
            paymentMethodSelect = document.querySelector('.payment-method-select, [name="payment_method"], #payment-method');
            console.log("Método de pagamento alternativo encontrado:", paymentMethodSelect ? "Sim" : "Não");
        }
        
        if (!cashPaymentSection) {
            cashPaymentSection = document.querySelector('.cash-payment, #payment-cash-section, #cash-payment-section');
            console.log("Seção de pagamento em dinheiro alternativa encontrada:", cashPaymentSection ? "Sim" : "Não");
        }
        
        if (paymentMethodSelect) {
            console.log("Método de pagamento inicial:", paymentMethodSelect.value);
            debugElemento(paymentMethodSelect, "Select de método de pagamento:");
            
            // Mostrar/esconder seção de pagamento em dinheiro com base no método selecionado
            function updateCashPaymentVisibility() {
                const selectedMethod = paymentMethodSelect.value;
                console.log("Método de pagamento selecionado:", selectedMethod);
                
                if (cashPaymentSection) {
                    if (selectedMethod === 'dinheiro' || selectedMethod === 'cash' || selectedMethod === '1') {
                        cashPaymentSection.style.display = 'block';
                        console.log("Mostrando seção de pagamento em dinheiro");
                    } else {
                        cashPaymentSection.style.display = 'none';
                        console.log("Ocultando seção de pagamento em dinheiro");
                    }
                } else {
                    console.warn("Seção de pagamento em dinheiro não encontrada");
                }
            }
            
            // Configurar evento de mudança
            paymentMethodSelect.addEventListener('change', updateCashPaymentVisibility);
            
            // Chamar imediatamente para configurar o estado inicial
            updateCashPaymentVisibility();
            
            // Configurar cálculo de troco
            calcularTroco();
        } else {
            console.warn("Select de método de pagamento não encontrado");
        }
    }
    
    // Calcular troco com base no valor pago
    function calcularTroco() {
        console.log("Configurando cálculo de troco");
        
        const paymentInput = document.getElementById('payment-amount');
        
        if (!paymentInput) {
            console.warn("Input de valor pago não encontrado");
            return;
        }
        
        paymentInput.addEventListener('input', function() {
            // Obter o valor total da venda
            const totalElement = document.getElementById('total-sale') || 
                                document.getElementById('total_venda') ||
                                document.getElementById('cart-total');
            
            if (!totalElement) {
                console.warn("Elemento de total da venda não encontrado");
                return;
            }
            
            console.log("Total da venda (elemento):", totalElement.textContent);
            
            // Extrair valor numérico do total (removendo R$ e outros caracteres)
            const totalText = totalElement.textContent.replace(/[^\d,.]/g, '').replace(',', '.');
            const totalValue = parseFloat(totalText);
            
            console.log("Total da venda (valor):", totalValue);
            
            // Obter valor pago
            const amountPaid = parseFloat(this.value) || 0;
            console.log("Valor pago:", amountPaid);
            
            // Calcular troco
            const change = amountPaid - totalValue;
            console.log("Troco calculado:", change);
            
            // Exibir troco
            const changeElement = document.getElementById('change-amount') || 
                                 document.getElementById('troco') ||
                                 document.querySelector('.change-display');
            
            if (changeElement) {
                // Se o troco for negativo, mostrar quanto falta para completar o pagamento
                if (change < 0) {
                    changeElement.textContent = `Faltam R$ ${Math.abs(change).toFixed(2)}`;
                    changeElement.style.color = 'red';
                } else {
                    changeElement.textContent = `R$ ${change.toFixed(2)}`;
                    changeElement.style.color = 'green';
                }
            } else {
                console.warn("Elemento de exibição de troco não encontrado");
            }
        });
        
        console.log("Evento de cálculo de troco configurado");
    }
    
    // Função para buscar produtos pelo código/nome
    function buscarProdutos(termo) {
        console.log("Buscando produtos com termo:", termo);
        
        // Obter todos os produtos da tabela
        const produtos = Array.from(document.querySelectorAll('#products-grid tbody tr.product-item'));
        console.log(`Total de produtos disponíveis: ${produtos.length}`);
        
        // Verificar se o termo de busca é curto (menos de 3 caracteres)
        const termoCurto = termo.length < 3;
        let resultados = [];
        
        // Para termos curtos, buscamos apenas correspondência exata de código
        if (termoCurto) {
            console.log("Termo curto, buscando apenas correspondência exata de código");
            resultados = produtos.filter(p => p.getAttribute('data-code') === termo);
        } else {
            // Para termos longos, buscamos correspondência parcial em código ou nome
            console.log("Termo longo, buscando correspondências parciais");
            
            // Primeiro tenta buscar por correspondência exata do código
            const correspondenciaExata = produtos.find(p => p.getAttribute('data-code') === termo);
            if (correspondenciaExata) {
                resultados = [correspondenciaExata];
            } else {
                // Busca por nome exato (ignorando maiúsculas/minúsculas)
                const correspondenciaNomeExato = produtos.find(p => 
                    p.getAttribute('data-name').toLowerCase() === termo.toLowerCase()
                );
                
                if (correspondenciaNomeExato) {
                    resultados = [correspondenciaNomeExato];
                } else {
                    // Busca parcial em código ou nome
                    resultados = produtos.filter(p => 
                        p.getAttribute('data-code').includes(termo) || 
                        p.getAttribute('data-name').toLowerCase().includes(termo.toLowerCase())
                    );
                }
            }
        }
        
        console.log(`Produtos encontrados: ${resultados.length}`);
        return resultados;
    }
    
    // Função para mostrar modal de seleção de produtos quando múltiplos são encontrados
    function mostrarModalSelecaoProdutos(produtos) {
        console.log("Mostrando modal de seleção com", produtos.length, "produtos");
        
        // Verificar se a biblioteca SweetAlert2 está disponível
        if (typeof Swal === 'undefined') {
            alert('Múltiplos produtos encontrados. Por favor, digite um código mais específico.');
            return;
        }
        
        // Criar HTML da lista de produtos
        let htmlProdutos = '<div class="list-group">';
        produtos.forEach(produto => {
            const id = produto.getAttribute('data-id');
            const nome = produto.getAttribute('data-name');
            const codigo = produto.getAttribute('data-code');
            const preco = parseFloat(produto.getAttribute('data-price').replace(',', '.')).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            
            htmlProdutos += `
                <button type="button" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center produto-opcao" data-id="${id}">
                    <div>
                        <strong>${nome}</strong>
                        <br><small class="text-muted">Código: ${codigo}</small>
                    </div>
                    <span class="badge bg-primary rounded-pill">${preco}</span>
                </button>
            `;
        });
        htmlProdutos += '</div>';
        
        // Exibir o modal com a lista de produtos
        Swal.fire({
            title: 'Selecione um Produto',
            html: htmlProdutos,
            showConfirmButton: false,
            showCancelButton: true,
            cancelButtonText: 'Cancelar',
            focusCancel: true,
            didOpen: () => {
                // Adicionar eventos de clique aos produtos listados
                document.querySelectorAll('.produto-opcao').forEach(opcao => {
                    opcao.addEventListener('click', () => {
                        const produtoId = opcao.getAttribute('data-id');
                        const produtoSelecionado = produtos.find(p => p.getAttribute('data-id') === produtoId);
                        
                        if (produtoSelecionado) {
                            // Fechar o modal
                            Swal.close();
                            
                            // Selecionar o produto (dispara um clique no produto)
                            produtoSelecionado.click();
                        }
                    });
                });
            }
        });
    }
    
    // Configurar campo de busca de produtos
    function setupProductSearchField() {
        console.log("Configurando campo de busca de produtos");
        
        const codigoProdutoInput = document.getElementById('codigo_produto');
        if (!codigoProdutoInput) {
            console.warn("Campo de busca de produtos não encontrado");
            return;
        }
        
        // Remover eventos existentes clonando o elemento
        const newInput = codigoProdutoInput.cloneNode(true);
        codigoProdutoInput.parentNode.replaceChild(newInput, codigoProdutoInput);
        
        // Adicionar evento para a tecla Enter
        newInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const termo = this.value.trim();
                
                if (!termo) {
                    alert("Digite um código ou nome de produto para buscar");
                    return;
                }
                
                console.log("Buscando produtos com termo:", termo);
                const produtosEncontrados = buscarProdutos(termo);
                
                if (produtosEncontrados.length === 0) {
                    // Nenhum produto encontrado
                    if (termo.length < 3) {
                        Swal.fire({
                            icon: 'info',
                            title: 'Código muito curto',
                            text: 'Para códigos curtos, certifique-se de digitar o código exato do produto.',
                            confirmButtonText: 'OK'
                        });
                    } else {
                        Swal.fire('Produto não encontrado', 'Verifique o código ou nome digitado.', 'info');
                    }
                } else if (produtosEncontrados.length === 1) {
                    // Um único produto encontrado - simular clique nele
                    produtosEncontrados[0].click();
                } else {
                    // Múltiplos produtos encontrados - mostrar modal de seleção
                    mostrarModalSelecaoProdutos(produtosEncontrados);
                }
            }
        });
        
        console.log("Campo de busca de produtos configurado");
    }
    
    // Inicialização
    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOM carregado, inicializando sistema PDV...");
        
        // Garantir token CSRF
        ensureCSRFToken();
        
        // Configurar componentes
        setupProductClicks();
        setupQuantityInput();
        setupAddToCartButton();
        setupPaymentForm();
        setupProductSearchField(); // Adicionar configuração do campo de busca
        
        console.log("Sistema PDV inicializado com sucesso!");
    });
})(); 