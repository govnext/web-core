# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_context(context):
	"""
	Prepara o contexto para a página inicial do Portal da Transparência.

	Esta função carrega os dados necessários para exibir na página inicial,
	como serviços mais buscados, estatísticas e informações recentes.
	"""
	context.title = _("Portal da Transparência")
	context.subtitle = _("Fiscalize, questione e participe. Entenda como seu dinheiro está sendo usado. Transparência é confiança.")

	# Carrega os serviços mais buscados
	context.servicos_populares = get_servicos_populares()

	# Carrega estatísticas recentes
	context.estatisticas = get_estatisticas()

	# Carrega atualizações recentes
	context.atualizacoes_recentes = get_atualizacoes_recentes()

	# Carrega todos os serviços disponíveis
	context.todos_servicos = get_todos_servicos()

	# Carrega informações institucionais
	context.info_institucional = get_info_institucional()

	return context

def get_servicos_populares():
	"""Retorna os serviços mais buscados no portal."""
	return [
		{
			"titulo": _("Gestão de Pessoas"),
			"descricao": _("Consulte informações consolidadas sobre servidores, estrutura remuneratória, folha de pagamento, dentre outros."),
			"icone": "fa fa-users",
			"link": "/transparencia/gestao-pessoas"
		},
		{
			"titulo": _("Despesas"),
			"descricao": _("Demonstra os gastos da prefeitura, incluindo pagamentos realizados, destinatários, valores e descrição da despesa."),
			"icone": "fa fa-money-bill-alt",
			"link": "/transparencia/despesas"
		},
		{
			"titulo": _("Contratos"),
			"descricao": _("Acesse informações sobre todos os contratos firmados pela prefeitura, incluindo valores, fornecedores, vigências e objetos contratados."),
			"icone": "fa fa-file-contract",
			"link": "/transparencia/contratos"
		}
	]

def get_estatisticas():
	"""Retorna estatísticas recentes para exibir no portal."""
	# Em um ambiente real, esses dados viriam do banco de dados
	return {
		"orcamento_total": frappe.utils.fmt_money(100000000, currency="BRL"),
		"despesas_total": frappe.utils.fmt_money(45000000, currency="BRL"),
		"receitas_total": frappe.utils.fmt_money(52000000, currency="BRL"),
		"contratos_ativos": 156,
		"licitacoes_andamento": 23,
		"servidores_ativos": 1250
	}

def get_atualizacoes_recentes():
	"""Retorna as atualizações mais recentes do portal."""
	# Em um ambiente real, esses dados viriam do banco de dados
	return [
		{
			"titulo": _("Publicação do Relatório de Gestão Fiscal"),
			"data": "2025-06-10",
			"tipo": "Prestação de Contas",
			"link": "/transparencia/relatorio-gestao-fiscal-2025-q1"
		},
		{
			"titulo": _("Nova licitação para aquisição de medicamentos"),
			"data": "2025-06-05",
			"tipo": "Licitação",
			"link": "/transparencia/licitacao/2025-056"
		},
		{
			"titulo": _("Publicação da folha de pagamento de maio/2025"),
			"data": "2025-06-01",
			"tipo": "Folha de Pagamento",
			"link": "/transparencia/folha-pagamento/2025-05"
		}
	]

def get_todos_servicos():
	"""Retorna todos os serviços disponíveis no portal."""
	from apps.govnext_core.govnext_core.transparencia.portal.config import get_data

	servicos = []
	for secao in get_data():
		for item in secao.get("items", []):
			servicos.append({
				"titulo": item.get("label"),
				"descricao": item.get("description"),
				"link": get_item_link(item),
				"categoria": secao.get("label")
			})

	return servicos

def get_info_institucional():
	"""Retorna informações institucionais para exibir no rodapé."""
	return {
		"nome": _("Prefeitura Municipal de Exemplo"),
		"endereco": _("Rua Exemplo, 123 • Centro • Exemplo-UF • CEP. 12.345-678"),
		"telefone": _("(12) 3456-7890"),
		"email": "transparencia@exemplo.gov.br",
		"horario": _("Segunda a sexta, das 8h às 17h")
	}

def get_item_link(item):
	"""Gera o link para um item do menu."""
	tipo = item.get("type")
	nome = item.get("name")

	if tipo == "doctype":
		return f"/transparencia/list/{nome}"
	elif tipo == "page":
		return f"/transparencia/{nome}"
	else:
		return "#"
