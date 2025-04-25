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
                confirmarQuantidade(); // confirma e adiciona produto
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

    function confirmarQuantidade() {
        console.log("Confirmando quantidade");
        
        // Verificar se o modal está aberto
        const modal = document.getElementById('modalQuantidade');
        if (!modal || !modal.classList.contains('show')) {
            console.error("Erro: Modal de quantidade não está aberto");
            return;
        }
        
        // Obter o valor da quantidade
        const quantityInput = document.getElementById('product-quantity');
        if (!quantityInput) {
            console.error("Erro: Input de quantidade não encontrado");
            return;
        }
        
        // Verificar se é um valor válido
        const quantity = parseInt(quantityInput.value);
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
        
        // Verificar se a quantidade é válida para o estoque disponível
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
        
        console.log("Adicionando produto ao carrinho com quantidade:", quantity);
        
        // Verificar se o botão tem os atributos de dados necessários
        const addButton = document.getElementById('add-to-cart');
        if (!addButton) {
            console.error("Erro: Botão de adicionar ao carrinho não encontrado");
            return;
        }
        
        // Informações de debug para tentar encontrar o problema
        const id = addButton.getAttribute('data-id');
        const name = addButton.getAttribute('data-name');
        const price = addButton.getAttribute('data-price');
        
        console.log("Dados do produto para carrinho:", { id, name, price, quantity });
        
        // Se o botão não tiver os atributos de dados necessários, ocorreu algum problema na seleção do produto
        if (!id || !name || !price) {
            console.error("Erro: Botão sem dados de produto", addButton);
            
            // Tentar recuperar os dados do produto selecionado
            const selectedProduct = document.querySelector('#products-grid tbody tr.selected');
            if (selectedProduct) {
                console.log("Tentando recuperar dados do produto selecionado", selectedProduct);
                
                const selectedId = selectedProduct.getAttribute('data-id');
                const selectedName = selectedProduct.getAttribute('data-name');
                const selectedPrice = selectedProduct.getAttribute('data-price');
                const selectedCode = selectedProduct.getAttribute('data-code');
                
                console.log("Dados recuperados:", { selectedId, selectedName, selectedPrice, selectedCode });
                
                // Atualizar atributos do botão com os dados do produto selecionado
                addButton.setAttribute('data-id', selectedId);
                addButton.setAttribute('data-name', selectedName);
                addButton.setAttribute('data-price', selectedPrice);
                addButton.setAttribute('data-code', selectedCode);
                
                // Agora podemos prosseguir com o click nativo
                addButton.click();
                
                // Fechar o modal após um breve atraso
                setTimeout(() => {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                }, 300);
            } else {
                console.error("Erro: Produto selecionado não encontrado para recuperação");
                Swal.fire({
                    icon: 'error',
                    title: 'Erro ao Adicionar Produto',
                    text: 'Não foi possível obter os dados do produto. Por favor, tente novamente.',
                    confirmButtonText: 'OK'
                });
                
                // Fechar o modal para que o usuário possa tentar novamente
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            }
            return;
        }
        
        // Simplesmente clicar no botão nativo para acionar o comportamento original
        addButton.click();
        
        // Fechar o modal após um breve atraso
        setTimeout(() => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        }, 300);
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
                confirmarQuantidade(); // Chama a função de confirmação
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
    
    // Configuração dos botões e eventos do modal de quantidade
    const configurarModal = function() {
        console.log("Configurando modal e botões");
        
        // Configurar botão Adicionar ao Carrinho
        const botaoConfirmar = document.getElementById('add-to-cart');
        if (botaoConfirmar) {
            // Remover listeners anteriores para evitar duplicação
            const novoBotao = botaoConfirmar.cloneNode(true);
            botaoConfirmar.parentNode.replaceChild(novoBotao, botaoConfirmar);
            
            // Adicionar novo listener
            novoBotao.addEventListener('click', function(e) {
                // Não chamar preventDefault para permitir que o botão execute sua ação padrão
                console.log("Botão Adicionar ao Carrinho clicado");
                // confirmarQuantidade();
            });
        }
        
        // Configurar botões +/- para quantidade
        const botaoMais = document.getElementById('increase-qty');
        const botaoMenos = document.getElementById('decrease-qty');
        const inputQuantidade = document.getElementById('product-quantity');
        
        if (botaoMais && inputQuantidade) {
            // Remover listeners anteriores
            const novoBotaoMais = botaoMais.cloneNode(true);
            botaoMais.parentNode.replaceChild(novoBotaoMais, botaoMais);
            
            // Adicionar novo listener
            novoBotaoMais.addEventListener('click', function() {
                const currentValue = parseInt(inputQuantidade.value) || 1;
                inputQuantidade.value = currentValue + 1;
            });
        }
        
        if (botaoMenos && inputQuantidade) {
            // Remover listeners anteriores
            const novoBotaoMenos = botaoMenos.cloneNode(true);
            botaoMenos.parentNode.replaceChild(novoBotaoMenos, botaoMenos);
            
            // Adicionar novo listener
            novoBotaoMenos.addEventListener('click', function() {
                const currentValue = parseInt(inputQuantidade.value) || 2;
                if (currentValue > 1) {
                    inputQuantidade.value = currentValue - 1;
                }
            });
        }
        
        // Configurar formulário de quantidade
        const formQuantidade = document.getElementById('add-to-cart-form');
        if (formQuantidade) {
            // Remover listeners anteriores
            const novoForm = formQuantidade.cloneNode(true);
            formQuantidade.parentNode.replaceChild(novoForm, formQuantidade);
            
            // Adicionar novo listener
            novoForm.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log("Formulário de quantidade submetido");
                confirmarQuantidade();
                return false;
            });
        }
        
        // Configurar o modal de quantidade quando for aberto
        const modalQuantidade = document.getElementById('modalQuantidade');
        if (modalQuantidade) {
            modalQuantidade.addEventListener('shown.bs.modal', function() {
                console.log("Modal de quantidade aberto");
                
                // Configurar o input de quantidade
                const quantityInput = document.getElementById('product-quantity');
                if (quantityInput) {
                    quantityInput.focus();
                    quantityInput.select();
                    
                    // Adicionar evento de Enter no input
                    quantityInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            console.log("Enter pressionado no input de quantidade");
                            confirmarQuantidade();
                        }
                    });
                }
            });
        }
    };
    
    // Executar configuração do modal
    configurarModal();
    
    // Executar novamente a configuração após um pequeno atraso para garantir que todos os elementos estejam carregados
    setTimeout(configurarModal, 500);
    
    // Mensagem inicial no console
    console.log("PDV.js carregado - Atalhos: F1=Produto, F2=Pagamento, F3=Desconto, F4=Finalizar");
}); 