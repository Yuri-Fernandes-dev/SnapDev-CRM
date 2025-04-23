/**
 * PDV - Controle de atalhos de teclado e fluxo do PDV
 */
document.addEventListener("DOMContentLoaded", function () {
    let etapa = 0;

    window.addEventListener("keydown", function (event) {
        // Atalho F1: foco no input
        if (event.key === "F1") {
            event.preventDefault();
            document.getElementById("codigo_produto")?.focus();
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
            document.getElementById("metodo_pagamento")?.focus();
        }

        // F3: desconto
        if (event.key === "F3") {
            event.preventDefault();
            document.getElementById("desconto")?.focus();
        }

        // F4: finalizar venda
        if (event.key === "F4") {
            event.preventDefault();
            document.getElementById("btn-finalizar")?.click();
        }
    });

    // Funções auxiliares para o fluxo do PDV
    function selecionarProduto() {
        console.log("Produto selecionado");
        
        // Obter o valor do campo de código/busca
        const codigo = document.getElementById("codigo_produto").value.trim();
        if (!codigo) return;
        
        // Buscar produtos visíveis
        const produtos = Array.from(document.querySelectorAll('#products-grid tbody tr.product-item'))
            .filter(row => row.style.display !== 'none');
        
        // Selecionar o primeiro produto visível ou um que corresponda exatamente
        if (produtos.length > 0) {
            // Tentar encontrar correspondência exata com código
            const produtoExato = produtos.find(p => {
                const prodCodigo = p.getAttribute('data-code')?.toLowerCase() || '';
                return prodCodigo === codigo.toLowerCase();
            });
            
            // Selecionar produto encontrado ou o primeiro disponível
            const produtoSelecionado = produtoExato || produtos[0];
            
            // Limpar seleções anteriores
            produtos.forEach(p => {
                p.classList.remove('selected');
                p.style.outline = '';
            });
            
            // Destacar o produto selecionado
            produtoSelecionado.classList.add('selected');
            produtoSelecionado.style.outline = '2px solid #198754';
            produtoSelecionado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            console.log("Produto selecionado:", produtoSelecionado.getAttribute('data-name'));
        }
    }

    function abrirModalQuantidade() {
        console.log("Abrindo modal de quantidade");
        
        // Obter o produto selecionado
        const produtoSelecionado = document.querySelector('#products-grid tbody tr.selected');
        if (!produtoSelecionado) return;
        
        // Verificar se tem a função nativa do sistema para abrir o modal
        if (typeof selectProduct === 'function') {
            // Usar a função nativa do sistema
            selectProduct(produtoSelecionado);
        } else {
            // Abrir o modal manualmente
            const modal = new bootstrap.Modal(document.getElementById('modalQuantidade'));
            modal.show();
            
            // Preencher dados do produto no modal
            const nome = produtoSelecionado.getAttribute('data-name');
            const preco = produtoSelecionado.getAttribute('data-price');
            const estoque = produtoSelecionado.getAttribute('data-stock');
            
            document.getElementById('modal-product-name').textContent = nome;
            document.getElementById('modal-product-price').textContent = `R$ ${parseFloat(preco).toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            document.getElementById('modal-product-stock').textContent = estoque;
            document.getElementById('product-quantity').value = '1';
            
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
        if (!modal || !modal.classList.contains('show')) return;
        
        // Clicar no botão de adicionar ao carrinho
        const addButton = document.getElementById('add-to-cart');
        if (addButton) {
            addButton.click();
        }
    }
    
    // Mensagem inicial no console
    console.log("PDV.js carregado - Atalhos: F1=Produto, F2=Pagamento, F3=Desconto, F4=Finalizar");
}); 