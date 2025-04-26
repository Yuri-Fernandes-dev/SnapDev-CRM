/**
 * CORREÇÃO EMERGENCIAL - CLIQUE NOS PRODUTOS
 * Este arquivo deve ser incluído APÓS o pdv.js original
 */
(function() {
    console.log("=== INICIALIZANDO FIX-PDV.JS ===");
    console.log("Versão da correção: 2.0.1");
    console.log("Data: " + new Date().toLocaleString());
    
    // Função para debugging
    function debugElemento(elemento, mensagem) {
        if (!elemento) {
            console.error(`DEBUG [${mensagem}]: Elemento não encontrado`);
            return;
        }
        
        console.log(`DEBUG [${mensagem}]: Elemento encontrado`, {
            id: elemento.id,
            tagName: elemento.tagName,
            classes: Array.from(elemento.classList),
            atributos: Array.from(elemento.attributes).map(attr => `${attr.name}="${attr.value}"`),
            conteudo: elemento.textContent.trim().substring(0, 100)
        });
    }
    
    // Log de todos os elementos principais
    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOM carregado - Diagnóstico de elementos importantes");
        
        // Log para encontrar botões de adicionar ao carrinho
        const botoesCarrinho = document.querySelectorAll('button, .btn, [type="button"]');
        console.log(`Encontrados ${botoesCarrinho.length} botões na página:`);
        botoesCarrinho.forEach(btn => {
            if (btn.id || btn.className.includes('btn') || btn.textContent.toLowerCase().includes('carrinho') || btn.textContent.toLowerCase().includes('adicionar')) {
                debugElemento(btn, `Possível botão de carrinho`);
            }
        });
        
        // Log para encontrar modais
        const modais = document.querySelectorAll('.modal');
        console.log(`Encontrados ${modais.length} modais na página:`);
        modais.forEach(modal => debugElemento(modal, 'Modal'));
        
        // Log para encontrar formulários
        const forms = document.querySelectorAll('form');
        console.log(`Encontrados ${forms.length} formulários na página:`);
        forms.forEach(form => debugElemento(form, 'Formulário'));
    });
    
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

    // Função para obter valor de cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Verifica se o cookie começa com o nome desejado
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Função para adicionar produto ao carrinho via AJAX
    function adicionarAoCarrinhoAjax(produtoId, quantidade) {
        console.log(`Iniciando adição ao carrinho: Produto ID=${produtoId}, Quantidade=${quantidade}`);
        
        // Para debugging
        console.log("Dados do produto a adicionar:", {
            produtoId: produtoId,
            quantidade: quantidade
        });
        
        // Verificar se produto_id é uma string ou número
        if (!produtoId) {
            console.error("ID do produto é inválido");
            alert("Erro: ID do produto inválido");
            return;
        }
        
        // Verificar se quantidade é um número
        if (isNaN(parseInt(quantidade)) || parseInt(quantidade) <= 0) {
            console.error("Quantidade inválida");
            alert("Erro: Quantidade deve ser maior que zero");
            return;
        }
        
        // Preparar formData para garantir consistência
        const formData = new FormData();
        formData.append('produto_id', produtoId);
        formData.append('quantidade', quantidade);
        
        // Mostrar loader ou indicador de carregamento
        console.log("Enviando requisição AJAX para adicionar produto");
        
        // Usar Fetch API em vez de jQuery para mais compatibilidade
        fetch('/sistema/vendas/adicionar-item/', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                console.error("Erro na resposta:", response.status, response.statusText);
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            console.log("Produto adicionado com sucesso!");
            console.log("Buscando elementos para atualizar o carrinho");
            
            // DEBUG: Imprimir a resposta HTML recebida (primeiros 100 caracteres)
            console.log("Resposta HTML recebida (truncada):", html.substring(0, 100) + "...");
            
            // Tentar vários seletores conhecidos para o carrinho
            const cartSelectors = [
                '#cart-items',
                '#items-cart-container',
                '#itens_venda',
                '.cart-items-section'
            ];
            
            let cartUpdated = false;
            
            for (const selector of cartSelectors) {
                const element = document.querySelector(selector);
                if (element) {
                    console.log(`Encontrado elemento de carrinho: ${selector}`);
                    
                    // Se for o #cart-items, precisamos atualizar o conteúdo diretamente
                    if (selector === '#cart-items') {
                        // Tentar atualizar o cart global se ele existir
                        if (typeof window.cart !== 'undefined') {
                            try {
                                // Atualizar carrinho global com os dados da sessão
                                const carrinho = JSON.parse(sessionStorage.getItem('carrinho') || '[]');
                                window.cart = carrinho;
                                
                                // Chamar renderCartItems se existir
                                if (typeof window.renderCartItems === 'function') {
                                    window.renderCartItems();
                                    cartUpdated = true;
                                    console.log("Carrinho atualizado via renderCartItems()");
                                }
                            } catch (e) {
                                console.error("Erro ao atualizar carrinho global:", e);
                            }
                        }
                        
                        // Se não conseguir atualizar via função, substituir HTML diretamente
                        if (!cartUpdated) {
                            element.innerHTML = html;
                            cartUpdated = true;
                            console.log("Carrinho atualizado via innerHTML");
                        }
                    } else {
                        // Para outros seletores, apenas substituir o HTML
                        element.innerHTML = html;
                        cartUpdated = true;
                        console.log(`Carrinho atualizado via elemento ${selector}`);
                    }
                    
                    break;
                }
            }
            
            // Se nenhum elemento foi encontrado, tentar injetar no elemento pai
            if (!cartUpdated) {
                console.warn("Nenhum elemento de carrinho conhecido foi encontrado, tentando alternativas");
                
                // Buscar elementos que possam conter o carrinho
                const cartContainers = [
                    document.querySelector('.cart-items-section'),
                    document.querySelector('.cart-container'),
                    document.querySelector('.card-body')
                ];
                
                for (const container of cartContainers) {
                    if (container) {
                        // Criar um novo elemento div para o carrinho
                        const newCartElement = document.createElement('div');
                        newCartElement.id = 'items-cart-container';
                        newCartElement.innerHTML = html;
                        
                        // Substituir o conteúdo ou adicionar ao final
                        container.innerHTML = '';
                        container.appendChild(newCartElement);
                        
                        console.log("Carrinho criado e injetado em um container alternativo");
                        cartUpdated = true;
                        break;
                    }
                }
            }
            
            // Último recurso - recarregar a página
            if (!cartUpdated) {
                console.warn("Não foi possível atualizar o carrinho na interface, recarregando a página");
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
            
            // Fechar o modal
            const quantModal = document.getElementById('modalQuantidade');
            if (quantModal) {
                const bsModal = bootstrap.Modal.getInstance(quantModal);
                if (bsModal) bsModal.hide();
            } else {
                const produtoModal = document.getElementById('produtoModal');
                if (produtoModal) {
                    const bsModal = bootstrap.Modal.getInstance(produtoModal);
                    if (bsModal) bsModal.hide();
                }
            }
            
            // Limpar o campo de quantidade
            const quantidadeInput = document.getElementById('quantidade_input');
            if (quantidadeInput) {
                quantidadeInput.value = '';
            }
            
            // Atualizar o contador de itens e total se existirem
            atualizarContadoresCarrinho();
            
            // Mostrar mensagem de sucesso
            if (typeof Swal !== 'undefined') {
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
            } else {
                alert("Produto adicionado ao carrinho!");
            }
        })
        .catch(error => {
            console.error("Erro ao adicionar produto:", error);
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'error',
                    title: 'Erro ao adicionar produto',
                    text: 'Verifique o console para mais detalhes.'
                });
            } else {
                alert("Erro ao adicionar produto ao carrinho. Verifique o console para detalhes.");
            }
        });
    }

    // Função para atualizar os contadores e totais do carrinho
    function atualizarContadoresCarrinho() {
        // Tentar obter os elementos de subtotal e total
        const subtotalElement = document.getElementById('subtotal');
        const totalElement = document.getElementById('total');
        
        // Se encontrar os elementos, buscar os dados do carrinho e atualizar
        if (subtotalElement || totalElement) {
            console.log("Atualizando contadores do carrinho");
            
            // Fazer uma requisição para obter os dados atualizados do carrinho
            fetch('/sistema/vendas/pdv/')
                .then(response => response.text())
                .then(html => {
                    // Criar um DOM temporário para extrair valores
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    
                    // Atualizar subtotal
                    if (subtotalElement) {
                        const newSubtotal = doc.getElementById('subtotal')?.textContent;
                        if (newSubtotal) {
                            subtotalElement.textContent = newSubtotal;
                            console.log("Subtotal atualizado:", newSubtotal);
                        }
                    }
                    
                    // Atualizar total
                    if (totalElement) {
                        const newTotal = doc.getElementById('total')?.textContent;
                        if (newTotal) {
                            totalElement.textContent = newTotal;
                            console.log("Total atualizado:", newTotal);
                        }
                    }
                })
                .catch(error => {
                    console.error("Erro ao atualizar contadores do carrinho:", error);
                });
        }
    }

    // Configurar botão de adicionar ao carrinho
    function setupAddToCartButton() {
        console.log("Configurando botão de adicionar ao carrinho");
        
        // Encontrar o botão
        const btnAdicionar = document.getElementById('btnAdicionarAoCarrinho');
        
        if (btnAdicionar) {
            console.log("Botão encontrado, configurando evento de clique");
            
            // Remover qualquer listener anterior para evitar duplicação
            const newBtn = btnAdicionar.cloneNode(true);
            btnAdicionar.parentNode.replaceChild(newBtn, btnAdicionar);
            
            // Adicionar handler para o botão
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("Botão Adicionar ao Carrinho clicado");
                
                // Obter dados do formulário
                const produtoId = document.getElementById('produto_id')?.value;
                const quantidade = document.getElementById('quantidade_input')?.value;
                
                console.log(`Validando dados: Produto ID=${produtoId}, Quantidade=${quantidade}`);
                
                // Validar os dados
                if (!produtoId || produtoId <= 0) {
                    console.error("Produto inválido");
                    alert("Produto inválido");
                    return;
                }
                
                if (!quantidade || quantidade <= 0) {
                    console.error("Quantidade inválida");
                    alert("Quantidade deve ser maior que zero");
                    return;
                }
                
                // Adicionar ao carrinho
                adicionarAoCarrinhoAjax(produtoId, quantidade);
            });
        } else {
            console.log("Botão não encontrado, procurando alternativas...");
            
            // Tentar encontrar botões alternativos
            const alternativeButtons = [
                document.getElementById('add-to-cart'),
                document.querySelector('.btn[data-action="adicionar"]'),
                document.querySelector('.btn-adicionar-carrinho')
            ];
            
            // Procurar por qualquer botão que possa ser o correto
            for (const btn of alternativeButtons) {
                if (btn) {
                    console.log("Botão alternativo encontrado:", btn);
                    
                    // Remover qualquer listener anterior para evitar duplicação
                    const newBtn = btn.cloneNode(true);
                    btn.parentNode.replaceChild(newBtn, btn);
                    
                    // Adicionar handler para o botão
                    newBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        console.log("Botão alternativo clicado");
                        
                        // Tentar obter informações do dataset
                        const produtoId = this.dataset.id || document.getElementById('produto_id')?.value;
                        const quantidade = document.getElementById('quantidade_input')?.value || document.getElementById('product-quantity')?.value || 1;
                        
                        console.log(`Validando dados alternativos: Produto ID=${produtoId}, Quantidade=${quantidade}`);
                        
                        // Validar os dados
                        if (!produtoId) {
                            console.error("Produto inválido");
                            alert("Produto inválido");
                            return;
                        }
                        
                        // Adicionar ao carrinho
                        adicionarAoCarrinhoAjax(produtoId, quantidade);
                    });
                    
                    break;
                }
            }
        }
    }

    // Configurar input de quantidade
    function setupQuantityInput() {
        console.log("Configurando input de quantidade");
        
        // Encontrar input de quantidade
        const inputQuantidade = document.getElementById('quantidade_input');
        
        if (inputQuantidade) {
            console.log("Input encontrado, configurando evento de keydown");
            
            // Remover qualquer listener anterior para evitar duplicação
            const newInput = inputQuantidade.cloneNode(true);
            inputQuantidade.parentNode.replaceChild(newInput, inputQuantidade);
            
            // Adicionar handler para o input
            newInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    console.log("Tecla Enter pressionada no input de quantidade");
                    e.preventDefault();
                    
                    // Obter botão de adicionar
                    const btnAdicionar = document.getElementById('btnAdicionarAoCarrinho');
                    if (btnAdicionar) {
                        btnAdicionar.click();
                    } else {
                        // Tentar alternativas
                        const alternativeButtons = [
                            document.getElementById('add-to-cart'),
                            document.getElementById('btnAdicionarAoCarrinho'),
                            document.querySelector('.btn[data-action="adicionar"]'),
                            document.querySelector('.btn-adicionar-carrinho')
                        ];
                        
                        for (const btn of alternativeButtons) {
                            if (btn) {
                                btn.click();
                                break;
                            }
                        }
                    }
                }
            });
            
            // Garantir que o foco esteja no input quando o modal abrir
            const modalQuantidade = document.getElementById('quantidadeModal');
            if (modalQuantidade) {
                modalQuantidade.addEventListener('shown.bs.modal', function() {
                    console.log("Modal aberto - focando no input de quantidade");
                    
                    // Usar setTimeout para garantir que o foco funcione
                    setTimeout(function() {
                        newInput.focus();
                        newInput.select();
                    }, 100);
                });
            }
        } else {
            console.log("Input de quantidade não encontrado, procurando alternativas...");
            
            // Tentar encontrar inputs alternativos
            const alternativeInputs = [
                document.getElementById('product-quantity'),
                document.querySelector('input[data-field="quantity"]'),
                document.querySelector('.quantity-input')
            ];
            
            // Procurar por qualquer input que possa ser o correto
            for (const input of alternativeInputs) {
                if (input) {
                    console.log("Input alternativo encontrado:", input);
                    
                    // Remover qualquer listener anterior para evitar duplicação
                    const newInput = input.cloneNode(true);
                    input.parentNode.replaceChild(newInput, input);
                    
                    // Adicionar handler para o input
                    newInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            console.log("Tecla Enter pressionada no input alternativo");
                            e.preventDefault();
                            
                            // Tentar obter o botão adequado e clicar nele
                            const alternativeButtons = [
                                document.getElementById('add-to-cart'),
                                document.getElementById('btnAdicionarAoCarrinho'),
                                document.querySelector('.btn[data-action="adicionar"]'),
                                document.querySelector('.btn-adicionar-carrinho')
                            ];
                            
                            for (const btn of alternativeButtons) {
                                if (btn) {
                                    btn.click();
                                    break;
                                }
                            }
                        }
                    });
                    
                    // Garantir que o foco esteja no input quando o modal abrir
                    const modalAberto = document.querySelector('.modal.show');
                    if (modalAberto) {
                        console.log("Modal encontrado - focando no input alternativo");
                        
                        // Usar setTimeout para garantir que o foco funcione
                        setTimeout(function() {
                            newInput.focus();
                            newInput.select();
                        }, 100);
                    }
                    
                    break;
                }
            }
        }
    }

    // Configurar cliques nos produtos
    function setupProductClicks() {
        console.log("Configurando cliques nos produtos");
        
        // Tenta encontrar os produtos usando diferentes seletores
        const produtoItems = document.querySelectorAll('.produto-item, tr.product-item, .product-card');
        
        if (produtoItems.length > 0) {
            console.log(`Encontrados ${produtoItems.length} produtos, configurando eventos de clique`);
            
            // Adicionar handler para cliques nos produtos
            produtoItems.forEach(produto => {
                // Remover listener antigo clonando o elemento
                const clone = produto.cloneNode(true);
                produto.parentNode.replaceChild(clone, produto);
                
                // Adicionar novo evento de clique
                clone.addEventListener('click', function() {
                    // Tentar obter dados do produto de atributos data-*
                    const produtoId = this.getAttribute('data-id') || this.dataset.id;
                    const nomeProduto = this.getAttribute('data-name') || this.dataset.name;
                    const precoProduto = this.getAttribute('data-price') || this.dataset.price;
                    const estoqueProduto = this.getAttribute('data-stock') || this.dataset.stock;
                    
                    console.log(`Produto clicado: ID=${produtoId}, Nome=${nomeProduto}, Preço=${precoProduto}, Estoque=${estoqueProduto}`);
                    
                    // Verificar estoque
                    if (estoqueProduto !== undefined && parseInt(estoqueProduto) <= 0) {
                        if (typeof Swal !== 'undefined') {
                            Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                        } else {
                            alert("Produto sem estoque. Este produto não está disponível no momento.");
                        }
                        return;
                    }
                    
                    // Tenta encontrar os elementos do modal por diferentes IDs
                    const modalQuantidade = document.getElementById('quantidadeModal') || document.getElementById('produtoModal');
                    const produtoIdInput = document.getElementById('produto_id');
                    const produtoNomeEl = document.getElementById('produto_nome') || document.getElementById('modal-product-name');
                    const produtoPrecoEl = document.getElementById('preco_produto') || document.getElementById('modal-product-price');
                    const quantidadeInput = document.getElementById('quantidade_input') || document.getElementById('product-quantity');
                    
                    // Preencher os dados no modal se encontrados
                    if (produtoIdInput) produtoIdInput.value = produtoId;
                    if (produtoNomeEl) produtoNomeEl.textContent = nomeProduto;
                    if (produtoPrecoEl) produtoPrecoEl.textContent = `R$ ${parseFloat(precoProduto).toFixed(2)}`;
                    if (quantidadeInput) {
                        quantidadeInput.value = "1";
                        
                        // Focar e selecionar o input após um delay para garantir que o modal esteja aberto
                        setTimeout(() => {
                            quantidadeInput.focus();
                            quantidadeInput.select();
                        }, 300);
                    }
                    
                    // Abrir o modal se encontrado
                    if (modalQuantidade) {
                        // Verificar se o Bootstrap 5 está disponível
                        if (typeof bootstrap !== 'undefined') {
                            const modal = new bootstrap.Modal(modalQuantidade);
                            modal.show();
                        } 
                        // Fallback para jQuery se disponível
                        else if (typeof $ !== 'undefined' && typeof $.fn.modal === 'function') {
                            $(modalQuantidade).modal('show');
                        }
                        // Última opção: tentar usar classe CSS
                        else {
                            modalQuantidade.classList.add('show');
                            modalQuantidade.style.display = 'block';
                            
                            // Adicionar backdrop
                            const backdrop = document.createElement('div');
                            backdrop.className = 'modal-backdrop fade show';
                            document.body.appendChild(backdrop);
                        }
                    } else {
                        console.error("Erro: Modal de quantidade não encontrado!");
                        
                        // Se não houver modal, tentar adicionar diretamente
                        adicionarAoCarrinhoAjax(produtoId, 1);
                    }
                });
            });
        } else {
            console.log("Nenhum produto encontrado, verificando alternativas...");
            
            // Verificar elementos de produtos alternativos
            const alternativeProdutos = document.querySelectorAll('.product, .item-produto, .produto');
            
            if (alternativeProdutos.length > 0) {
                console.log(`Encontrados ${alternativeProdutos.length} produtos alternativos`);
                
                alternativeProdutos.forEach(produto => {
                    // Remover listener antigo clonando o elemento
                    const clone = produto.cloneNode(true);
                    produto.parentNode.replaceChild(clone, produto);
                    
                    // Adicionar novo evento de clique
                    clone.addEventListener('click', function() {
                        // Tentar extrair ID e outros dados
                        let produtoId = this.getAttribute('data-id') || 
                                         this.dataset.id || 
                                         this.querySelector('[data-id]')?.dataset.id;
                        
                        // Se não encontrou ID, tentar extrair de um link
                        if (!produtoId) {
                            const link = this.querySelector('a[href*="produto"]');
                            if (link) {
                                const matches = link.href.match(/produto\/(\d+)/);
                                if (matches && matches[1]) {
                                    produtoId = matches[1];
                                }
                            }
                        }
                        
                        if (produtoId) {
                            console.log(`Produto alternativo clicado: ID=${produtoId}`);
                            
                            // Tentar abrir modal ou adicionar diretamente
                            const modalQuantidade = document.getElementById('quantidadeModal') || document.getElementById('produtoModal');
                            
                            if (modalQuantidade) {
                                // Preencher dado mínimo necessário
                                const produtoIdInput = document.getElementById('produto_id');
                                if (produtoIdInput) produtoIdInput.value = produtoId;
                                
                                // Abrir modal
                                if (typeof bootstrap !== 'undefined') {
                                    const modal = new bootstrap.Modal(modalQuantidade);
                                    modal.show();
                                } else if (typeof $ !== 'undefined') {
                                    $(modalQuantidade).modal('show');
                                }
                            } else {
                                // Adicionar diretamente com quantidade padrão 1
                                adicionarAoCarrinhoAjax(produtoId, 1);
                            }
                        } else {
                            console.error("Não foi possível identificar o ID do produto");
                        }
                    });
                });
            } else {
                console.warn("Nenhum elemento de produto encontrado na página");
            }
        }
    }

    // Garantir que o CSRF token esteja no DOM
    function ensureCSRFToken() {
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
    }

    // Função para buscar produtos com código curto ou texto
    function buscarProdutos(termo) {
        console.log(`Buscando produtos com termo: "${termo}"`);
        
        // Verificar se o termo é muito curto (menos de 3 caracteres)
        const termoCurto = termo.length < 3;
        const produtos = [];
        
        // Tenta encontrar os produtos usando diferentes seletores
        const produtoItems = document.querySelectorAll('.produto-item, tr.product-item, .product-card');
        
        if (produtoItems.length === 0) {
            console.warn("Nenhum produto encontrado na página.");
            return { encontrados: [], exato: null };
        }
        
        // Primeiro buscar correspondência exata
        let produtoExato = null;
        
        produtoItems.forEach(produto => {
            const codigo = (produto.getAttribute('data-code') || '').toLowerCase();
            const nome = (produto.getAttribute('data-name') || '').toLowerCase();
            const termoLower = termo.toLowerCase();
            
            // Verificar correspondência exata
            if (codigo === termoLower || nome === termoLower) {
                produtoExato = produto;
                produtos.push(produto);
            }
        });
        
        // Se não encontrou nenhum produto exato e o termo não é curto,
        // buscar produtos que contenham o termo
        if (!produtoExato && !termoCurto) {
            produtoItems.forEach(produto => {
                const codigo = (produto.getAttribute('data-code') || '').toLowerCase();
                const nome = (produto.getAttribute('data-name') || '').toLowerCase();
                const termoLower = termo.toLowerCase();
                
                if ((codigo.includes(termoLower) || nome.includes(termoLower)) 
                    && !produtos.includes(produto)) {
                    produtos.push(produto);
                }
            });
        }
        
        return {
            encontrados: produtos,
            exato: produtoExato
        };
    }
    
    // Função para mostrar modal de seleção de produtos
    function mostrarModalSelecaoProdutos(produtos) {
        console.log(`Mostrando modal de seleção para ${produtos.length} produtos encontrados`);
        
        if (produtos.length === 0) return;
        
        // Verificar se temos SweetAlert disponível
        if (typeof Swal === 'undefined') {
            // Fallback para alert básico
            alert("Múltiplos produtos encontrados. Por favor, especifique melhor sua busca.");
            return;
        }
        
        // Criar HTML para listar os produtos
        let html = '<div class="list-group">';
        
        produtos.forEach(produto => {
            const id = produto.getAttribute('data-id');
            const nome = produto.getAttribute('data-name');
            const codigo = produto.getAttribute('data-code');
            const preco = produto.getAttribute('data-price');
            
            html += `
                <button type="button" class="list-group-item list-group-item-action produto-selecao" data-id="${id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${nome}</strong>
                            <small class="d-block text-muted">Código: ${codigo}</small>
                        </div>
                        <span class="badge bg-primary rounded-pill">R$ ${parseFloat(preco).toFixed(2)}</span>
                    </div>
                </button>
            `;
        });
        
        html += '</div>';
        
        // Mostrar o modal com os produtos
        Swal.fire({
            title: 'Selecione um Produto',
            html: html,
            showCancelButton: true,
            showConfirmButton: false,
            cancelButtonText: 'Cancelar',
            width: '600px',
            didOpen: () => {
                // Adicionar eventos de clique aos produtos
                document.querySelectorAll('.produto-selecao').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const produtoId = this.getAttribute('data-id');
                        const produtoSelecionado = produtos.find(p => p.getAttribute('data-id') === produtoId);
                        
                        // Fechar o modal
                        Swal.close();
                        
                        // Selecionar o produto
                        if (produtoSelecionado) {
                            console.log(`Produto selecionado: ${produtoSelecionado.getAttribute('data-name')}`);
                            
                            // Verificar se o produto está sem estoque
                            const estoque = parseInt(produtoSelecionado.getAttribute('data-stock') || '0');
                            if (estoque <= 0) {
                                Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                                return;
                            }
                            
                            // Simular clique no produto
                            produtoSelecionado.click();
                        }
                    });
                });
            }
        });
    }
    
    // Hook para interceptar a busca pelo campo código_produto
    function setupProductSearchField() {
        const searchInput = document.getElementById('codigo_produto');
        if (!searchInput) {
            console.warn("Campo de busca não encontrado");
            return;
        }
        
        console.log("Configurando campo de busca de produtos");
        
        // Interceptar o evento keydown para tratar Enter
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                
                const termo = this.value.trim();
                if (!termo) return;
                
                console.log(`Termo de busca: "${termo}"`);
                
                // Verificar se o termo é muito curto
                if (termo.length < 3) {
                    // Para termos curtos, exigir correspondência exata
                    const { encontrados, exato } = buscarProdutos(termo);
                    
                    if (exato) {
                        // Verificar estoque do produto
                        const estoque = parseInt(exato.getAttribute('data-stock') || '0');
                        if (estoque <= 0) {
                            Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                            return;
                        }
                        
                        // Simular clique no produto
                        exato.click();
                    } else if (encontrados.length > 1) {
                        // Se encontrou múltiplos produtos, mostrar alerta
                        Swal.fire({
                            icon: 'info',
                            title: 'Código muito curto',
                            text: 'Para códigos curtos, insira o código exato do produto ou pelo menos 3 caracteres para busca.',
                            confirmButtonText: 'OK'
                        });
                    } else {
                        // Nenhum produto encontrado
                        Swal.fire('Produto não encontrado', 'Verifique o código ou digite mais caracteres para busca.', 'warning');
                    }
                } else {
                    // Para termos mais longos, buscar normalmente
                    const { encontrados, exato } = buscarProdutos(termo);
                    
                    if (exato) {
                        // Verificar estoque do produto
                        const estoque = parseInt(exato.getAttribute('data-stock') || '0');
                        if (estoque <= 0) {
                            Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                            return;
                        }
                        
                        // Simular clique no produto
                        exato.click();
                    } else if (encontrados.length === 1) {
                        // Apenas um produto encontrado, verificar estoque
                        const estoque = parseInt(encontrados[0].getAttribute('data-stock') || '0');
                        if (estoque <= 0) {
                            Swal.fire('Produto sem estoque', 'Este produto não está disponível no momento.', 'warning');
                            return;
                        }
                        
                        // Simular clique no produto
                        encontrados[0].click();
                    } else if (encontrados.length > 1) {
                        // Múltiplos produtos encontrados, mostrar modal de seleção
                        mostrarModalSelecaoProdutos(encontrados);
                    } else {
                        // Nenhum produto encontrado
                        Swal.fire('Produto não encontrado', 'Verifique o código ou digite mais caracteres para busca.', 'warning');
                    }
                }
                
                // Limpar o campo de busca
                this.value = '';
            }
        });
    }

    // Inicializar quando o DOM estiver carregado
    document.addEventListener('DOMContentLoaded', function() {
        console.log("DOM carregado - Inicializando configurações do PDV");
        
        // Garantir que o CSRF token esteja presente no DOM
        ensureCSRFToken();
        
        // Configurar o AJAX para incluir o CSRF token em todas as requisições
        if (typeof $ !== 'undefined') {
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
        }
        
        // Configurar os componentes
        setupProductClicks();
        setupQuantityInput();
        setupAddToCartButton();
        setupProductSearchField();
        
        // Log para confirmar inicialização
        console.log("PDV inicializado com sucesso!");
    });
})(); 