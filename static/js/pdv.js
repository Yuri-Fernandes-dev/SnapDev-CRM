/**
 * PDV - Controle de atalhos de teclado e fluxo do PDV
 */
document.addEventListener("DOMContentLoaded", function () {
    let etapa = 0;

    window.addEventListener("keydown", function (event) {
        // Evitar atalhos se algum modal estiver aberto
        if (document.querySelector('.modal.show')) {
            return;
        }
        
        // Atalho F1: foco no input
        if (event.key === "F1") {
            event.preventDefault();
            document.getElementById("codigo_produto")?.focus();
            document.getElementById("codigo_produto")?.select();
            etapa = 1;
        }

        // ENTER: ação de acordo com etapa
        if (event.key === "Enter") {
            event.preventDefault();
            if (etapa === 1) {
                selecionarProduto(); // lógica pra selecionar produto
                etapa = 2;
            } else if (etapa === 2) {
                abrirModalQuantidade(); // exibe modal
                etapa = 3;
            } else if (etapa === 3) {
                adicionarAoCarrinho(); // confirma e adiciona produto
                etapa = 0;
            }
        }

        // F2: método de pagamento
        if (event.key === "F2") {
            event.preventDefault();
            const pagamento = document.getElementById("metodo_pagamento");
            if (pagamento) {
                pagamento.focus();
                // Se tiver a função nativa para abrir o modal de pagamento, chamá-la
                if (typeof abrirModalFormaPagamento === 'function') {
                    abrirModalFormaPagamento();
                }
            }
        }

        // F3: desconto
        if (event.key === "F3") {
            event.preventDefault();
            const desconto = document.getElementById("desconto");
            if (desconto) {
                desconto.focus();
                // Se tiver a função nativa para abrir o modal de desconto, chamá-la
                if (typeof abrirModalDesconto === 'function') {
                    abrirModalDesconto();
                }
            }
        }

        // F4: finalizar venda
        if (event.key === "F4") {
            event.preventDefault();
            const botaoFinalizar = document.getElementById("btn-finalizar");
            if (botaoFinalizar) {
                botaoFinalizar.click();
                // Se tiver a função nativa para finalizar a venda, chamá-la
                if (typeof finalizarVenda === 'function') {
                    finalizarVenda();
                }
            }
        }
    });

    // Funções auxiliares para o fluxo do PDV
    function selecionarProduto() {
        console.log("Produto selecionado");
        
        // Obter o valor do campo de código/busca
        const codigo = document.getElementById("codigo_produto").value.trim();
        if (!codigo) return;
        
        // Buscar todos os produtos
        const produtos = Array.from(document.querySelectorAll('#products-grid tbody tr.product-item'));
        
        // MODIFICADO: Buscar apenas correspondências exatas (não palavras parciais)
        const produtoExato = produtos.find(p => {
            const prodCodigo = p.getAttribute('data-code')?.toLowerCase() || '';
            const prodNome = p.getAttribute('data-name')?.toLowerCase() || '';
            const prodCodigoBarras = p.getAttribute('data-barcode')?.toLowerCase() || '';
            
            // Buscar correspondência exata com código, nome ou código de barras
            return prodCodigo === codigo.toLowerCase() || 
                   prodNome === codigo.toLowerCase() || 
                   prodCodigoBarras === codigo.toLowerCase();
        });
        
        // Se encontrou correspondência exata, selecionar apenas esse produto
        if (produtoExato) {
            console.log("Produto exato encontrado:", produtoExato);
            // Mostrar apenas o produto exato (ocultar os outros)
            produtos.forEach(p => {
                if (p !== produtoExato) {
                    p.style.display = 'none';
                    p.classList.remove('selected');
                    p.style.outline = '';
                } else {
                    p.style.display = '';
                }
            });
            
            // Selecionar o produto encontrado
            produtoExato.classList.add('selected');
            produtoExato.style.outline = '2px solid #198754';
            produtoExato.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            console.log("Produto exato selecionado:", produtoExato.getAttribute('data-name'));
            
            // Se não estiver sem estoque, abrir modal de quantidade
            if (!produtoExato.classList.contains('out-of-stock')) {
                // Preencher informações para o botão de adicionar ao carrinho manualmente
                const id = produtoExato.getAttribute('data-id');
                const name = produtoExato.getAttribute('data-name');
                const price = produtoExato.getAttribute('data-price');
                const code = produtoExato.getAttribute('data-code');
                const stock = produtoExato.getAttribute('data-stock');
                
                console.log("Dados do produto para o carrinho:", { id, name, price, code, stock });
                
                // Verificar se os atributos necessários existem
                if (!id || !name || !price) {
                    console.error("Erro: Produto com dados incompletos", produtoExato);
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro ao Selecionar Produto',
                        text: 'Dados do produto estão incompletos. Por favor, contate o suporte.',
                        confirmButtonText: 'OK'
                    });
                    return;
                }
                
                // Preparar o modal para exibição
                const modalProduto = document.getElementById('modal-product-name');
                const modalPreco = document.getElementById('modal-product-price');
                const modalEstoque = document.getElementById('modal-product-stock');
                const modalQuantidade = document.getElementById('product-quantity');
                
                if (modalProduto) modalProduto.textContent = name;
                if (modalPreco) modalPreco.textContent = `R$ ${parseFloat(price).toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                if (modalEstoque) modalEstoque.textContent = stock;
                if (modalQuantidade) modalQuantidade.value = '1';
                
                // Atribuir dados ao botão de adicionar ao carrinho
                const addButton = document.getElementById('add-to-cart');
                if (addButton) {
                    addButton.setAttribute('data-id', id);
                    addButton.setAttribute('data-name', name);
                    addButton.setAttribute('data-price', price);
                    addButton.setAttribute('data-code', code);
                    console.log("Botão de adicionar ao carrinho configurado com dados:", addButton);
                }
                
                // Verificar se existe a função de selecionar produto do sistema
                if (typeof selectProduct === 'function') {
                    setTimeout(() => selectProduct(produtoExato), 100);
                } else {
                    abrirModalQuantidade();
                }
            } else {
                // Mostrar aviso de produto sem estoque
                Swal.fire({
                    icon: 'warning',
                    title: 'Produto Indisponível',
                    text: 'Este produto está sem estoque.',
                    confirmButtonText: 'OK'
                });
            }
        } else {
            // Nenhum produto exato encontrado - limpar seleção
            produtos.forEach(p => {
                p.classList.remove('selected');
                p.style.outline = '';
            });
            
            // Mostrar todos os produtos e aviso
            produtos.forEach(p => p.style.display = '');
            
            console.log("Nenhum produto exato encontrado para:", codigo);
            
            // Mostrar aviso de produto não encontrado
            Swal.fire({
                icon: 'info',
                title: 'Produto Não Encontrado',
                text: 'Nenhum produto corresponde exatamente à busca. Tente um código ou nome exato.',
                confirmButtonText: 'OK'
            });
        }
    }

    function abrirModalQuantidade() {
        console.log("Abrindo modal de quantidade");
        
        // Obter o produto selecionado
        const produtoSelecionado = document.querySelector('#products-grid tbody tr.selected');
        if (!produtoSelecionado) {
            console.error("Erro: Nenhum produto selecionado para abrir o modal");
            return;
        }
        
        // Extrair dados do produto selecionado
        const id = produtoSelecionado.getAttribute('data-id');
        const nome = produtoSelecionado.getAttribute('data-name');
        const preco = produtoSelecionado.getAttribute('data-price');
        const estoque = produtoSelecionado.getAttribute('data-stock');
        const codigo = produtoSelecionado.getAttribute('data-code');
        
        console.log("Dados do produto para modal:", { id, nome, preco, estoque, codigo });
        
        // Verificar se tem a função nativa do sistema para abrir o modal
        if (typeof selectProduct === 'function') {
            // Usar a função nativa do sistema
            console.log("Usando função nativa selectProduct");
            selectProduct(produtoSelecionado);
        } else {
            console.log("Usando função própria para abrir modal");
            // Abrir o modal manualmente
            const modal = new bootstrap.Modal(document.getElementById('modalQuantidade'));
            modal.show();
            
            // Preencher dados do produto no modal
            document.getElementById('modal-product-name').textContent = nome;
            document.getElementById('modal-product-price').textContent = `R$ ${parseFloat(preco).toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            document.getElementById('modal-product-stock').textContent = estoque;
            document.getElementById('product-quantity').value = '1';
            
            // Definir atributos no botão de adicionar ao carrinho
            const botaoAdicionar = document.getElementById('add-to-cart');
            if (botaoAdicionar) {
                botaoAdicionar.setAttribute('data-id', id);
                botaoAdicionar.setAttribute('data-name', nome);
                botaoAdicionar.setAttribute('data-price', preco);
                botaoAdicionar.setAttribute('data-code', codigo);
                console.log("Botão configurado com atributos:", botaoAdicionar);
            } else {
                console.error("Erro: Botão de adicionar ao carrinho não encontrado");
            }
            
            // Focar no campo de quantidade
            setTimeout(() => {
                document.getElementById('product-quantity').focus();
                document.getElementById('product-quantity').select();
            }, 300);
        }
    }

    // Nova função para adicionar produto ao carrinho
    function adicionarAoCarrinho() {
        console.log("Adicionando produto ao carrinho");
        
        // Verificar se o modal está aberto
        const modal = document.getElementById('modalQuantidade');
        if (!modal || !modal.classList.contains('show')) {
            console.error("Erro: Modal de quantidade não está aberto");
            return;
        }
        
        // 1. Obter dados do produto e quantidade
        const addButton = document.getElementById('add-to-cart');
        const quantityInput = document.getElementById('product-quantity');
        
        if (!addButton || !quantityInput) {
            console.error("Erro: Botão ou input de quantidade não encontrados");
            return;
        }
        
        const id = addButton.getAttribute('data-id');
        const name = addButton.getAttribute('data-name');
        const price = addButton.getAttribute('data-price');
        const code = addButton.getAttribute('data-code');
        const quantity = parseInt(quantityInput.value) || 1;
        
        // 2. Validar quantidade
        if (isNaN(quantity) || quantity <= 0) {
            console.error("Erro: Quantidade inválida:", quantity);
            Swal.fire({
                icon: 'warning',
                title: 'Quantidade Inválida',
                text: 'Por favor, insira uma quantidade válida.',
                confirmButtonText: 'OK'
            });
            quantityInput.focus();
            quantityInput.select();
            return;
        }
        
        // 3. Validar estoque
        const stockText = document.getElementById('modal-product-stock').textContent;
        const availableStock = parseInt(stockText) || 0;
        if (quantity > availableStock) {
            console.error("Erro: Quantidade excede estoque:", quantity, availableStock);
            Swal.fire({
                icon: 'warning',
                title: 'Quantidade Excede Estoque',
                text: `Estoque disponível: ${availableStock}. Por favor, reduza a quantidade.`,
                confirmButtonText: 'OK'
            });
            return;
        }
        
        // 4. Verificar se tem dados necessários
        if (!id || !name || !price) {
            console.error("Erro: Produto sem dados completos", { id, name, price });
            Swal.fire({
                icon: 'error',
                title: 'Erro nos Dados do Produto',
                text: 'Dados do produto incompletos. Por favor, tente novamente.',
                confirmButtonText: 'OK'
            });
            return;
        }
        
        console.log("Produto a ser adicionado:", { id, name, price, code, quantity });
        
        // 5. Adicionar ao carrinho
        try {
            // Se existir a variável cart no escopo global
            if (typeof cart !== 'undefined') {
                // Verificar se o produto já está no carrinho
                const existingIndex = findProductInCart ? findProductInCart(id) : -1;
                
                if (existingIndex >= 0) {
                    // Aumentar a quantidade se já existe
                    cart[existingIndex].quantity += quantity;
                    console.log("Quantidade atualizada no carrinho:", cart[existingIndex]);
                } else {
                    // Adicionar novo item
                    cart.push({
                        id: id,
                        name: name,
                        price: parseFloat(price),
                        code: code,
                        quantity: quantity
                    });
                    console.log("Novo produto adicionado ao carrinho:", cart[cart.length - 1]);
                }
                
                // Atualizar o carrinho na UI se existir a função
                if (typeof renderCartItems === 'function') {
                    renderCartItems();
                }
            } else {
                // Alternativa: disparar evento nativo do botão
                console.log("Simulando clique no botão para execução do código nativo");
                
                // Definir o atributo de quantidade (se necessário)
                addButton.setAttribute('data-quantity', quantity);
                
                // Disparar o clique nativo no botão
                const clickEvent = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                });
                addButton.dispatchEvent(clickEvent);
            }
            
            // 6. Fechar o modal
            setTimeout(() => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
                console.log("Modal fechado após adicionar ao carrinho");
            }, 300);
            
            // 7. Limpar a seleção e resetar o estado
            setTimeout(() => {
                // Limpar o campo de código do produto
                const codigoInput = document.getElementById("codigo_produto");
                if (codigoInput) {
                    codigoInput.value = "";
                    codigoInput.focus();
                }
                
                // Resetar a seleção de produtos
                const produtos = document.querySelectorAll('#products-grid tbody tr.product-item');
                produtos.forEach(p => {
                    p.style.display = '';
                    p.classList.remove('selected');
                    p.style.outline = '';
                });
            }, 500);
            
        } catch (error) {
            console.error("Erro ao adicionar produto ao carrinho:", error);
            Swal.fire({
                icon: 'error',
                title: 'Erro ao Adicionar Produto',
                text: 'Ocorreu um erro ao adicionar o produto ao carrinho.',
                confirmButtonText: 'OK'
            });
        }
    }
    
    // Adicionar evento global para tecla ENTER quando um modal estiver aberto
    document.addEventListener('keydown', function(event) {
        // Verifica se a tecla pressionada é ENTER
        if (event.key === 'Enter') {
            // Verifica se o modal de quantidade está visível
            const modalQuantidade = document.getElementById('modalQuantidade');
            if (modalQuantidade && modalQuantidade.classList.contains('show')) {
                event.preventDefault(); // Impede o comportamento padrão
                console.log("Enter pressionado no modal de quantidade");
                adicionarAoCarrinho(); // Chama a função de adicionar ao carrinho
                return;
            }
            
            // Verifica se o modal de confirmação de venda está visível
            const confirmationModal = document.getElementById('confirmationModal');
            if (confirmationModal && confirmationModal.classList.contains('show')) {
                event.preventDefault();
                // Buscar o botão de confirmar venda e clicar nele
                const confirmButton = document.getElementById('confirm-sale');
                if (confirmButton && !confirmButton.disabled && confirmButton.style.display !== 'none') {
                    confirmButton.click();
                }
                return;
            }
            
            // Verifica se o modal de forma de pagamento está visível
            const modalFormaPagamento = document.getElementById('modalFormaPagamento');
            if (modalFormaPagamento && modalFormaPagamento.classList.contains('show')) {
                event.preventDefault();
                // Se o foco estiver no campo de valor pago
                if (document.activeElement === document.getElementById('modal-payment-amount')) {
                    const confirmButton = document.getElementById('confirm-payment-method');
                    if (confirmButton) confirmButton.click();
                } 
                // Se o foco estiver no select de método de pagamento
                else if (document.activeElement === document.getElementById('modal-payment-method')) {
                    const selected = document.getElementById('modal-payment-method').options[document.getElementById('modal-payment-method').selectedIndex];
                    if (selected && selected.textContent.includes('Dinheiro')) {
                        document.getElementById('modal-payment-amount')?.focus();
                    } else {
                        const confirmButton = document.getElementById('confirm-payment-method');
                        if (confirmButton) confirmButton.click();
                    }
                }
                return;
            }
            
            // Verifica se o modal de desconto está visível
            const modalDesconto = document.getElementById('modalDesconto');
            if (modalDesconto && modalDesconto.classList.contains('show')) {
                event.preventDefault();
                const confirmButton = document.getElementById('confirm-discount');
                if (confirmButton) confirmButton.click();
                return;
            }
        }
    });
    
    // Configurar eventos diretos nos elementos do modal
    function configurarEventosModal() {
        console.log("Configurando eventos diretos no modal de quantidade");
        
        // 1. Input de quantidade - evento de ENTER
        const inputQuantidade = document.getElementById('product-quantity');
        if (inputQuantidade) {
            inputQuantidade.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    console.log("Enter pressionado no input de quantidade");
                    adicionarAoCarrinho();
                }
            });
        }
        
        // 2. Botão Adicionar ao Carrinho
        const botaoAdicionar = document.getElementById('add-to-cart');
        if (botaoAdicionar) {
            botaoAdicionar.addEventListener('click', function(e) {
                // Não vamos prevenir o comportamento padrão para permitir que o sistema nativo funcione
                console.log("Botão Adicionar ao Carrinho clicado");
                // adicionarAoCarrinho será chamado pelo evento nativo ou pelo formulário
            });
        }
        
        // 3. Botões + e -
        const botaoMais = document.getElementById('increase-qty');
        const botaoMenos = document.getElementById('decrease-qty');
        
        if (botaoMais) {
            botaoMais.addEventListener('click', function() {
                const input = document.getElementById('product-quantity');
                if (input) {
                    const valor = parseInt(input.value) || 1;
                    input.value = valor + 1;
                }
            });
        }
        
        if (botaoMenos) {
            botaoMenos.addEventListener('click', function() {
                const input = document.getElementById('product-quantity');
                if (input) {
                    const valor = parseInt(input.value) || 2;
                    if (valor > 1) {
                        input.value = valor - 1;
                    }
                }
            });
        }
        
        // 4. Formulário
        const formulario = document.getElementById('add-to-cart-form');
        if (formulario) {
            formulario.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log("Formulário submetido");
                adicionarAoCarrinho();
                return false;
            });
        }
    }
    
    // Ativar eventos quando o modal for aberto
    const modalQuantidade = document.getElementById('modalQuantidade');
    if (modalQuantidade) {
        // Remover event listener antigo se existir
        const modalClone = modalQuantidade.cloneNode(true);
        if (modalQuantidade.parentNode) {
            modalQuantidade.parentNode.replaceChild(modalClone, modalQuantidade);
        }
        
        // Adicionar novo event listener
        modalClone.addEventListener('shown.bs.modal', function() {
            console.log("Modal de quantidade aberto - configurando eventos");
            
            // Configurar eventos do modal
            configurarEventosModal();
            
            // Focar no input de quantidade
            setTimeout(() => {
                const input = document.getElementById('product-quantity');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 300);
        });
    }
    
    // Configurar eventos na inicialização
    configurarEventosModal();
    
    // Mensagem inicial no console
    console.log("PDV.js carregado - Atalhos: F1=Produto, F2=Pagamento, F3=Desconto, F4=Finalizar");
}); 