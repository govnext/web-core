# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.website.router import resolve_route
from frappe.website.utils import build_response

# Rotas do Portal da Transparência
portal_routes = [
    {"from_route": "transparencia", "to_route": "transparencia/home"},
    {"from_route": "transparencia/home", "to_route": "transparencia_home"},

    # Serviços mais buscados
    {"from_route": "transparencia/gestao-pessoas", "to_route": "transparencia/gestao_pessoas"},
    {"from_route": "transparencia/despesas", "to_route": "transparencia/despesas"},
    {"from_route": "transparencia/contratos", "to_route": "transparencia/contratos"},

    # Mais serviços
    {"from_route": "transparencia/convenios-sem-repasse", "to_route": "transparencia/convenios_sem_repasse"},
    {"from_route": "transparencia/receitas", "to_route": "transparencia/receitas"},
    {"from_route": "transparencia/ordem-cronologica", "to_route": "transparencia/ordem_cronologica"},
    {"from_route": "transparencia/convenios-transferencias", "to_route": "transparencia/convenios_transferencias"},
    {"from_route": "transparencia/concursos", "to_route": "transparencia/concursos"},
    {"from_route": "transparencia/diarias", "to_route": "transparencia/diarias"},
    {"from_route": "transparencia/compras-licitacoes", "to_route": "transparencia/compras_licitacoes"},
    {"from_route": "transparencia/adesao-registro-preco", "to_route": "transparencia/adesao_registro_preco"},
    {"from_route": "transparencia/obras-publicas", "to_route": "transparencia/obras_publicas"},
    {"from_route": "transparencia/prestacao-contas", "to_route": "transparencia/prestacao_contas"},
    {"from_route": "transparencia/orcamento", "to_route": "transparencia/orcamento"},
    {"from_route": "transparencia/renuncias-receitas", "to_route": "transparencia/renuncias_receitas"},
    {"from_route": "transparencia/emendas-parlamentares", "to_route": "transparencia/emendas_parlamentares"},
    {"from_route": "transparencia/multas-receitas-despesas", "to_route": "transparencia/multas_receitas_despesas"},
    {"from_route": "transparencia/julgamento-contas", "to_route": "transparencia/julgamento_contas"},
    {"from_route": "transparencia/educacao", "to_route": "transparencia/educacao"},
    {"from_route": "transparencia/institucional", "to_route": "transparencia/institucional"},
    {"from_route": "transparencia/carta-servicos", "to_route": "transparencia/carta_servicos"},
    {"from_route": "transparencia/relatorio-atividades", "to_route": "transparencia/relatorio_atividades"},
    {"from_route": "transparencia/divida-ativa", "to_route": "transparencia/divida_ativa"},
    {"from_route": "transparencia/bolsa-familia", "to_route": "transparencia/bolsa_familia"},
    {"from_route": "transparencia/transferencias-recebidas", "to_route": "transparencia/transferencias_recebidas"},
    {"from_route": "transparencia/empresas-sancionadas", "to_route": "transparencia/empresas_sancionadas"},
    {"from_route": "transparencia/fiscais-contrato", "to_route": "transparencia/fiscais_contrato"},
    {"from_route": "transparencia/pesquisa-satisfacao", "to_route": "transparencia/pesquisa_satisfacao"},

    # Planejamentos
    {"from_route": "transparencia/metas-fiscais", "to_route": "transparencia/metas_fiscais"},
    {"from_route": "transparencia/plano-metas", "to_route": "transparencia/plano_metas"},

    # Você também pode estar procurando
    {"from_route": "transparencia/sic", "to_route": "transparencia/sic"},
    {"from_route": "transparencia/ouvidoria", "to_route": "transparencia/ouvidoria"},
    {"from_route": "transparencia/saude", "to_route": "transparencia/saude"},
    {"from_route": "transparencia/legislacao", "to_route": "transparencia/legislacao"},
    {"from_route": "transparencia/perguntas-frequentes", "to_route": "transparencia/perguntas_frequentes"},
    {"from_route": "transparencia/radar-transparencia", "to_route": "transparencia/radar_transparencia"},
    {"from_route": "transparencia/calendario-oficial", "to_route": "transparencia/calendario_oficial"},

    # Mais do Portal da Transparência
    {"from_route": "transparencia/orgao-oficial", "to_route": "transparencia/orgao_oficial"},
    {"from_route": "transparencia/assistencia-social", "to_route": "transparencia/assistencia_social"},
    {"from_route": "transparencia/covid-19", "to_route": "transparencia/covid19"},
    {"from_route": "transparencia/ajuda", "to_route": "transparencia/ajuda"},
    {"from_route": "transparencia/dados-antes-2016", "to_route": "transparencia/dados_antes_2016"},

    # API e busca
    {"from_route": "transparencia/busca", "to_route": "transparencia/busca"},
    {"from_route": "transparencia/api", "to_route": "transparencia/api"},
]

def get_website_rules():
    """Retorna as regras de roteamento para o portal de transparência."""
    rules = []

    for route in portal_routes:
        rules.append({
            "from_route": route["from_route"],
            "to_route": route["to_route"]
        })

    return rules

def get_routes():
	"""
	Define as rotas para o Portal da Transparência.

	Esta função mapeia URLs para funções específicas que renderizam as páginas
	do Portal da Transparência.
	"""
	return [
		{
			"route": "/transparencia",
			"template": "transparencia_home",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.home.get_context"
		},
		{
			"route": "/transparencia/despesas",
			"template": "transparencia_despesas",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.despesas.get_context"
		},
		{
			"route": "/transparencia/receitas",
			"template": "transparencia_receitas",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.receitas.get_context"
		},
		{
			"route": "/transparencia/contratos",
			"template": "transparencia_contratos",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.contratos.get_context"
		},
		{
			"route": "/transparencia/licitacoes",
			"template": "transparencia_licitacoes",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.licitacoes.get_context"
		},
		{
			"route": "/transparencia/servidores",
			"template": "transparencia_servidores",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.servidores.get_context"
		},
		{
			"route": "/transparencia/orcamento",
			"template": "transparencia_orcamento",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.orcamento.get_context"
		},
		{
			"route": "/transparencia/obras",
			"template": "transparencia_obras",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.obras.get_context"
		},
		{
			"route": "/transparencia/convenios",
			"template": "transparencia_convenios",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.convenios.get_context"
		},
		{
			"route": "/transparencia/prestacao-contas",
			"template": "transparencia_prestacao_contas",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.prestacao_contas.get_context"
		},
		{
			"route": "/transparencia/gestao-pessoas",
			"template": "transparencia_gestao_pessoas",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.gestao_pessoas.get_context"
		},
		{
			"route": "/transparencia/servicos",
			"template": "transparencia_servicos",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.servicos.get_context"
		},
		{
			"route": "/transparencia/busca",
			"template": "transparencia_busca",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.busca.get_context"
		},
		{
			"route": "/transparencia/ajuda",
			"template": "transparencia_ajuda",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.ajuda.get_context"
		},
		{
			"route": "/transparencia/perguntas-frequentes",
			"template": "transparencia_faq",
			"controller": "apps.govnext_core.govnext_core.transparencia.portal.faq.get_context"
		}
	]
