/**
 * PDV - Controle de atalhos de teclado e fluxo do PDV (Versão Corrigida)
 */

// Função para obter CSRF token do cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Função para obter o CSRF token de várias fontes
function getCSRFToken() {
    // Verificar se existe um input hidden com o token
    const tokenInput = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (tokenInput) {
        console.log("CSRF token encontrado em input hidden:", tokenInput.value);
        return tokenInput.value;
    }
    
    // Verificar se existe no cookie
    const tokenCookie = getCookie('csrftoken');
    if (tokenCookie) {
        console.log("CSRF token encontrado em cookie:", tokenCookie);
        return tokenCookie;
    }
    
    // Verificar se existe em meta tag
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (tokenMeta) {
        console.log("CSRF token encontrado em meta tag:", tokenMeta.content);
        return tokenMeta.content;
    }
    
    console.error("CSRF token não encontrado!");
    return null;
}

document.addEventListener("DOMContentLoaded", function () {
    console.log("PDV.js carregado - Sistema de vendas inicializado");

    // Restaurar clique nos produtos - FIXME: CORREÇÃO URGENTE
    const produtosItems = document.querySelectorAll('#products-grid tbody tr.product-item');
    console.log("Número de produtos encontrados:", produtosItems.length);
    
    // Remover e readicionar eventos de clique para cada produto
    produtosItems.forEach(produto => {
        // Clonar o elemento para remover eventos
        const clone = produto.cloneNode(true);
        produto.parentNode.replaceChild(clone, produto);
        
        // Adicionar novo evento de clique
        clone.addEventListener('click', function() {
            console.log("Produto clicado:", this.getAttribute('data-name'));
            
            // Verificar estoque
            if (parseInt(this.getAttribute('data-stock')) <= 0) {
                Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                return;
            }
            
            // Preparar dados do produto
            const produtoData = {
                id: this.getAttribute('data-id'),
                name: this.getAttribute('data-name'),
                price: this.getAttribute('data-price'),
                code: this.getAttribute('data-code'),
                stock: this.getAttribute('data-stock')
            };
            
            // Preencher modal com dados do produto
            document.getElementById('modal-product-name').textContent = produtoData.name;
            document.getElementById('modal-product-price').textContent = `R$ ${parseFloat(produtoData.price).toFixed(2)}`;
            
            if (document.getElementById('modal-product-stock')) {
                document.getElementById('modal-product-stock').textContent = produtoData.stock;
            }
            
            // Configurar botão de adicionar
            const addToCartBtn = document.getElementById('add-to-cart');
            if (addToCartBtn) {
                addToCartBtn.setAttribute('data-id', produtoData.id);
                addToCartBtn.setAttribute('data-name', produtoData.name);
                addToCartBtn.setAttribute('data-price', produtoData.price);
                addToCartBtn.setAttribute('data-code', produtoData.code);
            }
            
            // Resetar quantidade para 1
            const quantityInput = document.getElementById('product-quantity');
            if (quantityInput) {
                quantityInput.value = "1";
            }
            
            // Abrir modal
            const modalQuantidade = document.getElementById('modalQuantidade');
            if (modalQuantidade) {
                const modal = new bootstrap.Modal(modalQuantidade);
                modal.show();
                
                // Focar no input de quantidade
                setTimeout(() => {
                    document.getElementById('product-quantity')?.focus();
                    document.getElementById('product-quantity')?.select();
                }, 300);
            } else {
                console.error("Erro: Modal de quantidade não encontrado!");
            }
        });
    });

    // Elementos principais
    const elements = {
        codigoProduto: document.getElementById("codigo_produto"),
        modalQuantidade: document.getElementById("modalQuantidade"),
        inputQuantidade: document.getElementById("product-quantity"),
        btnAdicionar: document.getElementById("add-to-cart"),
        formQuantidade: document.getElementById("add-to-cart-form")
    };

    // Variável de controle do fluxo
    let etapa = 0;

    // Atalhos de teclado globais
    document.addEventListener("keydown", function (event) {
        // Ignorar se estiver em inputs de texto (exceto no input de busca)
        if (event.target.tagName === 'INPUT' && event.target.id !== 'codigo_produto' && 
            event.target.id !== 'product-quantity') {
            return;
        }
        
        // F1 - Foco no input de código/busca
        if (event.key === "F1") {
            event.preventDefault();
            if (elements.codigoProduto) {
                elements.codigoProduto.focus();
                elements.codigoProduto.select();
            etapa = 1;
                console.log("F1: Foco no input de código do produto");
            }
        }

        // ENTER - Ação conforme etapa atual
        if (event.key === "Enter") {
            event.preventDefault();
            
            // Se o modal de quantidade estiver aberto
            if (elements.modalQuantidade && elements.modalQuantidade.classList.contains('show')) {
                console.log("Enter no modal de quantidade");
                adicionarProdutoAoCarrinho();
                return;
            }
            
            // Fluxo normal
            if (etapa === 1) {
                console.log("Enter na etapa 1: Selecionar produto");
                selecionarProduto();
                etapa = 2;
            } else if (etapa === 2) {
                console.log("Enter na etapa 2: Abrir modal de quantidade");
                abrirModalQuantidade();
            }
        }

        // F2 - Desconto
        if (event.key === "F2") {
            event.preventDefault();
            document.getElementById("desconto")?.focus();
        }

        // F3 - Pagamento
        if (event.key === "F3") {
            event.preventDefault();
            document.getElementById("metodo_pagamento")?.focus();
        }

        // F4 - Finalizar venda
        if (event.key === "F4") {
            event.preventDefault();
            document.getElementById("btn-finalizar")?.click();
        }
    });

    // Função para selecionar produto
    function selecionarProduto() {
        const codigo = elements.codigoProduto.value.trim();
        if (!codigo) return;
        
        const produtos = Array.from(document.querySelectorAll('#products-grid tbody tr.product-item'));
        
        // Verifica se o código é muito curto (menos de 3 caracteres)
        const codigoCurto = codigo.length < 3;
        
        // Primeiro tenta buscar por correspondência exata do código
        let produtoSelecionado = produtos.find(p => p.getAttribute('data-code') === codigo);
        
        // Se não encontrar correspondência exata e não for código curto, tenta busca parcial
        if (!produtoSelecionado && !codigoCurto) {
            produtoSelecionado = produtos.find(p => 
                p.getAttribute('data-name').toLowerCase() === codigo.toLowerCase()
            );
        }

        // Se ainda não encontrou e não for código curto, procura produtos que contenham o texto
        const produtosEncontrados = [];
        if (!produtoSelecionado && !codigoCurto) {
            produtos.forEach(p => {
                if (p.getAttribute('data-code').includes(codigo) || 
                    p.getAttribute('data-name').toLowerCase().includes(codigo.toLowerCase())) {
                    produtosEncontrados.push(p);
                }
            });

            // Se encontrou apenas um produto parcial, usa ele
            if (produtosEncontrados.length === 1) {
                produtoSelecionado = produtosEncontrados[0];
            }
            // Se encontrou múltiplos produtos, exibe um modal de seleção
            else if (produtosEncontrados.length > 1) {
                exibirModalSelecaoProdutos(produtosEncontrados);
                return;
            }
        }

        if (produtoSelecionado) {
            // Seleciona o produto
            produtos.forEach(p => p.classList.remove('selected'));
            produtoSelecionado.classList.add('selected');
            
            // Prepara dados para o modal
            const produtoData = {
                id: produtoSelecionado.getAttribute('data-id'),
                nome: produtoSelecionado.getAttribute('data-name'),
                preco: produtoSelecionado.getAttribute('data-price'),
                estoque: produtoSelecionado.getAttribute('data-stock')
            };

            // Abre modal de quantidade
            abrirModalQuantidade(produtoData);
        } else {
            // Mensagem quando o código é curto demais
            if (codigoCurto) {
                Swal.fire({
                    icon: 'info',
                    title: 'Código muito curto',
                    text: 'Para códigos curtos, insira o código exato do produto ou pelo menos 3 caracteres para busca.',
                    confirmButtonText: 'OK'
                });
            } else {
                Swal.fire('Produto não encontrado', 'Digite um código ou nome válido', 'info');
            }
        }
    }

    // Nova função para exibir modal de seleção de produtos quando houver múltiplos resultados
    function exibirModalSelecaoProdutos(produtos) {
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
            const preco = parseFloat(produto.getAttribute('data-price')).toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            
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
                            
                            // Selecionar o produto
                            const produtoData = {
                                id: produtoSelecionado.getAttribute('data-id'),
                                nome: produtoSelecionado.getAttribute('data-name'),
                                preco: produtoSelecionado.getAttribute('data-price'),
                                estoque: produtoSelecionado.getAttribute('data-stock')
                            };
                            
                            // Abrir modal de quantidade
                            abrirModalQuantidade(produtoData);
                        }
                    });
                });
            }
        });
    }

    // Função para abrir modal de quantidade
    function abrirModalQuantidade(produtoData) {
        if (!elements.modalQuantidade) return;

        // Preenche dados do produto no modal
        document.getElementById('modal-product-name').textContent = produtoData.nome;
        document.getElementById('modal-product-price').textContent = `R$ ${parseFloat(produtoData.preco).toFixed(2)}`;
        
        // Configura botão de adicionar
        elements.btnAdicionar.dataset.id = produtoData.id;
        elements.btnAdicionar.dataset.price = produtoData.preco;

        // Abre o modal
        const modal = new bootstrap.Modal(elements.modalQuantidade);
            modal.show();
            
        // Foca no input de quantidade
            setTimeout(() => {
            elements.inputQuantidade.focus();
            elements.inputQuantidade.select();
            }, 300);
    }

    // Função principal para adicionar produto ao carrinho
    function adicionarProdutoAoCarrinho() {
        const quantidade = parseInt(elements.inputQuantidade.value) || 1;
        const produtoId = elements.btnAdicionar.dataset.id;
        const produtoPreco = elements.btnAdicionar.dataset.price;

        if (!produtoId || !produtoPreco) {
            Swal.fire('Erro', 'Dados do produto incompletos', 'error');
            return;
        }
        
        // Verificar se a função nativa está disponível
        if (typeof addToCart === 'function') {
            // Usa função nativa do sistema
            addToCart(produtoId, quantidade);
        } else {
            // Implementação alternativa: enviar via AJAX diretamente
            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                console.error("CSRF token não encontrado!");
                Swal.fire('Erro de Segurança', 'Token CSRF não encontrado. Recarregue a página.', 'error');
                return;
            }
            
            // Mostrar indicador de carregamento
            Swal.fire({
                title: 'Adicionando ao carrinho...',
                text: 'Por favor, aguarde',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Enviar via AJAX
            $.ajax({
                url: '/sistema/vendas/adicionar-item/',
                type: 'POST',
                dataType: 'html',
                data: {
                    'produto_id': produtoId,
                    'quantidade': quantidade
                },
                headers: {
                    'X-CSRFToken': csrfToken
                },
                success: function(response) {
                    console.log("Produto adicionado com sucesso!");
                    
                    // Atualizar carrinho
                    $('#itens_venda').html(response);
                    
                    // Fechar o loading
                    Swal.close();
                    
                    // Mostrar mensagem de sucesso
                    const Toast = Swal.mixin({
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 3000,
                        timerProgressBar: true
                    });
                    
                    Toast.fire({
                        icon: 'success',
                        title: 'Produto adicionado ao carrinho!'
                    });
                    
                    // Adicionar ao array do carrinho
                    if (typeof cart !== 'undefined') {
                        const item = {
                            id: produtoId,
                            price: parseFloat(produtoPreco),
                            quantity: quantidade,
                        };
                        cart.push(item);
                    }
                    
                    // Atualizar a UI
                    if (typeof updateCartUI === 'function') {
                        updateCartUI();
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Erro ao adicionar produto:", error);
                    console.error("Status:", status);
                    console.error("Resposta:", xhr.responseText);
                    
                    Swal.fire({
                        icon: 'error',
                        title: 'Erro ao adicionar ao carrinho',
                        text: 'Verifique o console para mais detalhes.'
                    });
                }
            });
        }

        // Fecha o modal
        const modal = bootstrap.Modal.getInstance(elements.modalQuantidade);
        modal.hide();

        // Limpa e prepara para próximo produto
        elements.codigoProduto.value = '';
        elements.codigoProduto.focus();
        etapa = 1;
    }

    // Configura eventos do modal
    if (elements.modalQuantidade) {
        elements.modalQuantidade.addEventListener('shown.bs.modal', function() {
            elements.inputQuantidade.value = '1';
            elements.inputQuantidade.focus();
        });
    }

    // Configura evento de submit do formulário
    if (elements.formQuantidade) {
        elements.formQuantidade.addEventListener('submit', function(e) {
            e.preventDefault();
            adicionarProdutoAoCarrinho();
        });
    }

    // Configura evento de Enter no input de quantidade
    if (elements.inputQuantidade) {
        elements.inputQuantidade.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                adicionarProdutoAoCarrinho();
                }
            });
        }
        
    console.log("Configuração do PDV concluída - Sistema pronto para uso");
});

// Função corrigida para adicionar ao carrinho
function adicionarAoCarrinho() {
    const btnAdicionar = document.getElementById('add-to-cart');
    if (!btnAdicionar) return;

    // Dispara o clique NATIVO do sistema
    btnAdicionar.click();
    
    // Fecha o modal após 300ms (tempo para processamento)
                setTimeout(() => {
        bootstrap.Modal.getInstance(document.getElementById('modalQuantidade'))?.hide();
                }, 300);
}

// Configuração do evento Enter no modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && document.getElementById('modalQuantidade')?.classList.contains('show')) {
        e.preventDefault();
        document.getElementById('add-to-cart')?.click();
    }
});

// Define a função updateCartUI como polyfill para renderCartItems
function updateCartUI() {
    console.log("Atualizando a UI do carrinho");
    // Verifica se a função renderCartItems existe e a chama
    if (typeof renderCartItems === 'function') {
        renderCartItems();
        
        // Se updateTotals existir, chama também
        if (typeof updateTotals === 'function') {
            updateTotals();
        }
    } else {
        console.log("Função renderCartItems não encontrada");
    }
}

// Compatibilidade com IDs específicos do sistema
$(document).ready(function() {
    console.log("Configurando compatibilidade para IDs específicos do sistema...");
    
    // Verificar se existe input de CSRF token no DOM
    if (!document.querySelector('input[name=csrfmiddlewaretoken]')) {
        console.log("CSRF token input não encontrado, adicionando ao DOM");
        // Obter token do cookie
        const csrftoken = getCookie('csrftoken');
        if (csrftoken) {
            // Criar input hidden e adicionar ao body
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrfmiddlewaretoken';
            input.value = csrftoken;
            document.body.appendChild(input);
            console.log("CSRF token input adicionado ao DOM:", csrftoken);
        }
    }
    
    // Configurar o AJAX para incluir o CSRF token em todas as requisições
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain) {
                const csrftoken = getCSRFToken();
                if (csrftoken) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        }
    });
    
    // Mapear do ID padrão do sistema para IDs específicos mencionados nos requisitos
    
    // 1. Verificar se existe o elemento #quantidade_input
    const quantidadeInput = $('#quantidade_input');
    if (quantidadeInput.length) {
        console.log("Encontrado #quantidade_input, configurando eventos...");
        
        // Adicionar evento Enter no #quantidade_input
        quantidadeInput.on('keydown', function(e) {
            if (e.which === 13) { // Código 13 = Enter
                e.preventDefault();
                console.log("Enter pressionado em #quantidade_input");
                
                // Obter dados do produto
                const produtoId = $('#produto_id').val();
                const quantidade = parseInt($(this).val());
                
                if (!produtoId || isNaN(quantidade) || quantidade <= 0) {
                    alert("Verifique o ID do produto e a quantidade!");
                    return;
                }
                
                // Obter CSRF token
                const csrfToken = getCSRFToken();
                if (!csrfToken) {
                    console.error("CSRF token não encontrado!");
                    alert("Erro de segurança: Token CSRF não encontrado. Recarregue a página.");
                    return;
                }
                
                console.log("CSRF token obtido:", csrfToken);
                
                // Enviar AJAX
                $.ajax({
                    url: '/sistema/vendas/adicionar-item/',
                    method: 'POST',
                    dataType: 'html',
                    data: {
                        'produto_id': produtoId,
                        'quantidade': quantidade
                    },
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    success: function(data) {
                        console.log("Item adicionado com sucesso");
                        
                        // Atualizar carrinho
                        $('#itens_venda').html(data);
                        
                        // Fechar modal
                        $('#produtoModal').modal('hide');
                        
                        // Focar em #produto_input
                        setTimeout(function() {
                            $('#produto_input').focus();
                        }, 300);
                    },
                    error: function(xhr, status, error) {
                        console.error("Erro ao adicionar item:", error);
                        console.error("Status:", status);
                        console.error("Resposta:", xhr.responseText);
                        alert("Erro ao adicionar item. Verifique o console para detalhes.");
                    }
                });
            }
        });
    }
    
    // 2. Verificar se existe o botão #btn_adicionar_carrinho
    const btnAdicionar = $('#btn_adicionar_carrinho');
    if (btnAdicionar.length) {
        console.log("Encontrado #btn_adicionar_carrinho, configurando evento de clique...");
        
        btnAdicionar.on('click', function(e) {
            e.preventDefault();
            console.log("Clique em #btn_adicionar_carrinho");
            
            // Simular o Enter no input de quantidade
            const enterEvent = $.Event('keydown');
            enterEvent.which = 13;
            $('#quantidade_input').trigger(enterEvent);
        });
    }
    
    console.log("Configuração de compatibilidade concluída");
});