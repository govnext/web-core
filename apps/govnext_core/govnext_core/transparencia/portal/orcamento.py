# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de orçamento do Portal da Transparência.
	"""
	context.title = _("Orçamento")
	context.subtitle = _("Disponibiliza informações detalhadas sobre a previsão de receitas e despesas, esclarecendo como os recursos são planejados.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Dados do orçamento
	context.orcamento = get_orcamento_data()

	# Estatísticas orçamentárias
	context.estatisticas_orcamento = get_estatisticas_orcamento()

	# Gráficos orçamentários
	context.graficos = get_graficos_orcamento()

	# Estrutura orçamentária
	context.estrutura_orcamentaria = get_estrutura_orcamentaria()

	# Programas de governo
	context.programas_governo = get_programas_governo()

	# Metas fiscais
	context.metas_fiscais = get_metas_fiscais()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa orçamentária."""
	return {
		"exercicio": [
			{"label": "2025", "value": "2025"},
			{"label": "2024", "value": "2024"},
			{"label": "2023", "value": "2023"},
			{"label": "2022", "value": "2022"}
		],
		"tipo": [
			{"label": _("Todos"), "value": "todos"},
			{"label": _("Receitas"), "value": "receitas"},
			{"label": _("Despesas"), "value": "despesas"},
			{"label": _("Investimentos"), "value": "investimentos"}
		],
		"funcao": [
			{"label": _("Todas as funções"), "value": "todas"},
			{"label": _("Educação"), "value": "educacao"},
			{"label": _("Saúde"), "value": "saude"},
			{"label": _("Assistência Social"), "value": "assistencia_social"},
			{"label": _("Administração"), "value": "administracao"},
			{"label": _("Urbanismo"), "value": "urbanismo"},
			{"label": _("Transporte"), "value": "transporte"}
		],
		"orgao": get_orgaos_list(),
		"status": [
			{"label": _("Todos os status"), "value": "todos"},
			{"label": _("Não Iniciado"), "value": "nao_iniciado"},
			{"label": _("Em Execução"), "value": "execucao"},
			{"label": _("Concluído"), "value": "concluido"},
			{"label": _("Suspenso"), "value": "suspenso"}
		]
	}

def get_orcamento_data():
	"""Retorna os dados orçamentários para exibição."""
	return {
		"receitas": {
			"orcado": 24000000.00,
			"arrecadado": 18450000.00,
			"percentual_execucao": 76.9,
			"categorias": [
				{
					"nome": "Receitas Tributárias",
					"orcado": 7500000.00,
					"arrecadado": 6050000.00,
					"percentual": 80.7
				},
				{
					"nome": "Transferências Intergovernamentais",
					"orcado": 14000000.00,
					"arrecadado": 11300000.00,
					"percentual": 80.7
				},
				{
					"nome": "Outras Receitas Correntes",
					"orcado": 1500000.00,
					"arrecadado": 1100000.00,
					"percentual": 73.3
				},
				{
					"nome": "Receitas de Capital",
					"orcado": 1000000.00,
					"arrecadado": 0.00,
					"percentual": 0.0
				}
			]
		},
		"despesas": {
			"orcado": 23500000.00,
			"empenhado": 19650000.00,
			"liquidado": 17800000.00,
			"pago": 15600000.00,
			"percentual_empenho": 83.6,
			"percentual_liquidacao": 90.6,
			"percentual_pagamento": 87.6,
			"categorias": [
				{
					"nome": "Pessoal e Encargos Sociais",
					"orcado": 12500000.00,
					"empenhado": 11200000.00,
					"liquidado": 10800000.00,
					"pago": 10200000.00,
					"percentual_empenho": 89.6
				},
				{
					"nome": "Outras Despesas Correntes",
					"orcado": 6800000.00,
					"empenhado": 5650000.00,
					"liquidado": 5200000.00,
					"pago": 4200000.00,
					"percentual_empenho": 83.1
				},
				{
					"nome": "Investimentos",
					"orcado": 3200000.00,
					"empenhado": 2300000.00,
					"liquidado": 1800000.00,
					"pago": 1200000.00,
					"percentual_empenho": 71.9
				},
				{
					"nome": "Inversões Financeiras",
					"orcado": 800000.00,
					"empenhado": 400000.00,
					"liquidado": 0.00,
					"pago": 0.00,
					"percentual_empenho": 50.0
				},
				{
					"nome": "Amortização da Dívida",
					"orcado": 200000.00,
					"empenhado": 100000.00,
					"liquidado": 0.00,
					"pago": 0.00,
					"percentual_empenho": 50.0
				}
			]
		}
	}

def get_estatisticas_orcamento():
	"""Retorna estatísticas orçamentárias consolidadas."""
	return {
		"orcamento_total": fmt_money(24000000, currency="BRL"),
		"receita_orcada": fmt_money(24000000, currency="BRL"),
		"receita_arrecadada": fmt_money(18450000, currency="BRL"),
		"despesa_orcada": fmt_money(23500000, currency="BRL"),
		"despesa_empenhada": fmt_money(19650000, currency="BRL"),
		"despesa_paga": fmt_money(15600000, currency="BRL"),
		"resultado_orcamentario": fmt_money(2850000, currency="BRL"),
		"percentual_receita": 76.9,
		"percentual_despesa": 83.6,
		"superavit_deficit": "Superávit",
		"restos_pagar": fmt_money(4050000, currency="BRL"),
		"disponibilidade_caixa": fmt_money(8920000, currency="BRL")
	}

def get_graficos_orcamento():
	"""Retorna dados para gráficos orçamentários."""
	return {
		"execucao_orcamentaria": {
			"categorias": ["Receitas", "Despesas"],
			"orcado": [24000000, 23500000],
			"realizado": [18450000, 15600000],
			"percentual": [76.9, 66.4]
		},
		"receitas_por_categoria": {
			"labels": ["Tributárias", "Transferências", "Outras Correntes", "Capital"],
			"orcado": [7500000, 14000000, 1500000, 1000000],
			"arrecadado": [6050000, 11300000, 1100000, 0],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545"]
		},
		"despesas_por_categoria": {
			"labels": ["Pessoal", "Custeio", "Investimentos", "Inversões", "Amortização"],
			"orcado": [12500000, 6800000, 3200000, 800000, 200000],
			"empenhado": [11200000, 5650000, 2300000, 400000, 100000],
			"pago": [10200000, 4200000, 1200000, 0, 0],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"]
		},
		"evolucao_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"receitas": [2800000, 2950000, 2750000, 3100000, 3200000, 3650000],
			"despesas": [2650000, 2880000, 2580000, 2890000, 2450000, 2150000],
			"meta_receitas": [4000000, 4000000, 4000000, 4000000, 4000000, 4000000],
			"meta_despesas": [3916667, 3916667, 3916667, 3916667, 3916667, 3916667]
		}
	}

def get_estrutura_orcamentaria():
	"""Retorna a estrutura orçamentária por função de governo."""
	return [
		{
			"codigo": "12",
			"funcao": "Educação",
			"orcado": 6500000,
			"empenhado": 5650000,
			"percentual_empenho": 86.9,
			"percentual_orcamento": 27.7,
			"subfuncoes": [
				{"codigo": "361", "nome": "Ensino Fundamental", "orcado": 4200000, "empenhado": 3850000},
				{"codigo": "365", "nome": "Educação Infantil", "orcado": 1800000, "empenhado": 1400000},
				{"codigo": "366", "nome": "Educação de Jovens e Adultos", "orcado": 350000, "empenhado": 280000},
				{"codigo": "367", "nome": "Educação Especial", "orcado": 150000, "empenhado": 120000}
			]
		},
		{
			"codigo": "10",
			"funcao": "Saúde",
			"orcado": 5800000,
			"empenhado": 4950000,
			"percentual_empenho": 85.3,
			"percentual_orcamento": 24.7,
			"subfuncoes": [
				{"codigo": "301", "nome": "Atenção Básica", "orcado": 3200000, "empenhado": 2850000},
				{"codigo": "302", "nome": "Assistência Hospitalar", "orcado": 1800000, "empenhado": 1550000},
				{"codigo": "303", "nome": "Suporte Profilático", "orcado": 500000, "empenhado": 350000},
				{"codigo": "304", "nome": "Vigilância Sanitária", "orcado": 300000, "empenhado": 200000}
			]
		},
		{
			"codigo": "04",
			"funcao": "Administração",
			"orcado": 3200000,
			"empenhado": 2850000,
			"percentual_empenho": 89.1,
			"percentual_orcamento": 13.6,
			"subfuncoes": [
				{"codigo": "122", "nome": "Administração Geral", "orcado": 2200000, "empenhado": 2050000},
				{"codigo": "123", "nome": "Administração Financeira", "orcado": 600000, "empenhado": 480000},
				{"codigo": "124", "nome": "Controle Interno", "orcado": 250000, "empenhado": 180000},
				{"codigo": "125", "nome": "Normalização e Fiscalização", "orcado": 150000, "empenhado": 140000}
			]
		},
		{
			"codigo": "15",
			"funcao": "Urbanismo",
			"orcado": 2800000,
			"empenhado": 2200000,
			"percentual_empenho": 78.6,
			"percentual_orcamento": 11.9,
			"subfuncoes": [
				{"codigo": "451", "nome": "Infraestrutura Urbana", "orcado": 1800000, "empenhado": 1450000},
				{"codigo": "452", "nome": "Serviços Urbanos", "orcado": 800000, "empenhado": 600000},
				{"codigo": "453", "nome": "Transportes Coletivos", "orcado": 200000, "empenhado": 150000}
			]
		},
		{
			"codigo": "08",
			"funcao": "Assistência Social",
			"orcado": 2400000,
			"empenhado": 2050000,
			"percentual_empenho": 85.4,
			"percentual_orcamento": 10.2,
			"subfuncoes": [
				{"codigo": "241", "nome": "Assistência ao Idoso", "orcado": 800000, "empenhado": 720000},
				{"codigo": "242", "nome": "Assistência ao Portador de Deficiência", "orcado": 450000, "empenhado": 380000},
				{"codigo": "243", "nome": "Assistência à Criança e ao Adolescente", "orcado": 650000, "empenhado": 550000},
				{"codigo": "244", "nome": "Assistência Comunitária", "orcado": 500000, "empenhado": 400000}
			]
		},
		{
			"codigo": "26",
			"funcao": "Transporte",
			"orcado": 1500000,
			"empenhado": 1200000,
			"percentual_empenho": 80.0,
			"percentual_orcamento": 6.4,
			"subfuncoes": [
				{"codigo": "782", "nome": "Transporte Rodoviário", "orcado": 1200000, "empenhado": 950000},
				{"codigo": "784", "nome": "Transporte Hidroviário", "orcado": 300000, "empenhado": 250000}
			]
		}
	]

def get_programas_governo():
	"""Retorna os programas de governo e suas execuções."""
	return [
		{
			"codigo": "0001",
			"nome": "Educação de Qualidade para Todos",
			"objetivo": "Garantir educação básica de qualidade para todas as crianças e adolescentes",
			"orcado": 6500000,
			"empenhado": 5650000,
			"percentual_execucao": 86.9,
			"metas": [
				{"indicador": "Taxa de aprovação no ensino fundamental", "meta": 95, "realizado": 92},
				{"indicador": "Número de matrículas na educação infantil", "meta": 2500, "realizado": 2380},
				{"indicador": "Índice de abandono escolar", "meta": 3, "realizado": 2.8}
			],
			"acoes": [
				{"nome": "Manutenção do Ensino Fundamental", "orcado": 4200000, "empenhado": 3850000},
				{"nome": "Expansão da Educação Infantil", "orcado": 1800000, "empenhado": 1400000},
				{"nome": "Programa de Alimentação Escolar", "orcado": 500000, "empenhado": 400000}
			]
		},
		{
			"codigo": "0002",
			"nome": "Saúde Integral e Preventiva",
			"objetivo": "Promover atenção integral à saúde da população municipal",
			"orcado": 5800000,
			"empenhado": 4950000,
			"percentual_execucao": 85.3,
			"metas": [
				{"indicador": "Cobertura da Estratégia Saúde da Família", "meta": 95, "realizado": 92},
				{"indicador": "Número de consultas médicas realizadas", "meta": 45000, "realizado": 42500},
				{"indicador": "Taxa de mortalidade infantil", "meta": 12, "realizado": 11.5}
			],
			"acoes": [
				{"nome": "Atenção Básica em Saúde", "orcado": 3200000, "empenhado": 2850000},
				{"nome": "Assistência Farmacêutica", "orcado": 1200000, "empenhado": 1050000},
				{"nome": "Vigilância em Saúde", "orcado": 800000, "empenhado": 650000}
			]
		},
		{
			"codigo": "0003",
			"nome": "Cidade Sustentável e Moderna",
			"objetivo": "Desenvolver infraestrutura urbana sustentável e moderna",
			"orcado": 2800000,
			"empenhado": 2200000,
			"percentual_execucao": 78.6,
			"metas": [
				{"indicador": "Quilômetros de vias pavimentadas", "meta": 15, "realizado": 12},
				{"indicador": "Percentual de coleta seletiva", "meta": 40, "realizado": 35},
				{"indicador": "Número de praças revitalizadas", "meta": 8, "realizado": 6}
			],
			"acoes": [
				{"nome": "Pavimentação e Recapeamento", "orcado": 1800000, "empenhado": 1450000},
				{"nome": "Limpeza Urbana e Coleta Seletiva", "orcado": 600000, "empenhado": 480000},
				{"nome": "Revitalização de Espaços Públicos", "orcado": 400000, "empenhado": 270000}
			]
		},
		{
			"codigo": "0004",
			"nome": "Proteção Social Integral",
			"objetivo": "Garantir proteção social às famílias em situação de vulnerabilidade",
			"orcado": 2400000,
			"empenhado": 2050000,
			"percentual_execucao": 85.4,
			"metas": [
				{"indicador": "Famílias atendidas pelos CRAS", "meta": 1500, "realizado": 1420},
				{"indicador": "Crianças em programas de proteção", "meta": 800, "realizado": 760},
				{"indicador": "Idosos atendidos em centros de convivência", "meta": 300, "realizado": 285}
			],
			"acoes": [
				{"nome": "Proteção Social Básica", "orcado": 1200000, "empenhado": 1050000},
				{"nome": "Proteção Social Especial", "orcado": 800000, "empenhado": 680000},
				{"nome": "Benefícios Eventuais", "orcado": 400000, "empenhado": 320000}
			]
		}
	]

def get_metas_fiscais():
	"""Retorna as metas fiscais estabelecidas."""
	return {
		"resultado_nominal": {
			"meta": -500000,
			"realizado": 2850000,
			"status": "Superado"
		},
		"resultado_primario": {
			"meta": 1200000,
			"realizado": 2850000,
			"status": "Superado"
		},
		"receita_total": {
			"meta": 24000000,
			"realizado": 18450000,
			"percentual": 76.9,
			"status": "Em execução"
		},
		"despesa_total": {
			"meta": 23500000,
			"realizado": 15600000,
			"percentual": 66.4,
			"status": "Em execução"
		},
		"despesa_pessoal": {
			"meta": 12960000,  # 54% da RCL
			"realizado": 10200000,
			"percentual_rcl": 42.5,
			"limite_legal": 54.0,
			"status": "Dentro do limite"
		},
		"divida_consolidada": {
			"meta": 2400000,  # 10% da RCL
			"realizado": 1850000,
			"percentual_rcl": 7.7,
			"limite_legal": 120.0,
			"status": "Dentro do limite"
		}
	}

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
			{"label": _("Gabinete do Prefeito"), "value": "gabinete"},
			{"label": _("Secretaria de Administração"), "value": "administracao"},
			{"label": _("Secretaria de Educação"), "value": "educacao"},
			{"label": _("Secretaria de Saúde"), "value": "saude"},
			{"label": _("Secretaria de Obras"), "value": "obras"},
			{"label": _("Secretaria de Assistência Social"), "value": "assistencia"}
		]

@frappe.whitelist(allow_guest=True)
def get_orcamento_ajax(filtros=None):
	"""Endpoint AJAX para buscar dados orçamentários com filtros."""
	if filtros:
		filtros = json.loads(filtros)

	# Aplicar filtros e retornar dados
	orcamento = get_orcamento_data()

	return {
		"success": True,
		"data": orcamento
	}

@frappe.whitelist(allow_guest=True)
def get_programa_detalhes(codigo_programa):
	"""Endpoint para buscar detalhes de um programa específico."""
	programas = get_programas_governo()
	programa = next((p for p in programas if p["codigo"] == codigo_programa), None)

	if programa:
		return {
			"success": True,
			"data": programa
		}
	else:
		return {
			"success": False,
			"error": "Programa não encontrado"
		}

@frappe.whitelist(allow_guest=True)
def exportar_orcamento(formato="csv", tipo="completo"):
	"""Exporta dados orçamentários em diferentes formatos."""
	orcamento = get_orcamento_data()
	programas = get_programas_governo()

	if formato == "csv":
		return gerar_csv_orcamento(orcamento, programas, tipo)
	elif formato == "xlsx":
		return gerar_xlsx_orcamento(orcamento, programas, tipo)
	elif formato == "pdf":
		return gerar_pdf_orcamento(orcamento, programas, tipo)

	return {"error": "Formato não suportado"}

def gerar_csv_orcamento(orcamento, programas, tipo):
	"""Gera arquivo CSV com dados orçamentários."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	if tipo == "receitas":
		writer.writerow(["Categoria", "Orçado", "Arrecadado", "Percentual"])
		for categoria in orcamento["receitas"]["categorias"]:
			writer.writerow([
				categoria["nome"],
				fmt_money(categoria["orcado"], currency="BRL"),
				fmt_money(categoria["arrecadado"], currency="BRL"),
				f"{categoria['percentual']}%"
			])
	elif tipo == "despesas":
		writer.writerow(["Categoria", "Orçado", "Empenhado", "Liquidado", "Pago", "% Empenho"])
		for categoria in orcamento["despesas"]["categorias"]:
			writer.writerow([
				categoria["nome"],
				fmt_money(categoria["orcado"], currency="BRL"),
				fmt_money(categoria["empenhado"], currency="BRL"),
				fmt_money(categoria["liquidado"], currency="BRL"),
				fmt_money(categoria["pago"], currency="BRL"),
				f"{categoria['percentual_empenho']}%"
			])
	else:  # completo
		writer.writerow(["Tipo", "Categoria", "Orçado", "Realizado", "Percentual"])
		
		for categoria in orcamento["receitas"]["categorias"]:
			writer.writerow([
				"Receita",
				categoria["nome"],
				fmt_money(categoria["orcado"], currency="BRL"),
				fmt_money(categoria["arrecadado"], currency="BRL"),
				f"{categoria['percentual']}%"
			])
		
		for categoria in orcamento["despesas"]["categorias"]:
			writer.writerow([
				"Despesa",
				categoria["nome"],
				fmt_money(categoria["orcado"], currency="BRL"),
				fmt_money(categoria["empenhado"], currency="BRL"),
				f"{categoria['percentual_empenho']}%"
			])

	return {
		"content": output.getvalue(),
		"filename": f"orcamento_{tipo}_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}