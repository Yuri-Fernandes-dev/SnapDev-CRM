/**
 * PDV - Controle de atalhos de teclado e fluxo do PDV (Versão Corrigida)
 */
document.addEventListener("DOMContentLoaded", function () {
    console.log("PDV.js carregado - Sistema de vendas inicializado");

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
        const produtoSelecionado = produtos.find(p => {
            return p.getAttribute('data-code') === codigo || 
                   p.getAttribute('data-name').toLowerCase() === codigo.toLowerCase();
        });

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
            Swal.fire('Produto não encontrado', 'Digite um código ou nome válido', 'info');
        }
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

        // Adiciona ao carrinho (usando sistema existente ou implementação alternativa)
        if (typeof addToCart === 'function') {
            // Usa função nativa do sistema
            addToCart(produtoId, quantidade);
        } else {
            // Implementação alternativa
            const item = {
                id: produtoId,
                price: parseFloat(produtoPreco),
                quantity: quantidade,
                // ... outros campos necessários
            };
            
            // Adiciona ao array do carrinho
            if (typeof cart !== 'undefined') {
                cart.push(item);
            }
            
            // Atualiza a UI
            if (typeof updateCartUI === 'function') {
                updateCartUI();
            }
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