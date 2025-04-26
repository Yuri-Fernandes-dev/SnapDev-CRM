/**
 * CORREÇÃO EMERGENCIAL - CLIQUE NOS PRODUTOS
 * Este arquivo deve ser incluído APÓS o pdv.js original
 */
(function() {
    // Executar quando o DOM estiver completamente carregado
    function fixPDV() {
        console.log("🔧 CORREÇÃO PDV: Iniciando correção do clique em produtos...");
        
        // Obter todos os produtos da tabela
        const produtos = document.querySelectorAll('tr[data-id]');
        console.log("🔧 CORREÇÃO PDV: Encontrados " + produtos.length + " produtos na tabela");
        
        if (produtos.length === 0) {
            console.error("🔧 CORREÇÃO PDV: Nenhum produto encontrado na tabela!");
            // Tentar novamente após um pequeno delay
            setTimeout(fixPDV, 1000);
            return;
        }
        
        // Adicionar eventos de clique para cada produto
        produtos.forEach(function(produto) {
            // Remover qualquer evento existente, clonando o elemento
            try {
                const clone = produto.cloneNode(true);
                if (produto.parentNode) {
                    produto.parentNode.replaceChild(clone, produto);
                    
                    // Adicionar novo evento de clique
                    clone.addEventListener('click', function(event) {
                        // Impedir propagação para outros handlers
                        event.stopPropagation();
                        event.preventDefault();
                        
                        console.log("🔧 CORREÇÃO PDV: Produto clicado:", this.getAttribute('data-id'));
                        
                        // Dados do produto
                        const produtoId = this.getAttribute('data-id');
                        const produtoNome = this.getAttribute('data-name');
                        const produtoPreco = this.getAttribute('data-price');
                        const produtoEstoque = this.getAttribute('data-stock');
                        
                        // Verificar estoque
                        if (parseInt(produtoEstoque) <= 0) {
                            if (window.Swal) {
                                Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                            } else {
                                alert('Produto sem estoque. Este produto não está disponível no momento.');
                            }
                            return;
                        }
                        
                        // Preencher modal
                        const modalProdutoNome = document.getElementById('modal-product-name');
                        const modalProdutoPreco = document.getElementById('modal-product-price');
                        const modalProdutoEstoque = document.getElementById('modal-product-stock');
                        const btnAdicionar = document.getElementById('add-to-cart');
                        const inputQuantidade = document.getElementById('product-quantity');
                        
                        if (modalProdutoNome) modalProdutoNome.textContent = produtoNome;
                        if (modalProdutoPreco) modalProdutoPreco.textContent = `R$ ${parseFloat(produtoPreco).toFixed(2)}`;
                        if (modalProdutoEstoque) modalProdutoEstoque.textContent = produtoEstoque;
                        
                        // Configurar botão
                        if (btnAdicionar) {
                            btnAdicionar.setAttribute('data-id', produtoId);
                            btnAdicionar.setAttribute('data-price', produtoPreco);
                        }
                        
                        // Resetar quantidade
                        if (inputQuantidade) inputQuantidade.value = '1';
                        
                        // Abrir modal usando Bootstrap 5
                        const modalQuantidade = document.getElementById('modalQuantidade');
                        if (modalQuantidade) {
                            try {
                                const modal = new bootstrap.Modal(modalQuantidade);
                                modal.show();
                                
                                // Focar no input de quantidade
                                setTimeout(() => {
                                    if (inputQuantidade) {
                                        inputQuantidade.focus();
                                        inputQuantidade.select();
                                    }
                                }, 300);
                            } catch (error) {
                                console.error("🔧 CORREÇÃO PDV: Erro ao abrir modal:", error);
                                alert("Erro ao abrir o modal. Verifique o console para detalhes.");
                            }
                        } else {
                            console.error("🔧 CORREÇÃO PDV: Modal de quantidade não encontrado!");
                        }
                    });
                    
                    // Adicionar estilo de cursor pointer
                    clone.style.cursor = 'pointer';
                }
            } catch (error) {
                console.error("🔧 CORREÇÃO PDV: Erro ao configurar produto:", error);
            }
        });
        
        console.log("🔧 CORREÇÃO PDV: Clique em produtos restaurado com sucesso!");
    }
    
    // Executar a correção após o carregamento completo da página
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixPDV);
    } else {
        // Se o DOM já estiver carregado, executar imediatamente
        fixPDV();
        // E também tentar novamente após um pequeno delay para garantir
        setTimeout(fixPDV, 1000);
    }
    
    // CORREÇÃO PARA O BOTÃO ADICIONAR AO CARRINHO
    function fixBotaoAdicionar() {
        console.log("🔧 CORREÇÃO PDV: Configurando botão Adicionar ao Carrinho...");
        
        // Obter o botão pelo ID
        const btnAdicionar = document.getElementById('add-to-cart');
        
        if (!btnAdicionar) {
            console.error("🔧 CORREÇÃO PDV: Botão Adicionar ao Carrinho não encontrado!");
            setTimeout(fixBotaoAdicionar, 1000); // Tentar novamente
            return;
        }
        
        console.log("🔧 CORREÇÃO PDV: Botão Adicionar ao Carrinho encontrado, adicionando evento de clique");
        
        // Remover eventos existentes e adicionar novo
        const clone = btnAdicionar.cloneNode(true);
        btnAdicionar.parentNode.replaceChild(clone, btnAdicionar);
        
        // Adicionar novo evento de clique
        clone.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            console.log("🔧 CORREÇÃO PDV: Botão Adicionar ao Carrinho clicado");
            
            // Obter dados do produto e quantidade
            const produtoId = this.getAttribute('data-id');
            const quantidade = parseInt(document.getElementById('product-quantity').value) || 1;
            
            if (!produtoId) {
                console.error("🔧 CORREÇÃO PDV: Dados do produto não encontrados no botão");
                return;
            }
            
            console.log("🔧 CORREÇÃO PDV: Adicionando produto ID:", produtoId, "Quantidade:", quantidade);
            
            // Se a função nativa existir, usá-la
            if (typeof window.addToCart === 'function') {
                console.log("🔧 CORREÇÃO PDV: Usando função nativa addToCart");
                window.addToCart(produtoId, quantidade);
            } else {
                console.log("🔧 CORREÇÃO PDV: Usando abordagem AJAX alternativa");
                // Usar AJAX como alternativa
                $.ajax({
                    url: '/sistema/vendas/adicionar-item/',
                    method: 'POST',
                    data: {
                        'produto_id': produtoId,
                        'quantidade': quantidade,
                        'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
                    },
                    success: function(data) {
                        console.log("🔧 CORREÇÃO PDV: Item adicionado com sucesso");
                        
                        // Atualizar carrinho
                        $('#itens_venda').html(data);
                        
                        // Fechar modal
                        const modalQuantidade = document.getElementById('modalQuantidade');
                        if (modalQuantidade) {
                            const modal = bootstrap.Modal.getInstance(modalQuantidade);
                            if (modal) {
                                modal.hide();
                            } else {
                                // Fallback
                                $(modalQuantidade).modal('hide');
                            }
                        }
                        
                        // Focar no input de produto
                        setTimeout(function() {
                            $('#codigo_produto').focus();
                        }, 300);
                    },
                    error: function(xhr, status, error) {
                        console.error("🔧 CORREÇÃO PDV: Erro ao adicionar item:", error);
                        alert("Erro ao adicionar item ao carrinho. Verifique o console para detalhes.");
                    }
                });
            }
        });
        
        console.log("🔧 CORREÇÃO PDV: Botão Adicionar ao Carrinho configurado com sucesso");
    }
    
    // Executar a correção do botão após o carregamento do DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(fixBotaoAdicionar, 1000);
        });
    } else {
        setTimeout(fixBotaoAdicionar, 1000);
    }
})(); 