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
    
    // Função para calcular totais do carrinho
    function calcularTotaisCarrinho() {
        console.log("Calculando totais do carrinho");
        
        try {
            // Encontrar o contêiner dos itens do carrinho
            const cartItemsContainer = document.getElementById('cart-items') || 
                                      document.getElementById('items-cart-container') || 
                                      document.getElementById('itens_venda');
            
            if (!cartItemsContainer) {
                console.warn("Container de itens do carrinho não encontrado");
                return false;
            }
            
            // Encontrar todos os itens do carrinho
            const cartItems = cartItemsContainer.querySelectorAll('.cart-item, .item-carrinho, tr.item');
            console.log(`Encontrados ${cartItems.length} itens no carrinho`);
            
            if (cartItems.length === 0) {
                // Carrinho vazio, definir totais como zero
                atualizarTotaisInterface(0);
                return true;
            }
            
            // Calcular o subtotal somando os valores de todos os itens
            let subtotal = 0;
            
            cartItems.forEach(item => {
                // Tenta encontrar o preço total do item em diferentes possíveis elementos
                const precoText = item.querySelector('.item-price, .preco, .subtotal, td.subtotal')?.textContent || '0';
                
                // Limpar o texto do preço (remover R$, vírgulas, etc.)
                const precoLimpo = precoText.replace(/[^\d,.]/g, '').replace(',', '.');
                const preco = parseFloat(precoLimpo) || 0;
                
                console.log(`Item encontrado com preço: ${preco}`);
                subtotal += preco;
            });
            
            console.log(`Subtotal calculado: R$${subtotal.toFixed(2)}`);
            
            // Verificar desconto
            const descontoInput = document.getElementById('desconto');
            let desconto = 0;
            
            if (descontoInput) {
                desconto = parseFloat(descontoInput.value) || 0;
            }
            
            console.log(`Desconto aplicado: R$${desconto.toFixed(2)}`);
            
            // Calcular total final
            const total = Math.max(0, subtotal - desconto);
            console.log(`Total final calculado: R$${total.toFixed(2)}`);
            
            // Atualizar a interface
            atualizarTotaisInterface(subtotal, desconto, total);
            
            return true;
        } catch (e) {
            console.error("Erro ao calcular totais do carrinho:", e);
            return false;
        }
    }
    
    // Função para atualizar os totais na interface
    function atualizarTotaisInterface(subtotal, desconto = 0, total = null) {
        // Se total não for fornecido, assume que é igual ao subtotal menos desconto
        if (total === null) {
            total = Math.max(0, subtotal - desconto);
        }
        
        // Formatar valores para exibição
        const subtotalFormatado = `R$ ${subtotal.toFixed(2)}`;
        const totalFormatado = `R$ ${total.toFixed(2)}`;
        
        // Atualizar o subtotal
        const subtotalElement = document.getElementById('subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = subtotalFormatado;
        }
        
        // Atualizar o total em todos os possíveis elementos
        const totalElements = document.querySelectorAll('#total, #total-sale, #total_venda, .total-value');
        totalElements.forEach(el => {
            el.textContent = totalFormatado;
        });
        
        console.log(`Interface atualizada: Subtotal=${subtotalFormatado}, Total=${totalFormatado}`);
        
        // Verificar se o cálculo de troco deve ser atualizado
        const paymentInput = document.getElementById('payment-amount');
        if (paymentInput && paymentInput.value) {
            // Simular um evento de input para recalcular o troco
            const event = new Event('input', { bubbles: true });
            paymentInput.dispatchEvent(event);
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
                        
                        // Atualizar totais diretamente com os valores da resposta
                        if (data.subtotal) {
                            const subtotal = parseFloat(data.subtotal);
                            const total = parseFloat(data.total || data.subtotal);
                            atualizarTotaisInterface(subtotal, 0, total);
                        } else {
                            // Se não houver valores na resposta, calcular
                            calcularTotaisCarrinho();
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
                        
                        // Calcular totais após atualizar o HTML
                        setTimeout(calcularTotaisCarrinho, 100);
                        
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
    
    // Função para verificar se o modal existe e criá-lo caso não exista
    function garantirModalQuantidade() {
        console.log("Verificando se o modal de quantidade existe...");
        
        let modalQuantidade = document.getElementById('modalQuantidade');
        
        if (!modalQuantidade) {
            console.warn("Modal de quantidade não encontrado no DOM! Tentando criar...");
            
            // Criar o modal de quantidade dinamicamente
            const modalHTML = `
                <div class="modal fade" id="modalQuantidade" tabindex="-1" aria-hidden="true" data-bs-backdrop="static">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="modal-product-name">Nome do Produto</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <form id="add-to-cart-form">
                                <div class="modal-body">
                                    <p class="mb-3">Preço: <span class="fw-bold" id="modal-product-price">R$ 0,00</span></p>
                                    <p class="mb-3">Estoque disponível: <span class="fw-bold" id="modal-product-stock">0</span></p>
                                    
                                    <div class="mb-3">
                                        <label for="product-quantity" class="form-label">Quantidade</label>
                                        <div class="input-group">
                                            <button type="button" class="btn btn-outline-secondary" id="decrease-qty">-</button>
                                            <input type="number" id="product-quantity" class="form-control text-center" value="1" min="1">
                                            <button type="button" class="btn btn-outline-secondary" id="increase-qty">+</button>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                                    <button type="submit" class="btn btn-primary" id="add-to-cart" data-id="">Adicionar ao Carrinho</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            `;
            
            // Adicionar ao body
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHTML;
            document.body.appendChild(modalContainer.firstElementChild);
            
            // Obter referência para o modal recém-criado
            modalQuantidade = document.getElementById('modalQuantidade');
            
            if (modalQuantidade) {
                console.log("Modal de quantidade criado com sucesso!");
            } else {
                console.error("Falha ao criar o modal de quantidade!");
            }
        } else {
            console.log("Modal de quantidade encontrado:", modalQuantidade.id);
        }
        
        return modalQuantidade;
    }
    
    // Configurar botão Adicionar ao Carrinho
    function setupAddToCartButton() {
        console.log("Configurando botão de Adicionar ao Carrinho");
        
        // Encontrar o botão com diferentes seletores possíveis
        const addToCartButton = document.getElementById('add-to-cart') ||
                               document.getElementById('add-to-cart-button') ||
                               document.querySelector('.add-to-cart-button') ||
                               document.querySelector('[data-action="add-to-cart"]');
        
        if (addToCartButton) {
            console.log("Botão de adicionar ao carrinho encontrado:", addToCartButton.id || addToCartButton.className);
            
            // Remover TODOS os eventos de clique anteriores clonando o elemento
            const newButton = addToCartButton.cloneNode(true);
            addToCartButton.parentNode.replaceChild(newButton, addToCartButton);
            
            // Adicionar novo evento de clique
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Impedir propagação do evento
                
                // Desabilitar o botão temporariamente para evitar cliques múltiplos
                this.disabled = true;
                
                // Obter o ID do produto diretamente do atributo data-id do botão
                const produtoId = this.getAttribute('data-id');
                
                // Obter a quantidade do input
                const quantidadeInput = document.getElementById('product-quantity');
                const quantidade = quantidadeInput ? parseInt(quantidadeInput.value) || 1 : 1;
                
                if (!produtoId) {
                    console.error("ID de produto não encontrado no botão!");
                    alert("Erro: Não foi possível identificar o produto.");
                    this.disabled = false; // Reabilitar o botão
                    return;
                }
                
                console.log("Adicionando ao carrinho produto ID:", produtoId, "Quantidade:", quantidade);
                
                // Chamar a função para adicionar ao carrinho apenas UMA vez
                adicionarAoCarrinhoAjax(produtoId, quantidade);
                
                // Reabilitar o botão após 2 segundos
                setTimeout(() => {
                    this.disabled = false;
                }, 2000);
            });
            
            console.log("Evento click configurado para o botão Adicionar ao Carrinho");
        } else {
            console.warn("Botão 'Adicionar ao Carrinho' não encontrado!");
        }
    }
    
    // Configurar cliques nos produtos
    function setupProductClicks() {
        console.log("Configurando cliques nos produtos");
        
        // Garantir que o modal existe antes de prosseguir
        const modalQuantidade = garantirModalQuantidade();
        
        // Registra todos os modais disponíveis para diagnóstico
        const todosModais = document.querySelectorAll('.modal');
        console.log(`Total de modais encontrados: ${todosModais.length}`);
        todosModais.forEach(modal => {
            console.log(`Modal encontrado: ID=${modal.id}, Classes=${modal.className}`);
        });
        
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
                    
                    // Usamos o modal garantido
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
                            }, 300);
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
                            if (confirm("Não foi possível abrir o modal. Deseja adicionar o produto com quantidade 1?")) {
                                adicionarAoCarrinhoAjax(produtoId, 1);
                            }
                        }
                    } else {
                        console.error("Modal de quantidade não encontrado! Tentando adicionar diretamente ao carrinho.");
                        if (confirm("Modal não encontrado. Deseja adicionar o produto com quantidade 1?")) {
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
        
        // Se ainda não encontramos a seção de pagamento em dinheiro, vamos criá-la
        if (!cashPaymentSection && paymentMethodSelect) {
            console.log("Seção de pagamento em dinheiro não encontrada. Criando uma nova...");
            
            // Criar um novo contêiner para pagamento em dinheiro
            cashPaymentSection = document.createElement('div');
            cashPaymentSection.id = 'change-container';
            cashPaymentSection.className = 'form-group-compact mt-2';
            cashPaymentSection.style.display = 'none';
            cashPaymentSection.innerHTML = `
                <label for="payment-amount" class="form-label-sm">Valor Pago</label>
                <div class="input-group input-group-sm">
                    <span class="input-group-text">R$</span>
                    <input type="number" id="payment-amount" class="form-control" step="0.01" min="0">
                </div>
                <div class="mt-1">
                    <small>Troco: <span class="change-value" id="change-amount">R$ 0,00</span></small>
                </div>
            `;
            
            // Inserir após o select de método de pagamento
            const parentElement = paymentMethodSelect.closest('.form-group-compact') || 
                                 paymentMethodSelect.parentNode;
            
            if (parentElement) {
                parentElement.insertAdjacentElement('afterend', cashPaymentSection);
                console.log("Seção de pagamento em dinheiro criada e inserida no DOM");
            } else {
                console.error("Não foi possível encontrar um elemento pai para inserir a seção de pagamento");
            }
        }
        
        if (paymentMethodSelect) {
            console.log("Método de pagamento inicial:", paymentMethodSelect.value);
            debugElemento(paymentMethodSelect, "Select de método de pagamento:");
            
            // Mostrar/esconder seção de pagamento em dinheiro com base no método selecionado
            function updateCashPaymentVisibility() {
                const selectedMethod = paymentMethodSelect.value;
                console.log("Método de pagamento selecionado:", selectedMethod);
                
                if (cashPaymentSection) {
                    // Verificar diferentes possíveis valores para o método dinheiro
                    const isDinheiro = selectedMethod === 'dinheiro' || 
                                     selectedMethod === 'cash' || 
                                     selectedMethod === '1' || 
                                     selectedMethod === 1 ||
                                     (typeof selectedMethod === 'string' && 
                                      selectedMethod.toLowerCase().includes('dinheiro'));
                    
                    if (isDinheiro) {
                        cashPaymentSection.style.display = 'block';
                        console.log("Mostrando seção de pagamento em dinheiro");
                        
                        // Focar no campo de valor pago
                        setTimeout(() => {
                            const paymentAmount = document.getElementById('payment-amount');
                            if (paymentAmount) {
                                paymentAmount.focus();
                            }
                        }, 100);
                    } else {
                        cashPaymentSection.style.display = 'none';
                        console.log("Ocultando seção de pagamento em dinheiro");
                    }
                } else {
                    console.warn("Seção de pagamento em dinheiro não encontrada");
                }
            }
            
            // Verificar se há opções no select
            if (paymentMethodSelect.options.length === 0) {
                console.warn("Select de método de pagamento não tem opções. Adicionando opções padrão...");
                
                // Adicionar algumas opções padrão
                const options = [
                    { value: '1', text: 'Dinheiro' },
                    { value: '2', text: 'Cartão de Crédito' },
                    { value: '3', text: 'Cartão de Débito' },
                    { value: '4', text: 'PIX' }
                ];
                
                options.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.text = opt.text;
                    paymentMethodSelect.appendChild(option);
                });
            }
            
            // Remover eventos existentes clonando o elemento
            const newSelect = paymentMethodSelect.cloneNode(true);
            paymentMethodSelect.parentNode.replaceChild(newSelect, paymentMethodSelect);
            paymentMethodSelect = newSelect;
            
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
        
        // Procurar pelo campo de valor pago
        const paymentInput = document.getElementById('payment-amount');
        
        if (!paymentInput) {
            console.warn("Input de valor pago não encontrado");
            return;
        }
        
        // Remover eventos existentes clonando o elemento
        const newInput = paymentInput.cloneNode(true);
        paymentInput.parentNode.replaceChild(newInput, paymentInput);
        
        // Adicionar evento de input para calcular o troco em tempo real
        newInput.addEventListener('input', function() {
            // Obter o valor total da venda
            const totalElement = document.getElementById('total') || 
                               document.getElementById('total-sale') || 
                               document.getElementById('total_venda') || 
                               document.querySelector('.total-value');
            
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
                                 document.querySelector('.change-display, .change-value');
            
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
        
        try {
            // Garantir token CSRF
            ensureCSRFToken();
            
            // Primeiro garantimos que o modal existe
            garantirModalQuantidade();
            
            // Configurar componentes na ordem correta
            setupProductClicks();
            setupQuantityInput();
            setupAddToCartButton();
            setupPaymentForm();
            setupProductSearchField();
            
            // Calcular totais do carrinho iniciais
            setTimeout(calcularTotaisCarrinho, 500);
            
            console.log("Sistema PDV inicializado com sucesso!");
        } catch (error) {
            console.error("Erro ao inicializar o sistema PDV:", error);
            alert("Ocorreu um erro ao inicializar o sistema. Verifique o console para mais detalhes.");
        }
    });

    // Função para tentar consertar problemas comuns
    function corrigirProblemasComuns() {
        console.log("Verificando e corrigindo problemas comuns...");
        
        // 1. Verificar se o modal de quantidade existe
        garantirModalQuantidade();
        
        // 2. Verificar se o campo de pagamento em dinheiro está funcionando
        const paymentMethodSelect = document.getElementById('metodo_pagamento');
        if (paymentMethodSelect) {
            const event = new Event('change');
            paymentMethodSelect.dispatchEvent(event);
        }
        
        // 3. Recalcular totais do carrinho
        calcularTotaisCarrinho();
        
        console.log("Verificação e correção concluídas");
    }

    // Adicionar função de diagnóstico para uso no console
    window.diagnosticoPDV = function() {
        console.log("=== DIAGNÓSTICO DO SISTEMA PDV ===");
        
        const elementos = {
            "Modal de Quantidade": document.getElementById('modalQuantidade'),
            "Botão Adicionar ao Carrinho": document.getElementById('add-to-cart'),
            "Input de Quantidade": document.getElementById('product-quantity'),
            "Container do Carrinho": document.getElementById('cart-items') || document.getElementById('itens_venda'),
            "Select de Método de Pagamento": document.getElementById('metodo_pagamento'),
            "Campo de Valor Pago": document.getElementById('payment-amount'),
            "Campo de Troco": document.getElementById('change-amount'),
            "Subtotal": document.getElementById('subtotal'),
            "Total": document.getElementById('total') || document.querySelector('.total-value')
        };
        
        for (const [nome, elemento] of Object.entries(elementos)) {
            console.log(`${nome}: ${elemento ? 'Encontrado' : 'NÃO ENCONTRADO'}`);
            if (elemento) {
                debugElemento(elemento, nome);
            }
        }
        
        console.log("=== CORREÇÃO AUTOMÁTICA DE PROBLEMAS ===");
        corrigirProblemasComuns();
        
        return "Diagnóstico concluído. Verifique o console para mais detalhes.";
    };

    // Executar correção automática de problemas após 3 segundos
    setTimeout(corrigirProblemasComuns, 3000);
})(); 