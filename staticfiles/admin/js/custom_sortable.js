/**
 * Script para ordenar as colunas pelo cabeçalho
 */
(function($) {
    $(document).ready(function() {
        console.log("Script de ordenação do cabeçalho carregado");
        
        // Função para limpar strings monetárias (R$ 1.234,56 -> 1234.56)
        function parseMonetaryValue(text) {
            if (!text || text === '-') return 0;
            // Remove R$, espaços, pontos e substitui vírgula por ponto
            return parseFloat(text.replace(/R\$\s*/g, '')
                                .replace(/\./g, '')
                                .replace(/,/g, '.')
                                .trim());
        }
        
        // Adicionar ordenação para o cabeçalho "Lucro Total"
        $("#result_list th.column-total_profit").addClass("sortable").css("cursor", "pointer").on("click", function() {
            console.log("Cabeçalho Lucro Total clicado");
            
            // Verificar direção atual
            const isAscending = !$(this).hasClass("sorted-desc");
            
            // Atualizar classes de ordenação
            $("th").removeClass("sorted-asc sorted-desc");
            $(this).addClass(isAscending ? "sorted-desc" : "sorted-asc");
            
            // Obter todas as linhas
            const rows = $("#result_list tbody tr").get();
            
            // Ordenar pelo valor nas células da coluna
            const columnIndex = $(this).index();
            
            rows.sort(function(a, b) {
                const aValue = parseMonetaryValue($(a).find("td").eq(columnIndex).text());
                const bValue = parseMonetaryValue($(b).find("td").eq(columnIndex).text());
                
                // Ordem decrescente por padrão (maior primeiro)
                return isAscending ? bValue - aValue : aValue - bValue;
            });
            
            // Reorganizar as linhas na tabela
            $("#result_list tbody").empty();
            $.each(rows, function(index, row) {
                $("#result_list tbody").append(row);
            });
            
            // Atualizar as classes de linha alternada
            $("#result_list tbody tr").removeClass("row1 row2");
            $("#result_list tbody tr:even").addClass("row1");
            $("#result_list tbody tr:odd").addClass("row2");
            
            return false;
        });
        
        // Fazer o mesmo para Total em Vendas
        $("#result_list th.column-total_sales").addClass("sortable").css("cursor", "pointer").on("click", function() {
            console.log("Cabeçalho Total em Vendas clicado");
            
            const isAscending = !$(this).hasClass("sorted-desc");
            $("th").removeClass("sorted-asc sorted-desc");
            $(this).addClass(isAscending ? "sorted-desc" : "sorted-asc");
            
            const rows = $("#result_list tbody tr").get();
            const columnIndex = $(this).index();
            
            rows.sort(function(a, b) {
                const aValue = parseMonetaryValue($(a).find("td").eq(columnIndex).text());
                const bValue = parseMonetaryValue($(b).find("td").eq(columnIndex).text());
                return isAscending ? bValue - aValue : aValue - bValue;
            });
            
            $("#result_list tbody").empty();
            $.each(rows, function(index, row) {
                $("#result_list tbody").append(row);
            });
            
            $("#result_list tbody tr").removeClass("row1 row2");
            $("#result_list tbody tr:even").addClass("row1");
            $("#result_list tbody tr:odd").addClass("row2");
            
            return false;
        });
    });
})(django.jQuery); 