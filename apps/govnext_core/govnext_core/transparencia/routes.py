# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

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
