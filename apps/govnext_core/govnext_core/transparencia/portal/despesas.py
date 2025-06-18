# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months, get_first_day, get_last_day
import json

def get_context(context):
	"""
	Prepara o contexto para a página de despesas do Portal da Transparência.
	"""
	context.title = _("Despesas")
	context.subtitle = _("Demonstra os gastos da prefeitura, incluindo pagamentos realizados, destinatários, valores e descrição da despesa.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Dados de despesas
	context.despesas = get_despesas_data()

	# Estatísticas de despesas
	context.estatisticas_despesas = get_estatisticas_despesas()

	# Gráficos de despesas
	context.graficos = get_graficos_despesas()

	# Categorias de despesas
	context.categorias = get_categorias_despesas()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa de despesas."""
	return {
		"periodo": [
			{"label": _("Último mês"), "value": "ultimo_mes"},
			{"label": _("Últimos 3 meses"), "value": "ultimo_trimestre"},
			{"label": _("Último semestre"), "value": "ultimo_semestre"},
			{"label": _("Último ano"), "value": "ultimo_ano"},
			{"label": _("Período personalizado"), "value": "personalizado"}
		],
		"categoria": [
			{"label": _("Todas as categorias"), "value": "todas"},
			{"label": _("Pessoal e Encargos"), "value": "pessoal"},
			{"label": _("Material de Consumo"), "value": "material"},
			{"label": _("Serviços de Terceiros"), "value": "servicos"},
			{"label": _("Obras e Instalações"), "value": "obras"},
			{"label": _("Equipamentos"), "value": "equipamentos"},
			{"label": _("Transferências"), "value": "transferencias"}
		],
		"orgao": get_orgaos_list(),
		"ordenacao": [
			{"label": _("Data (mais recente)"), "value": "data_desc"},
			{"label": _("Data (mais antiga)"), "value": "data_asc"},
			{"label": _("Valor (maior)"), "value": "valor_desc"},
			{"label": _("Valor (menor)"), "value": "valor_asc"},
			{"label": _("Fornecedor A-Z"), "value": "fornecedor_asc"},
			{"label": _("Órgão A-Z"), "value": "orgao_asc"}
		]
	}

def get_despesas_data():
	"""Retorna os dados de despesas para exibição."""
	# Em um ambiente real, estes dados viriam do banco de dados
	# com filtros aplicados conforme a solicitação do usuário

	despesas_exemplo = [
		{
			"id": "2025/001234",
			"data": "2025-06-15",
			"fornecedor": "Empresa de Limpeza Municipal Ltda",
			"cnpj": "12.345.678/0001-90",
			"descricao": "Serviços de limpeza urbana - Contrato 2025/089",
			"categoria": "Serviços de Terceiros",
			"orgao": "Secretaria de Serviços Urbanos",
			"valor": 45000.00,
			"tipo_despesa": "Custeio",
			"processo": "2025.001.001234-5",
			"empenho": "2025EM001234",
			"liquidacao": "2025LQ001234",
			"pagamento": "2025PG001234",
			"modalidade": "Pregão Eletrônico"
		},
		{
			"id": "2025/001235",
			"data": "2025-06-14",
			"fornecedor": "Construtora ABC S.A.",
			"cnpj": "98.765.432/0001-10",
			"descricao": "Obra de pavimentação da Rua das Flores",
			"categoria": "Obras e Instalações",
			"orgao": "Secretaria de Obras",
			"valor": 125000.00,
			"tipo_despesa": "Investimento",
			"processo": "2025.002.005678-9",
			"empenho": "2025EM001235",
			"liquidacao": "2025LQ001235",
			"pagamento": "2025PG001235",
			"modalidade": "Tomada de Preços"
		},
		{
			"id": "2025/001236",
			"data": "2025-06-13",
			"fornecedor": "Farmácia Saúde & Vida",
			"cnpj": "11.222.333/0001-44",
			"descricao": "Aquisição de medicamentos básicos",
			"categoria": "Material de Consumo",
			"orgao": "Secretaria de Saúde",
			"valor": 8500.00,
			"tipo_despesa": "Custeio",
			"processo": "2025.003.009876-1",
			"empenho": "2025EM001236",
			"liquidacao": "2025LQ001236",
			"pagamento": "2025PG001236",
			"modalidade": "Dispensa de Licitação"
		}
	]

	# Formatar valores para exibição
	for despesa in despesas_exemplo:
		despesa["valor_formatado"] = fmt_money(despesa["valor"], currency="BRL")
		despesa["data_formatada"] = frappe.utils.formatdate(despesa["data"], "dd/MM/yyyy")

	return despesas_exemplo

def get_estatisticas_despesas():
	"""Retorna estatísticas resumidas das despesas."""
	return {
		"total_mes_atual": fmt_money(1250000, currency="BRL"),
		"total_ano_atual": fmt_money(15600000, currency="BRL"),
		"quantidade_pagamentos": 1247,
		"maior_pagamento": fmt_money(125000, currency="BRL"),
		"media_pagamento": fmt_money(12500, currency="BRL"),
		"total_empenhos": fmt_money(18750000, currency="BRL"),
		"total_liquidacoes": fmt_money(16200000, currency="BRL"),
		"percentual_execucao": 83.5
	}

def get_graficos_despesas():
	"""Retorna dados para gráficos de despesas."""
	return {
		"evolucao_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"valores": [1200000, 1350000, 1180000, 1420000, 1380000, 1250000],
			"meta": [1300000, 1300000, 1300000, 1400000, 1400000, 1400000]
		},
		"por_categoria": {
			"labels": ["Pessoal", "Material", "Serviços", "Obras", "Equipamentos", "Transferências"],
			"valores": [8500000, 1200000, 2800000, 1800000, 750000, 550000],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1", "#fd7e14"]
		},
		"por_orgao": {
			"labels": ["Educação", "Saúde", "Obras", "Administração", "Assistência Social"],
			"valores": [4200000, 3800000, 2500000, 2100000, 1200000],
			"percentuais": [28.0, 25.3, 16.7, 14.0, 8.0]
		}
	}

def get_categorias_despesas():
	"""Retorna as categorias de despesas com totalizações."""
	return [
		{
			"nome": "Pessoal e Encargos Sociais",
			"codigo": "3.1",
			"valor": 8500000,
			"percentual": 54.5,
			"subcategorias": [
				{"nome": "Vencimentos e Vantagens Fixas", "valor": 6200000},
				{"nome": "Obrigações Patronais", "valor": 1800000},
				{"nome": "Outras Despesas de Pessoal", "valor": 500000}
			]
		},
		{
			"nome": "Juros e Encargos da Dívida",
			"codigo": "3.2",
			"valor": 150000,
			"percentual": 1.0,
			"subcategorias": []
		},
		{
			"nome": "Outras Despesas Correntes",
			"codigo": "3.3",
			"valor": 4800000,
			"percentual": 30.8,
			"subcategorias": [
				{"nome": "Material de Consumo", "valor": 1200000},
				{"nome": "Serviços de Terceiros - PJ", "valor": 2800000},
				{"nome": "Transferências a Instituições", "valor": 550000},
				{"nome": "Outras", "valor": 250000}
			]
		},
		{
			"nome": "Investimentos",
			"codigo": "4.4",
			"valor": 1800000,
			"percentual": 11.5,
			"subcategorias": [
				{"nome": "Obras e Instalações", "valor": 1200000},
				{"nome": "Equipamentos e Material Permanente", "valor": 600000}
			]
		},
		{
			"nome": "Inversões Financeiras",
			"codigo": "4.5",
			"valor": 200000,
			"percentual": 1.3,
			"subcategorias": []
		},
		{
			"nome": "Amortização da Dívida",
			"codigo": "4.6",
			"valor": 150000,
			"percentual": 1.0,
			"subcategorias": []
		}
	]

def get_orgaos_list():
	"""Retorna lista de órgãos para filtro."""
	# Em um ambiente real, viria do banco de dados
	try:
		orgaos = frappe.get_all("Orgao Publico",
			fields=["name", "nome_orgao"],
			filters={"disabled": 0}
		)
		return [{"label": orgao.nome_orgao, "value": orgao.name} for orgao in orgaos]
	except:
		# Fallback com dados de exemplo
		return [
			{"label": _("Todos os órgãos"), "value": "todos"},
			{"label": _("Gabinete do Prefeito"), "value": "gabinete"},
			{"label": _("Secretaria de Administração"), "value": "administracao"},
			{"label": _("Secretaria de Educação"), "value": "educacao"},
			{"label": _("Secretaria de Saúde"), "value": "saude"},
			{"label": _("Secretaria de Obras"), "value": "obras"},
			{"label": _("Secretaria de Assistência Social"), "value": "assistencia"},
			{"label": _("Secretaria de Serviços Urbanos"), "value": "servicos_urbanos"}
		]

@frappe.whitelist(allow_guest=True)
def get_despesas_ajax(filtros=None):
	"""Endpoint AJAX para buscar despesas com filtros."""
	if filtros:
		filtros = json.loads(filtros)

	# Aplicar filtros e retornar dados
	despesas = get_despesas_data()

	return {
		"success": True,
		"data": despesas,
		"total": len(despesas),
		"total_valor": sum([d["valor"] for d in despesas])
	}

@frappe.whitelist(allow_guest=True)
def exportar_despesas(formato="csv", filtros=None):
	"""Exporta dados de despesas em diferentes formatos."""
	if filtros:
		filtros = json.loads(filtros)

	despesas = get_despesas_data()

	if formato == "csv":
		return gerar_csv_despesas(despesas)
	elif formato == "xlsx":
		return gerar_xlsx_despesas(despesas)
	elif formato == "pdf":
		return gerar_pdf_despesas(despesas)

	return {"error": "Formato não suportado"}

def gerar_csv_despesas(despesas):
	"""Gera arquivo CSV com dados de despesas."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	# Cabeçalho
	writer.writerow([
		"ID", "Data", "Fornecedor", "CNPJ", "Descrição",
		"Categoria", "Órgão", "Valor", "Tipo"
	])

	# Dados
	for despesa in despesas:
		writer.writerow([
			despesa["id"],
			despesa["data_formatada"],
			despesa["fornecedor"],
			despesa["cnpj"],
			despesa["descricao"],
			despesa["categoria"],
			despesa["orgao"],
			despesa["valor_formatado"],
			despesa["tipo_despesa"]
		])

	return {
		"content": output.getvalue(),
		"filename": f"despesas_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}
