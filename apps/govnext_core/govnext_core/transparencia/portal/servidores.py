# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de servidores do Portal da Transparência.
	"""
	context.title = _("Servidores")
	context.subtitle = _("Consulte informações consolidadas sobre servidores, estrutura remuneratória, folha de pagamento, dentre outros.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Dados de servidores
	context.servidores = get_servidores_data()

	# Estatísticas da folha
	context.estatisticas_folha = get_estatisticas_folha()

	# Gráficos de gestão de pessoas
	context.graficos = get_graficos_gestao_pessoas()

	# Estrutura de cargos
	context.estrutura_cargos = get_estrutura_cargos()

	# Faixas salariais
	context.faixas_salariais = get_faixas_salariais()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa de servidores."""
	return {
		"periodo": [
			{"label": _("Mês atual"), "value": "mes_atual"},
			{"label": _("Últimos 3 meses"), "value": "ultimo_trimestre"},
			{"label": _("Últimos 6 meses"), "value": "ultimo_semestre"},
			{"label": _("Último ano"), "value": "ultimo_ano"}
		],
		"situacao": [
			{"label": _("Todas as situações"), "value": "todas"},
			{"label": _("Ativos"), "value": "ativos"},
			{"label": _("Inativos"), "value": "inativos"},
			{"label": _("Afastados"), "value": "afastados"},
			{"label": _("Aposentados"), "value": "aposentados"}
		],
		"tipo_vinculo": [
			{"label": _("Todos os vínculos"), "value": "todos"},
			{"label": _("Efetivos"), "value": "efetivos"},
			{"label": _("Comissionados"), "value": "comissionados"},
			{"label": _("Temporários"), "value": "temporarios"},
			{"label": _("Terceirizados"), "value": "terceirizados"}
		],
		"orgao": get_orgaos_list(),
		"faixa_salarial": [
			{"label": _("Todas as faixas"), "value": "todas"},
			{"label": _("Até R$ 2.000"), "value": "ate_2000"},
			{"label": _("R$ 2.001 a R$ 5.000"), "value": "2001_5000"},
			{"label": _("R$ 5.001 a R$ 10.000"), "value": "5001_10000"},
			{"label": _("R$ 10.001 a R$ 15.000"), "value": "10001_15000"},
			{"label": _("Acima de R$ 15.000"), "value": "acima_15000"}
		],
		"ordenacao": [
			{"label": _("Nome A-Z"), "value": "nome_asc"},
			{"label": _("Nome Z-A"), "value": "nome_desc"},
			{"label": _("Salário (maior)"), "value": "salario_desc"},
			{"label": _("Salário (menor)"), "value": "salario_asc"},
			{"label": _("Cargo A-Z"), "value": "cargo_asc"},
			{"label": _("Órgão A-Z"), "value": "orgao_asc"}
		]
	}

def get_servidores_data():
	"""Retorna os dados de servidores para exibição."""
	# Em um ambiente real, estes dados viriam do banco de dados
	# Por questões de privacidade, nomes são fictícios

	servidores_exemplo = [
		{
			"id": "2025/SERV-001",
			"nome": "Ana Paula Silva",
			"cargo": "Professora de Educação Básica",
			"funcao": "Professora",
			"orgao": "Secretaria de Educação",
			"situacao": "Ativa",
			"tipo_vinculo": "Efetiva",
			"admissao": "2020-02-15",
			"carga_horaria": 40,
			"salario_base": 4500.00,
			"gratificacoes": 850.00,
			"descontos": 720.00,
			"salario_liquido": 4630.00,
			"mes_referencia": "2025-06"
		},
		{
			"id": "2025/SERV-002",
			"nome": "Carlos Roberto Santos",
			"cargo": "Médico Clínico Geral",
			"funcao": "Médico",
			"orgao": "Secretaria de Saúde",
			"situacao": "Ativo",
			"tipo_vinculo": "Efetivo",
			"admissao": "2018-08-10",
			"carga_horaria": 40,
			"salario_base": 12000.00,
			"gratificacoes": 2400.00,
			"descontos": 2160.00,
			"salario_liquido": 12240.00,
			"mes_referencia": "2025-06"
		},
		{
			"id": "2025/SERV-003",
			"nome": "Maria José Oliveira",
			"cargo": "Enfermeira",
			"funcao": "Coordenadora de Enfermagem",
			"orgao": "Secretaria de Saúde",
			"situacao": "Ativa",
			"tipo_vinculo": "Efetiva",
			"admissao": "2015-03-20",
			"carga_horaria": 40,
			"salario_base": 6800.00,
			"gratificacoes": 1200.00,
			"descontos": 1040.00,
			"salario_liquido": 6960.00,
			"mes_referencia": "2025-06"
		},
		{
			"id": "2025/SERV-004",
			"nome": "João Marcelo Pereira",
			"cargo": "Secretário Municipal",
			"funcao": "Secretário de Obras",
			"orgao": "Secretaria de Obras",
			"situacao": "Ativo",
			"tipo_vinculo": "Comissionado",
			"admissao": "2021-01-01",
			"carga_horaria": 40,
			"salario_base": 15000.00,
			"gratificacoes": 3000.00,
			"descontos": 2700.00,
			"salario_liquido": 15300.00,
			"mes_referencia": "2025-06"
		},
		{
			"id": "2025/SERV-005",
			"nome": "Fernanda Costa Lima",
			"cargo": "Assistente Social",
			"funcao": "Coordenadora CRAS",
			"orgao": "Secretaria de Assistência Social",
			"situacao": "Ativa",
			"tipo_vinculo": "Efetiva",
			"admissao": "2019-05-15",
			"carga_horaria": 30,
			"salario_base": 4200.00,
			"gratificacoes": 600.00,
			"descontos": 620.00,
			"salario_liquido": 4180.00,
			"mes_referencia": "2025-06"
		}
	]

	# Formatar valores para exibição
	for servidor in servidores_exemplo:
		servidor["salario_base_formatado"] = fmt_money(servidor["salario_base"], currency="BRL")
		servidor["gratificacoes_formatadas"] = fmt_money(servidor["gratificacoes"], currency="BRL")
		servidor["descontos_formatados"] = fmt_money(servidor["descontos"], currency="BRL")
		servidor["salario_liquido_formatado"] = fmt_money(servidor["salario_liquido"], currency="BRL")
		servidor["admissao_formatada"] = frappe.utils.formatdate(servidor["admissao"], "dd/MM/yyyy")

	return servidores_exemplo

def get_estatisticas_folha():
	"""Retorna estatísticas resumidas da folha de pagamento."""
	return {
		"total_servidores": 1250,
		"servidores_ativos": 1185,
		"servidores_inativos": 65,
		"folha_bruta_mensal": fmt_money(8500000, currency="BRL"),
		"folha_liquida_mensal": fmt_money(6750000, currency="BRL"),
		"total_descontos": fmt_money(1750000, currency="BRL"),
		"encargos_patronais": fmt_money(2380000, currency="BRL"),
		"folha_anual": fmt_money(102000000, currency="BRL"),
		"percentual_receita": 54.2,
		"media_salarial": fmt_money(5400, currency="BRL"),
		"gasto_per_capita": fmt_money(325, currency="BRL")
	}

def get_graficos_gestao_pessoas():
	"""Retorna dados para gráficos de gestão de pessoas."""
	return {
		"evolucao_folha": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"folha_bruta": [8200000, 8350000, 8180000, 8420000, 8380000, 8500000],
			"folha_liquida": [6560000, 6680000, 6544000, 6736000, 6704000, 6750000],
			"encargos": [2296000, 2340500, 2290400, 2358600, 2346400, 2380000]
		},
		"por_orgao": {
			"labels": ["Educação", "Saúde", "Administração", "Obras", "Assistência Social", "Outros"],
			"quantidade": [480, 350, 180, 120, 85, 35],
			"folha": [3400000, 2800000, 1200000, 800000, 480000, 320000],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1", "#fd7e14"]
		},
		"por_vinculo": {
			"labels": ["Efetivos", "Comissionados", "Temporários", "Terceirizados"],
			"quantidade": [850, 180, 120, 100],
			"folha": [5950000, 1800000, 480000, 270000],
			"cores": ["#28a745", "#ffc107", "#007bff", "#6c757d"]
		},
		"faixas_salariais": {
			"labels": ["Até R$ 2.000", "R$ 2.001-5.000", "R$ 5.001-10.000", "R$ 10.001-15.000", "Acima R$ 15.000"],
			"quantidade": [120, 650, 380, 80, 20],
			"percentual": [9.6, 52.0, 30.4, 6.4, 1.6]
		}
	}

def get_estrutura_cargos():
	"""Retorna a estrutura de cargos da administração."""
	return [
		{
			"categoria": "Magistério",
			"total_servidores": 480,
			"percentual": 38.4,
			"folha_total": 3400000,
			"cargos": [
				{"nome": "Professor de Educação Básica", "quantidade": 320, "salario_medio": 4500},
				{"nome": "Professor de Educação Infantil", "quantidade": 85, "salario_medio": 4200},
				{"nome": "Coordenador Pedagógico", "quantidade": 45, "salario_medio": 6500},
				{"nome": "Diretor de Escola", "quantidade": 25, "salario_medio": 8500},
				{"nome": "Supervisor de Ensino", "quantidade": 5, "salario_medio": 9200}
			]
		},
		{
			"categoria": "Saúde",
			"total_servidores": 350,
			"percentual": 28.0,
			"folha_total": 2800000,
			"cargos": [
				{"nome": "Enfermeiro", "quantidade": 85, "salario_medio": 6800},
				{"nome": "Técnico em Enfermagem", "quantidade": 120, "salario_medio": 3200},
				{"nome": "Médico Clínico Geral", "quantidade": 45, "salario_medio": 12000},
				{"nome": "Médico Especialista", "quantidade": 25, "salario_medio": 15000},
				{"nome": "Auxiliar de Saúde", "quantidade": 75, "salario_medio": 2800}
			]
		},
		{
			"categoria": "Administração Geral",
			"total_servidores": 180,
			"percentual": 14.4,
			"folha_total": 1200000,
			"cargos": [
				{"nome": "Assistente Administrativo", "quantidade": 85, "salario_medio": 3500},
				{"nome": "Analista Administrativo", "quantidade": 45, "salario_medio": 5800},
				{"nome": "Contador", "quantidade": 15, "salario_medio": 8500},
				{"nome": "Procurador Municipal", "quantidade": 8, "salario_medio": 12500},
				{"nome": "Secretário Municipal", "quantidade": 12, "salario_medio": 15000}
			]
		},
		{
			"categoria": "Serviços Urbanos",
			"total_servidores": 120,
			"percentual": 9.6,
			"folha_total": 480000,
			"cargos": [
				{"nome": "Gari", "quantidade": 45, "salario_medio": 2200},
				{"nome": "Motorista", "quantidade": 35, "salario_medio": 3200},
				{"nome": "Operador de Máquinas", "quantidade": 25, "salario_medio": 4200},
				{"nome": "Fiscal de Obras", "quantidade": 10, "salario_medio": 5500},
				{"nome": "Engenheiro", "quantidade": 5, "salario_medio": 9800}
			]
		},
		{
			"categoria": "Assistência Social",
			"total_servidores": 85,
			"percentual": 6.8,
			"folha_total": 420000,
			"cargos": [
				{"nome": "Assistente Social", "quantidade": 25, "salario_medio": 4200},
				{"nome": "Psicólogo", "quantidade": 15, "salario_medio": 4800},
				{"nome": "Educador Social", "quantidade": 35, "salario_medio": 3200},
				{"nome": "Coordenador CRAS", "quantidade": 8, "salario_medio": 6500},
				{"nome": "Auxiliar Social", "quantidade": 2, "salario_medio": 2800}
			]
		}
	]

def get_faixas_salariais():
	"""Retorna informações sobre as faixas salariais."""
	return [
		{
			"faixa": "Até R$ 2.000",
			"quantidade": 120,
			"percentual": 9.6,
			"total_folha": 192000,
			"cargos_principais": ["Auxiliar de Serviços Gerais", "Vigia", "Auxiliar de Limpeza"]
		},
		{
			"faixa": "R$ 2.001 a R$ 5.000",
			"quantidade": 650,
			"percentual": 52.0,
			"total_folha": 2275000,
			"cargos_principais": ["Professor", "Técnico em Enfermagem", "Assistente Administrativo"]
		},
		{
			"faixa": "R$ 5.001 a R$ 10.000",
			"quantidade": 380,
			"percentual": 30.4,
			"total_folha": 2660000,
			"cargos_principais": ["Enfermeiro", "Analista", "Coordenador"]
		},
		{
			"faixa": "R$ 10.001 a R$ 15.000",
			"quantidade": 80,
			"percentual": 6.4,
			"total_folha": 1000000,
			"cargos_principais": ["Médico", "Procurador", "Secretário"]
		},
		{
			"faixa": "Acima de R$ 15.000",
			"quantidade": 20,
			"percentual": 1.6,
			"total_folha": 373000,
			"cargos_principais": ["Prefeito", "Vice-Prefeito", "Secretários Especiais"]
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
			{"label": _("Gabinete do Prefeito"), "value": "gabinete"},
			{"label": _("Secretaria de Administração"), "value": "administracao"},
			{"label": _("Secretaria de Educação"), "value": "educacao"},
			{"label": _("Secretaria de Saúde"), "value": "saude"},
			{"label": _("Secretaria de Obras"), "value": "obras"},
			{"label": _("Secretaria de Assistência Social"), "value": "assistencia"}
		]

@frappe.whitelist(allow_guest=True)
def get_servidores_ajax(filtros=None):
	"""Endpoint AJAX para buscar servidores com filtros."""
	if filtros:
		filtros = json.loads(filtros)

	# Aplicar filtros e retornar dados
	servidores = get_servidores_data()

	return {
		"success": True,
		"data": servidores,
		"total": len(servidores),
		"total_folha": sum([s["salario_liquido"] for s in servidores])
	}

@frappe.whitelist(allow_guest=True)
def get_folha_pagamento(mes=None, ano=None):
	"""Endpoint para buscar folha de pagamento específica."""
	if not mes:
		mes = frappe.utils.nowdate().split('-')[1]
	if not ano:
		ano = frappe.utils.nowdate().split('-')[0]

	# Em um ambiente real, buscaria dados do banco
	folha = get_servidores_data()

	return {
		"success": True,
		"data": folha,
		"mes": mes,
		"ano": ano,
		"total_bruto": sum([s["salario_base"] + s["gratificacoes"] for s in folha]),
		"total_liquido": sum([s["salario_liquido"] for s in folha])
	}

@frappe.whitelist(allow_guest=True)
def exportar_folha(formato="csv", filtros=None):
	"""Exporta dados da folha de pagamento em diferentes formatos."""
	if filtros:
		filtros = json.loads(filtros)

	servidores = get_servidores_data()

	if formato == "csv":
		return gerar_csv_folha(servidores)
	elif formato == "xlsx":
		return gerar_xlsx_folha(servidores)
	elif formato == "pdf":
		return gerar_pdf_folha(servidores)

	return {"error": "Formato não suportado"}

def gerar_csv_folha(servidores):
	"""Gera arquivo CSV com dados da folha de pagamento."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	# Cabeçalho
	writer.writerow([
		"Nome", "Cargo", "Órgão", "Situação", "Vínculo",
		"Salário Base", "Gratificações", "Descontos", "Salário Líquido", "Admissão"
	])

	# Dados
	for servidor in servidores:
		writer.writerow([
			servidor["nome"],
			servidor["cargo"],
			servidor["orgao"],
			servidor["situacao"],
			servidor["tipo_vinculo"],
			servidor["salario_base_formatado"],
			servidor["gratificacoes_formatadas"],
			servidor["descontos_formatados"],
			servidor["salario_liquido_formatado"],
			servidor["admissao_formatada"]
		])

	return {
		"content": output.getvalue(),
		"filename": f"folha_pagamento_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}