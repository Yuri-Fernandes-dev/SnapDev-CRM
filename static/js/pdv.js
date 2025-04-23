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