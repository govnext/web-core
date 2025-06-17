# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months, get_first_day, get_last_day

def get_context(context):
	"""
	Prepara o contexto para a página de despesas do Portal da Transparência.

	Esta função carrega os dados de despesas para exibição, incluindo filtros,
	gráficos e tabelas detalhadas.
	"""
	context.title = _("Despesas Públicas")
	context.subtitle = _("Demonstra os gastos da prefeitura, incluindo pagamentos realizados, destinatários, valores e descrição da despesa.")

	# Obtém parâmetros de filtro da URL
	filters = get_filters_from_request()
	context.filters = filters

	# Carrega os dados de despesas com base nos filtros
	context.despesas = get_despesas(filters)

	# Calcula totais e estatísticas
	context.totais = calcular_totais(context.despesas)

	# Prepara dados para gráficos
	context.graficos = preparar_graficos(context.despesas)

	# Carrega dados para filtros dinâmicos
	context.opcoes_filtro = get_opcoes_filtro()

	return context

def get_filters_from_request():
	"""Extrai e processa os filtros da requisição."""
	return {
		"ano": frappe.form_dict.get("ano") or str(getdate().year),
		"mes": frappe.form_dict.get("mes") or str(getdate().month),
		"orgao": frappe.form_dict.get("orgao"),
		"categoria": frappe.form_dict.get("categoria"),
		"fornecedor": frappe.form_dict.get("fornecedor"),
		"valor_min": flt(frappe.form_dict.get("valor_min") or 0),
		"valor_max": flt(frappe.form_dict.get("valor_max") or 0),
		"page": int(frappe.form_dict.get("page") or 1)
	}

def get_despesas(filters):
	"""
	Obtém as despesas com base nos filtros aplicados.

	Em um ambiente real, isso faria consultas ao banco de dados.
	Aqui estamos simulando dados para demonstração.
	"""
	# Em um ambiente real, isso seria uma consulta ao banco de dados
	# Aqui estamos retornando dados simulados para demonstração

	# Simula uma lista de despesas
	despesas = []

	# Filtra por ano e mês, se especificados
	ano = int(filters.get("ano") or getdate().year)
	mes = int(filters.get("mes") or getdate().month)

	# Define o período de início e fim para filtrar
	data_inicio = get_first_day(f"{ano}-{mes:02d}-01")
	data_fim = get_last_day(data_inicio)

	# Simula a consulta ao banco de dados
	empenhos = frappe.get_all(
		"Empenho",
		filters={
			"data_empenho": ["between", [data_inicio, data_fim]],
			"orgao_publico": filters.get("orgao") or ["!=", ""],
			"categoria_despesa": filters.get("categoria") or ["!=", ""],
			"fornecedor": filters.get("fornecedor") or ["!=", ""]
		},
		fields=["name", "numero_empenho", "data_empenho", "valor_total",
				"orgao_publico", "categoria_despesa", "fornecedor", "descricao"],
		order_by="data_empenho desc",
		start=(filters.get("page") - 1) * 20,
		page_length=20
	)

	# Se não houver empenhos reais no banco, gera dados simulados
	if not empenhos:
		# Simulação de dados para demonstração
		import random
		from datetime import datetime, timedelta

		categorias = ["Pessoal", "Material de Consumo", "Serviços", "Obras", "Equipamentos"]
		orgaos = ["Secretaria de Administração", "Secretaria de Educação", "Secretaria de Saúde"]
		fornecedores = ["Empresa A Ltda", "Empresa B S.A.", "Empresa C Ltda", "Autônomo D"]

		for i in range(20):
			data = data_inicio + timedelta(days=random.randint(0, (data_fim - data_inicio).days))
			categoria = random.choice(categorias)
			orgao = random.choice(orgaos)
			fornecedor = random.choice(fornecedores)
			valor = random.uniform(1000, 100000)

			# Aplica filtros adicionais
			if filters.get("orgao") and orgao != filters.get("orgao"):
				continue
			if filters.get("categoria") and categoria != filters.get("categoria"):
				continue
			if filters.get("fornecedor") and fornecedor != filters.get("fornecedor"):
				continue
			if filters.get("valor_min") > 0 and valor < filters.get("valor_min"):
				continue
			if filters.get("valor_max") > 0 and valor > filters.get("valor_max"):
				continue

			despesas.append({
				"name": f"EMP-{ano}{mes:02d}{i+1:04d}",
				"numero_empenho": f"{i+1:04d}/{ano}",
				"data_empenho": data.strftime("%Y-%m-%d"),
				"valor_total": valor,
				"orgao_publico": orgao,
				"categoria_despesa": categoria,
				"fornecedor": fornecedor,
				"descricao": f"Despesa com {categoria.lower()} para {orgao}"
			})
	else:
		despesas = empenhos

	return despesas

def calcular_totais(despesas):
	"""Calcula os totais e estatísticas das despesas."""
	total = sum(d.get("valor_total", 0) for d in despesas)

	# Agrupa por categoria
	por_categoria = {}
	for d in despesas:
		categoria = d.get("categoria_despesa")
		if categoria not in por_categoria:
			por_categoria[categoria] = 0
		por_categoria[categoria] += d.get("valor_total", 0)

	# Agrupa por órgão
	por_orgao = {}
	for d in despesas:
		orgao = d.get("orgao_publico")
		if orgao not in por_orgao:
			por_orgao[orgao] = 0
		por_orgao[orgao] += d.get("valor_total", 0)

	return {
		"total": fmt_money(total, currency="BRL"),
		"quantidade": len(despesas),
		"por_categoria": por_categoria,
		"por_orgao": por_orgao
	}

def preparar_graficos(despesas):
	"""Prepara os dados para os gráficos de despesas."""
	# Dados para gráfico de pizza por categoria
	categorias = {}
	for d in despesas:
		categoria = d.get("categoria_despesa")
		if categoria not in categorias:
			categorias[categoria] = 0
		categorias[categoria] += d.get("valor_total", 0)

	grafico_categorias = {
		"labels": list(categorias.keys()),
		"datasets": [{
			"values": list(categorias.values())
		}]
	}

	# Dados para gráfico de barras por órgão
	orgaos = {}
	for d in despesas:
		orgao = d.get("orgao_publico")
		if orgao not in orgaos:
			orgaos[orgao] = 0
		orgaos[orgao] += d.get("valor_total", 0)

	grafico_orgaos = {
		"labels": list(orgaos.keys()),
		"datasets": [{
			"values": list(orgaos.values())
		}]
	}

	return {
		"categorias": grafico_categorias,
		"orgaos": grafico_orgaos
	}

def get_opcoes_filtro():
	"""Obtém as opções disponíveis para os filtros."""
	# Em um ambiente real, isso seria uma consulta ao banco de dados
	# Aqui estamos retornando dados simulados para demonstração

	anos = [str(getdate().year - i) for i in range(5)]

	meses = [
		{"value": "1", "label": _("Janeiro")},
		{"value": "2", "label": _("Fevereiro")},
		{"value": "3", "label": _("Março")},
		{"value": "4", "label": _("Abril")},
		{"value": "5", "label": _("Maio")},
		{"value": "6", "label": _("Junho")},
		{"value": "7", "label": _("Julho")},
		{"value": "8", "label": _("Agosto")},
		{"value": "9", "label": _("Setembro")},
		{"value": "10", "label": _("Outubro")},
		{"value": "11", "label": _("Novembro")},
		{"value": "12", "label": _("Dezembro")}
	]

	orgaos = frappe.get_all("OrgaoPublico", fields=["name", "nome_orgao"])
	if not orgaos:
		# Simulação de dados para demonstração
		orgaos = [
			{"name": "SEC-ADM", "nome_orgao": "Secretaria de Administração"},
			{"name": "SEC-EDU", "nome_orgao": "Secretaria de Educação"},
			{"name": "SEC-SAU", "nome_orgao": "Secretaria de Saúde"}
		]

	categorias = frappe.get_all("CategoriaDespesa", fields=["name", "descricao"])
	if not categorias:
		# Simulação de dados para demonstração
		categorias = [
			{"name": "CAT-PES", "descricao": "Pessoal"},
			{"name": "CAT-MAT", "descricao": "Material de Consumo"},
			{"name": "CAT-SER", "descricao": "Serviços"},
			{"name": "CAT-OBR", "descricao": "Obras"},
			{"name": "CAT-EQP", "descricao": "Equipamentos"}
		]

	return {
		"anos": anos,
		"meses": meses,
		"orgaos": orgaos,
		"categorias": categorias
	}
