/**
 * PDV - Correção do Fluxo de Cursor e Atalhos de Teclado
 * Este arquivo deve ser incluído APÓS o pdv.js e fix-pdv.js
 *
 * Restaura o fluxo original de venda:
 * 1. F1 seleciona o input do PDV
 * 2. Enter seleciona o produto e abre o modal de quantidade
 * 3. Enter adiciona o produto ao carrinho
 * 4. F2 vai para o input de desconto
 * 5. F3 seleciona o método de pagamento
 * 6. F4 finaliza a venda
 */

(function () {
  console.log("PDV Cursor Fix - Inicializando correção do fluxo de cursor");

  // Aguardar o carregamento completo do DOM
  document.addEventListener("DOMContentLoaded", function () {
    inicializarCorrecaoCursor();
  });

  // Se o DOM já estiver carregado, inicializar imediatamente
  if (
    document.readyState === "complete" ||
    document.readyState === "interactive"
  ) {
    setTimeout(inicializarCorrecaoCursor, 100);
  }

  function inicializarCorrecaoCursor() {
    console.log("Inicializando correção do fluxo de cursor do PDV");

    // Elementos principais do PDV
    const elementos = {
      inputCodigo: document.getElementById("codigo_produto"),
      inputDesconto: document.getElementById("desconto"),
      selectMetodoPagamento: document.getElementById("metodo_pagamento"),
      inputCliente: document.querySelector("input[name='cliente']"),
      btnFinalizar: document.getElementById("btn-finalizar"),
      modalQuantidade: document.getElementById("modalQuantidade"),
      inputQuantidade: document.getElementById("product-quantity"),
      btnAdicionarCarrinho: document.getElementById("add-to-cart"),
    };

    // Verificar elementos encontrados
    console.log(
      "Elementos encontrados:",
      Object.entries(elementos)
        .map(([k, v]) => `${k}: ${v ? "Sim" : "Não"}`)
        .join(", ")
    );

    // Variável de controle do fluxo
    let etapaAtual = 0;

    // Remover eventos de teclado existentes para evitar conflitos
    const oldKeydownHandler = document.onkeydown;
    document.onkeydown = null;

    // Adicionar novo handler global de teclado
    document.addEventListener(
      "keydown",
      function (event) {
        // Ignorar eventos em campos de texto que não fazem parte do fluxo
        if (
          event.target.tagName === "INPUT" &&
          event.target.type === "text" &&
          event.target !== elementos.inputCodigo &&
          event.target !== elementos.inputQuantidade &&
          event.target !== elementos.inputDesconto &&
          event.target !== elementos.inputCliente
        ) {
          return;
        }

        // F1 - Foco no input de código/busca
        if (event.key === "F1") {
          event.preventDefault();
          if (elementos.inputCodigo) {
            console.log("F1: Focando no input de código do produto");
            elementos.inputCodigo.focus();
            elementos.inputCodigo.select();
            etapaAtual = 1;
          }
          return;
        }

        // F2 - Desconto
        if (event.key === "F2") {
          event.preventDefault();
          if (elementos.inputDesconto) {
            console.log("F2: Focando no input de desconto");
            elementos.inputDesconto.focus();
            elementos.inputDesconto.select();
            etapaAtual = 2;
          }
          return;
        }

        // F3 - Método de Pagamento
        if (event.key === "F3") {
          event.preventDefault();
          if (elementos.selectMetodoPagamento) {
            console.log("F3: Focando no select de método de pagamento");
            elementos.selectMetodoPagamento.focus();
            etapaAtual = 3;
          }
          return;
        }

        // F4 - Finalizar Venda
        if (event.key === "F4") {
          event.preventDefault();
          if (elementos.btnFinalizar) {
            console.log("F4: Clicando no botão finalizar venda");
            elementos.btnFinalizar.click();
            etapaAtual = 0;
          }
          return;
        }

        // ENTER - Comportamento baseado na etapa atual
        if (event.key === "Enter") {
          // Se estiver no modal de quantidade
          if (
            elementos.modalQuantidade &&
            elementos.modalQuantidade.classList.contains("show") &&
            elementos.inputQuantidade === document.activeElement
          ) {
            event.preventDefault();
            console.log(
              "Enter no modal de quantidade: adicionando ao carrinho"
            );

            if (elementos.btnAdicionarCarrinho) {
              elementos.btnAdicionarCarrinho.click();
            }

            // Após adicionar ao carrinho, voltar para o input de código
            setTimeout(function () {
              if (elementos.inputCodigo) {
                elementos.inputCodigo.focus();
                elementos.inputCodigo.select();
                etapaAtual = 1;
              }
            }, 500);

            return;
          }

          // Se estiver no input de código (etapa 1)
          if (
            etapaAtual === 1 &&
            document.activeElement === elementos.inputCodigo
          ) {
            event.preventDefault();
            console.log("Enter no input de código: selecionando produto");

            const codigo = elementos.inputCodigo.value.trim();
            if (!codigo) return;

            // Buscar produto pelo código ou nome
            buscarESelecionarProduto(codigo);
            return;
          }
        }
      },
      true
    ); // Usar captura para garantir que este handler seja executado primeiro

    // Função para buscar e selecionar produto
    function buscarESelecionarProduto(codigo) {
      console.log("Buscando produto com código/nome:", codigo);

      const produtos = Array.from(
        document.querySelectorAll(
          "#products-grid tbody tr.product-item, .produto-item, [data-id]"
        )
      );
      if (produtos.length === 0) {
        console.warn("Nenhum produto encontrado na página");
        return;
      }

      console.log(`Encontrados ${produtos.length} produtos para busca`);

      // Primeiro tenta buscar por código exato
      let produtoSelecionado = produtos.find(
        (p) =>
          p.getAttribute("data-code") === codigo ||
          p.getAttribute("data-codigo") === codigo
      );

      // Se não encontrar, tenta por nome exato (case insensitive)
      if (!produtoSelecionado) {
        produtoSelecionado = produtos.find((p) => {
          const nome =
            p.getAttribute("data-name") || p.getAttribute("data-nome");
          return nome && nome.toLowerCase() === codigo.toLowerCase();
        });
      }

      // Se ainda não encontrou, busca por nome parcial
      if (!produtoSelecionado && codigo.length >= 3) {
        produtoSelecionado = produtos.find((p) => {
          const nome =
            p.getAttribute("data-name") || p.getAttribute("data-nome");
          return nome && nome.toLowerCase().includes(codigo.toLowerCase());
        });
      }

      if (produtoSelecionado) {
        console.log(
          "Produto encontrado:",
          produtoSelecionado.getAttribute("data-name") ||
            produtoSelecionado.getAttribute("data-nome")
        );

        // Simular clique no produto para abrir o modal
        produtoSelecionado.click();

        // Garantir que o foco vá para o input de quantidade
        setTimeout(function () {
          if (elementos.inputQuantidade) {
            elementos.inputQuantidade.focus();
            elementos.inputQuantidade.select();
          }
        }, 500);
      } else {
        console.warn("Produto não encontrado com o código/nome:", codigo);

        // Usar SweetAlert se disponível, senão alert padrão
        if (typeof Swal !== "undefined") {
          Swal.fire({
            title: "Produto não encontrado",
            text: "Verifique o código ou nome do produto",
            icon: "warning",
            confirmButtonText: "OK",
          }).then(() => {
            // Voltar o foco para o input de código
            if (elementos.inputCodigo) {
              elementos.inputCodigo.focus();
              elementos.inputCodigo.select();
            }
          });
        } else {
          alert(
            "Produto não encontrado. Verifique o código ou nome do produto."
          );
          // Voltar o foco para o input de código
          if (elementos.inputCodigo) {
            elementos.inputCodigo.focus();
            elementos.inputCodigo.select();
          }
        }
      }
    }

    // Configurar evento Enter no input de quantidade
    if (elementos.inputQuantidade) {
      // Remover eventos existentes
      const novoInput = elementos.inputQuantidade.cloneNode(true);
      elementos.inputQuantidade.parentNode.replaceChild(
        novoInput,
        elementos.inputQuantidade
      );
      elementos.inputQuantidade = novoInput;

      // Adicionar novo evento
      elementos.inputQuantidade.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          console.log("Enter pressionado no input de quantidade");

          if (elementos.btnAdicionarCarrinho) {
            elementos.btnAdicionarCarrinho.click();

            // Após adicionar ao carrinho, voltar para o input de código
            setTimeout(function () {
              if (elementos.inputCodigo) {
                elementos.inputCodigo.focus();
                elementos.inputCodigo.select();
                etapaAtual = 1;
              }
            }, 500);
          }
        }
      });
    }

    // Iniciar o fluxo focando no input de código
    if (elementos.inputCodigo) {
      console.log("Iniciando fluxo: focando no input de código");
      setTimeout(function () {
        elementos.inputCodigo.focus();
        elementos.inputCodigo.select();
        etapaAtual = 1;
      }, 500);
    }

    console.log("Correção do fluxo de cursor do PDV inicializada com sucesso");
  }
})();
