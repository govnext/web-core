# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de receitas do Portal da Transparência.
	"""
	context.title = _("Receitas")
	context.subtitle = _("Oferece informações detalhadas sobre as fontes de arrecadação do município, como impostos, transferências governamentais e outras receitas.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Dados de receitas
	context.receitas = get_receitas_data()

	# Estatísticas de receitas
	context.estatisticas_receitas = get_estatisticas_receitas()

	# Gráficos de receitas
	context.graficos = get_graficos_receitas()

	# Categorias de receitas
	context.categorias = get_categorias_receitas()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa de receitas."""
	return {
		"periodo": [
			{"label": _("Último mês"), "value": "ultimo_mes"},
			{"label": _("Últimos 3 meses"), "value": "ultimo_trimestre"},
			{"label": _("Último semestre"), "value": "ultimo_semestre"},
			{"label": _("Último ano"), "value": "ultimo_ano"},
			{"label": _("Período personalizado"), "value": "personalizado"}
		],
		"tipo": [
			{"label": _("Todas as receitas"), "value": "todas"},
			{"label": _("Receitas Correntes"), "value": "correntes"},
			{"label": _("Receitas de Capital"), "value": "capital"},
			{"label": _("Receitas Intraorçamentárias"), "value": "intraorcamentarias"}
		],
		"categoria": [
			{"label": _("Todas as categorias"), "value": "todas"},
			{"label": _("Impostos"), "value": "impostos"},
			{"label": _("Taxas"), "value": "taxas"},
			{"label": _("Contribuições"), "value": "contribuicoes"},
			{"label": _("Transferências da União"), "value": "transferencias_uniao"},
			{"label": _("Transferências do Estado"), "value": "transferencias_estado"},
			{"label": _("Outras Receitas"), "value": "outras"}
		],
		"orgao": get_orgaos_list(),
		"ordenacao": [
			{"label": _("Data (mais recente)"), "value": "data_desc"},
			{"label": _("Data (mais antiga)"), "value": "data_asc"},
			{"label": _("Valor (maior)"), "value": "valor_desc"},
			{"label": _("Valor (menor)"), "value": "valor_asc"},
			{"label": _("Fonte A-Z"), "value": "fonte_asc"},
			{"label": _("Órgão A-Z"), "value": "orgao_asc"}
		]
	}

def get_receitas_data():
	"""Retorna os dados de receitas para exibição."""
	# Em um ambiente real, estes dados viriam do banco de dados

	receitas_exemplo = [
		{
			"id": "2025/REC001234",
			"data": "2025-06-15",
			"fonte": "IPTU - Imposto Predial e Territorial Urbano",
			"codigo": "1.1.1.2.51.1.1",
			"descricao": "Arrecadação IPTU - Parcela 6/10 - Exercício 2025",
			"categoria": "Impostos",
			"tipo": "Receita Corrente",
			"orgao": "Secretaria da Fazenda",
			"valor": 156000.00,
			"meta_anual": 2500000.00,
			"percentual_meta": 62.4,
			"contribuinte": "Diversos",
			"lancamento": "2025LC001234"
		},
		{
			"id": "2025/REC001235",
			"data": "2025-06-14",
			"fonte": "FPM - Fundo de Participação dos Municípios",
			"codigo": "1.7.2.8.01.1.0",
			"descricao": "Transferência FPM - 2º decêndio de junho/2025",
			"categoria": "Transferências da União",
			"tipo": "Receita Corrente",
			"orgao": "Secretaria da Fazenda",
			"valor": 485000.00,
			"meta_anual": 6200000.00,
			"percentual_meta": 47.1,
			"contribuinte": "União Federal",
			"lancamento": "2025LC001235"
		},
		{
			"id": "2025/REC001236",
			"data": "2025-06-13",
			"fonte": "ISS - Imposto sobre Serviços",
			"codigo": "1.1.1.2.50.0.0",
			"descricao": "Arrecadação ISS - Diversos prestadores",
			"categoria": "Impostos",
			"tipo": "Receita Corrente",
			"orgao": "Secretaria da Fazenda",
			"valor": 89500.00,
			"meta_anual": 1800000.00,
			"percentual_meta": 41.2,
			"contribuinte": "Prestadores de Serviços",
			"lancamento": "2025LC001236"
		},
		{
			"id": "2025/REC001237",
			"data": "2025-06-12",
			"fonte": "FUNDEB - Fundo de Desenvolvimento da Educação Básica",
			"codigo": "1.7.2.8.01.2.0",
			"descricao": "Transferência FUNDEB - Complementação União",
			"categoria": "Transferências da União",
			"tipo": "Receita Corrente",
			"orgao": "Secretaria de Educação",
			"valor": 275000.00,
			"meta_anual": 3600000.00,
			"percentual_meta": 45.8,
			"contribuinte": "União Federal",
			"lancamento": "2025LC001237"
		}
	]

	# Formatar valores para exibição
	for receita in receitas_exemplo:
		receita["valor_formatado"] = fmt_money(receita["valor"], currency="BRL")
		receita["meta_anual_formatada"] = fmt_money(receita["meta_anual"], currency="BRL")
		receita["data_formatada"] = frappe.utils.formatdate(receita["data"], "dd/MM/yyyy")

	return receitas_exemplo

def get_estatisticas_receitas():
	"""Retorna estatísticas resumidas das receitas."""
	return {
		"total_mes_atual": fmt_money(2850000, currency="BRL"),
		"total_ano_atual": fmt_money(18450000, currency="BRL"),
		"meta_anual": fmt_money(24000000, currency="BRL"),
		"percentual_meta": 76.9,
		"quantidade_lancamentos": 542,
		"maior_arrecadacao": fmt_money(485000, currency="BRL"),
		"media_arrecadacao": fmt_money(34050, currency="BRL"),
		"crescimento_ano_anterior": 8.3
	}

def get_graficos_receitas():
	"""Retorna dados para gráficos de receitas."""
	return {
		"evolucao_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"valores": [2800000, 2950000, 2750000, 3100000, 3200000, 2850000],
			"meta": [3000000, 3000000, 3000000, 3200000, 3200000, 3200000],
			"ano_anterior": [2650000, 2750000, 2580000, 2890000, 2980000, 2650000]
		},
		"por_categoria": {
			"labels": ["Impostos", "Transferências União", "Transferências Estado", "Taxas", "Contribuições", "Outras"],
			"valores": [5200000, 8500000, 2800000, 850000, 650000, 450000],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1", "#fd7e14"]
		},
		"comparativo_mensal": {
			"labels": ["IPTU", "ISS", "FPM", "ICMS", "FUNDEB", "SUS"],
			"valores_mes": [156000, 89500, 485000, 320000, 275000, 185000],
			"valores_ano": [1850000, 1250000, 5850000, 3800000, 3300000, 2400000]
		}
	}

def get_categorias_receitas():
	"""Retorna as categorias de receitas com totalizações."""
	return [
		{
			"nome": "Receitas Tributárias",
			"codigo": "1.1.1.0.00.0.0",
			"valor": 6050000,
			"percentual": 32.8,
			"meta": 7500000,
			"subcategorias": [
				{"nome": "IPTU - Imposto Predial e Territorial Urbano", "valor": 1850000, "codigo": "1.1.1.2.51.1.1"},
				{"nome": "ISS - Imposto sobre Serviços", "valor": 1250000, "codigo": "1.1.1.2.50.0.0"},
				{"nome": "ITBI - Imposto sobre Transmissão", "valor": 890000, "codigo": "1.1.1.2.52.0.0"},
				{"nome": "Taxas Diversas", "valor": 2060000, "codigo": "1.1.1.3.00.0.0"}
			]
		},
		{
			"nome": "Transferências Intergovernamentais",
			"codigo": "1.7.0.0.00.0.0",
			"valor": 11300000,
			"percentual": 61.3,
			"meta": 14000000,
			"subcategorias": [
				{"nome": "FPM - Fundo de Participação dos Municípios", "valor": 5850000, "codigo": "1.7.2.8.01.1.0"},
				{"nome": "ICMS - Quota-parte", "valor": 3800000, "codigo": "1.7.1.8.01.2.0"},
				{"nome": "FUNDEB", "valor": 3300000, "codigo": "1.7.2.8.01.2.0"},
				{"nome": "SUS - Transferências", "valor": 2400000, "codigo": "1.7.2.8.02.1.0"}
			]
		},
		{
			"nome": "Receitas de Contribuições",
			"codigo": "1.2.0.0.00.0.0",
			"valor": 650000,
			"percentual": 3.5,
			"meta": 800000,
			"subcategorias": [
				{"nome": "Contribuição de Melhoria", "valor": 350000, "codigo": "1.2.4.0.00.0.0"},
				{"nome": "Contribuições Previdenciárias", "valor": 300000, "codigo": "1.2.1.8.01.1.0"}
			]
		},
		{
			"nome": "Receitas Patrimoniais",
			"codigo": "1.3.0.0.00.0.0",
			"valor": 280000,
			"percentual": 1.5,
			"meta": 400000,
			"subcategorias": [
				{"nome": "Aluguéis e Arrendamentos", "valor": 180000, "codigo": "1.3.2.1.01.0.0"},
				{"nome": "Rendimentos de Aplicações", "valor": 100000, "codigo": "1.3.5.1.01.0.0"}
			]
		},
		{
			"nome": "Outras Receitas Correntes",
			"codigo": "1.9.0.0.00.0.0",
			"valor": 170000,
			"percentual": 0.9,
			"meta": 300000,
			"subcategorias": [
				{"nome": "Multas e Juros de Mora", "valor": 120000, "codigo": "1.9.2.1.01.0.0"},
				{"nome": "Restituições", "valor": 50000, "codigo": "1.9.1.1.01.0.0"}
			]
		}
	]

def get_orgaos_list():
	"""Retorna lista de órgãos para filtro."""
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
			{"label": _("Secretaria da Fazenda"), "value": "fazenda"},
			{"label": _("Secretaria de Educação"), "value": "educacao"},
			{"label": _("Secretaria de Saúde"), "value": "saude"},
			{"label": _("Secretaria de Obras"), "value": "obras"},
			{"label": _("Secretaria de Assistência Social"), "value": "assistencia"}
		]

@frappe.whitelist(allow_guest=True)
def get_receitas_ajax(filtros=None):
	"""Endpoint AJAX para buscar receitas com filtros."""
	if filtros:
		filtros = json.loads(filtros)

	# Aplicar filtros e retornar dados
	receitas = get_receitas_data()

	return {
		"success": True,
		"data": receitas,
		"total": len(receitas),
		"total_valor": sum([r["valor"] for r in receitas])
	}

@frappe.whitelist(allow_guest=True)
def exportar_receitas(formato="csv", filtros=None):
	"""Exporta dados de receitas em diferentes formatos."""
	if filtros:
		filtros = json.loads(filtros)

	receitas = get_receitas_data()

	if formato == "csv":
		return gerar_csv_receitas(receitas)
	elif formato == "xlsx":
		return gerar_xlsx_receitas(receitas)
	elif formato == "pdf":
		return gerar_pdf_receitas(receitas)

	return {"error": "Formato não suportado"}

def gerar_csv_receitas(receitas):
	"""Gera arquivo CSV com dados de receitas."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	# Cabeçalho
	writer.writerow([
		"ID", "Data", "Fonte", "Código", "Descrição",
		"Categoria", "Tipo", "Órgão", "Valor", "Meta Anual", "% Meta"
	])

	# Dados
	for receita in receitas:
		writer.writerow([
			receita["id"],
			receita["data_formatada"],
			receita["fonte"],
			receita["codigo"],
			receita["descricao"],
			receita["categoria"],
			receita["tipo"],
			receita["orgao"],
			receita["valor_formatado"],
			receita["meta_anual_formatada"],
			f"{receita['percentual_meta']}%"
		])

	return {
		"content": output.getvalue(),
		"filename": f"receitas_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}
