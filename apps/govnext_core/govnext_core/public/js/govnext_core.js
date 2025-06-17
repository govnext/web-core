// GovNext Core - JavaScript Principal

frappe.provide("govnext");

govnext = {
    // Configuração global do GovNext
    config: {
        version: '0.0.1'
    },

    // Inicialização
    init: function() {
        this.setupCustomFilters();
        this.setupCustomFormatters();
        this.setupCustomValidations();
        console.log("GovNext Core inicializado - v" + this.config.version);
    },

    // Configurar filtros personalizados para listas
    setupCustomFilters: function() {
        if (!frappe.listview_settings) {
            frappe.listview_settings = {};
        }

        // Filtros personalizados para orçamentos
        frappe.listview_settings["Public Budget"] = {
            onload: function(listview) {
                listview.page.add_menu_item(__("Filtrar por Ano Fiscal Atual"), function() {
                    const today = frappe.datetime.get_today();
                    listview.filter_area.add("Fiscal Year", "Like", frappe.datetime.str_to_obj(today).year);
                });
            }
        };

        // Filtros personalizados para licitações
        frappe.listview_settings["Public Tender"] = {
            onload: function(listview) {
                listview.page.add_menu_item(__("Mostrar Licitações Ativas"), function() {
                    listview.filter_area.clear();
                    listview.filter_area.add("status", "not in", ["Concluído", "Revogado", "Anulado", "Fracassado", "Deserto"]);
                });

                listview.page.add_menu_item(__("Mostrar Licitações Encerradas"), function() {
                    listview.filter_area.clear();
                    listview.filter_area.add("status", "in", ["Concluído", "Revogado", "Anulado", "Fracassado", "Deserto"]);
                });
            }
        };
    },

    // Configurar formatadores personalizados para exibição de dados
    setupCustomFormatters: function() {
        // Formatador para valores monetários grandes (milhões, bilhões)
        frappe.form.formatters.LargeCurrency = function(value, df) {
            if (value == null || value === "") return "";

            let formattedValue = value;
            if (value >= 1e9) {
                formattedValue = (value / 1e9).toFixed(2) + " bi";
            } else if (value >= 1e6) {
                formattedValue = (value / 1e6).toFixed(2) + " mi";
            } else if (value >= 1e3) {
                formattedValue = (value / 1e3).toFixed(2) + " mil";
            }

            return frappe.form.formatters.Currency(formattedValue, df);
        };

        // Formatador para status de licitação
        frappe.form.formatters.TenderStatus = function(value) {
            if (!value) return "";

            let statusColor = "gray";

            switch(value) {
                case "Em Preparação":
                    statusColor = "blue";
                    break;
                case "Publicado":
                    statusColor = "orange";
                    break;
                case "Em Análise":
                    statusColor = "yellow";
                    break;
                case "Adjudicado":
                case "Homologado":
                    statusColor = "green";
                    break;
                case "Contratado":
                case "Concluído":
                    statusColor = "darkgreen";
                    break;
                case "Revogado":
                case "Anulado":
                case "Fracassado":
                case "Deserto":
                    statusColor = "red";
                    break;
            }

            return `<span class="indicator ${statusColor}">${value}</span>`;
        };
    },

    // Configurar validações personalizadas
    setupCustomValidations: function() {
        // Validação de CNPJ brasileiro
        frappe.ui.form.is_valid_cnpj = function(value) {
            if (!value) return false;

            // Remove caracteres não numéricos
            value = value.replace(/[^\d]+/g, '');

            // Deve ter exatamente 14 dígitos
            if (value.length !== 14) return false;

            // Verifica se todos os dígitos são iguais, o que é inválido
            if (/^(\d)\1+$/.test(value)) return false;

            // Validação dos dígitos verificadores
            let sum = 0;
            let weight = 2;

            // Primeiro dígito verificador
            for (let i = 11; i >= 0; i--) {
                sum += parseInt(value.charAt(i)) * weight;
                weight = (weight === 9) ? 2 : weight + 1;
            }

            let digit = 11 - (sum % 11);
            if (digit > 9) digit = 0;
            if (parseInt(value.charAt(12)) !== digit) return false;

            // Segundo dígito verificador
            sum = 0;
            weight = 2;

            for (let i = 12; i >= 0; i--) {
                sum += parseInt(value.charAt(i)) * weight;
                weight = (weight === 9) ? 2 : weight + 1;
            }

            digit = 11 - (sum % 11);
            if (digit > 9) digit = 0;

            return parseInt(value.charAt(13)) === digit;
        };
    }
};

// Iniciar GovNext quando o Frappe estiver pronto
$(document).ready(function() {
    if (frappe) {
        govnext.init();
    }
});
