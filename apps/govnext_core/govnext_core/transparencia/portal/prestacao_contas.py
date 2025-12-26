# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de prestação de contas do Portal da Transparência.
	"""
	context.title = _("Prestação de Contas")
	context.subtitle = _("Oferece relatórios detalhados sobre receitas, despesas e execução orçamentária permitindo acompanhar a gestão dos recursos públicos.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Relatórios disponíveis
	context.relatorios = get_relatorios_disponiveis()

	# Balancetes e demonstrativos
	context.balancetes = get_balancetes()

	# Relatórios de gestão fiscal
	context.relatorios_gestao_fiscal = get_relatorios_gestao_fiscal()

	# Prestação de contas anual
	context.prestacao_contas_anual = get_prestacao_contas_anual()

	# Indicadores financeiros
	context.indicadores_financeiros = get_indicadores_financeiros()

	# Cumprimento de metas
	context.cumprimento_metas = get_cumprimento_metas()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa de prestação de contas."""
	return {
		"exercicio": [
			{"label": "2025", "value": "2025"},
			{"label": "2024", "value": "2024"},
			{"label": "2023", "value": "2023"},
			{"label": "2022", "value": "2022"},
			{"label": "2021", "value": "2021"}
		],
		"periodo": [
			{"label": _("1º Bimestre"), "value": "1_bimestre"},
			{"label": _("2º Bimestre"), "value": "2_bimestre"},
			{"label": _("3º Bimestre"), "value": "3_bimestre"},
			{"label": _("4º Bimestre"), "value": "4_bimestre"},
			{"label": _("5º Bimestre"), "value": "5_bimestre"},
			{"label": _("6º Bimestre"), "value": "6_bimestre"},
			{"label": _("1º Quadrimestre"), "value": "1_quadrimestre"},
			{"label": _("2º Quadrimestre"), "value": "2_quadrimestre"},
			{"label": _("3º Quadrimestre"), "value": "3_quadrimestre"},
			{"label": _("Anual"), "value": "anual"}
		],
		"tipo_relatorio": [
			{"label": _("Todos os tipos"), "value": "todos"},
			{"label": _("Balancete Orçamentário"), "value": "balancete_orcamentario"},
			{"label": _("Balancete Financeiro"), "value": "balancete_financeiro"},
			{"label": _("Balancete Patrimonial"), "value": "balancete_patrimonial"},
			{"label": _("Relatório de Gestão Fiscal"), "value": "rgf"},
			{"label": _("Relatório Resumido de Execução Orçamentária"), "value": "rreo"},
			{"label": _("Demonstrativo de Aplicação na Educação"), "value": "educacao"},
			{"label": _("Demonstrativo de Aplicação na Saúde"), "value": "saude"}
		],
		"formato": [
			{"label": _("Todos os formatos"), "value": "todos"},
			{"label": _("PDF"), "value": "pdf"},
			{"label": _("Excel"), "value": "xlsx"},
			{"label": _("CSV"), "value": "csv"},
			{"label": _("XML"), "value": "xml"}
		]
	}

def get_relatorios_disponiveis():
	"""Retorna os relatórios de prestação de contas disponíveis."""
	return [
		{
			"codigo": "RGF_2025_2B",
			"nome": "Relatório de Gestão Fiscal - 2º Bimestre 2025",
			"tipo": "Relatório de Gestão Fiscal",
			"periodo": "Março-Abril/2025",
			"data_publicacao": "2025-05-30",
			"data_referencia": "2025-04-30",
			"arquivo": "rgf_2025_2b.pdf",
			"tamanho": "2.8 MB",
			"downloads": 245,
			"descricao": "Demonstra os limites e resultados fiscais do município",
			"status": "Publicado"
		},
		{
			"codigo": "RREO_2025_2B",
			"nome": "Relatório Resumido de Execução Orçamentária - 2º Bimestre 2025",
			"tipo": "RREO",
			"periodo": "Março-Abril/2025",
			"data_publicacao": "2025-05-30",
			"data_referencia": "2025-04-30",
			"arquivo": "rreo_2025_2b.pdf",
			"tamanho": "3.5 MB",
			"downloads": 189,
			"descricao": "Demonstra a execução das receitas e despesas orçamentárias",
			"status": "Publicado"
		},
		{
			"codigo": "BAL_ORC_2025_05",
			"nome": "Balancete Orçamentário - Maio 2025",
			"tipo": "Balancete Orçamentário",
			"periodo": "Maio/2025",
			"data_publicacao": "2025-06-15",
			"data_referencia": "2025-05-31",
			"arquivo": "balancete_orcamentario_2025_05.pdf",
			"tamanho": "1.8 MB",
			"downloads": 156,
			"descricao": "Posição das receitas e despesas orçamentárias",
			"status": "Publicado"
		},
		{
			"codigo": "BAL_FIN_2025_05",
			"nome": "Balancete Financeiro - Maio 2025",
			"tipo": "Balancete Financeiro",
			"periodo": "Maio/2025",
			"data_publicacao": "2025-06-15",
			"data_referencia": "2025-05-31",
			"arquivo": "balancete_financeiro_2025_05.pdf",
			"tamanho": "1.5 MB",
			"downloads": 98,
			"descricao": "Demonstra a movimentação financeira do município",
			"status": "Publicado"
		},
		{
			"codigo": "EDUC_2025_1Q",
			"nome": "Demonstrativo de Aplicação na Educação - 1º Quadrimestre 2025",
			"tipo": "Demonstrativo Educação",
			"periodo": "Janeiro-Abril/2025",
			"data_publicacao": "2025-05-20",
			"data_referencia": "2025-04-30",
			"arquivo": "demonstrativo_educacao_2025_1q.pdf",
			"tamanho": "2.2 MB",
			"downloads": 167,
			"descricao": "Aplicação de recursos na manutenção e desenvolvimento do ensino",
			"status": "Publicado"
		},
		{
			"codigo": "SAUDE_2025_1Q",
			"nome": "Demonstrativo de Aplicação na Saúde - 1º Quadrimestre 2025",
			"tipo": "Demonstrativo Saúde",
			"periodo": "Janeiro-Abril/2025",
			"data_publicacao": "2025-05-20",
			"data_referencia": "2025-04-30",
			"arquivo": "demonstrativo_saude_2025_1q.pdf",
			"tamanho": "2.0 MB",
			"downloads": 143,
			"descricao": "Aplicação de recursos em ações e serviços públicos de saúde",
			"status": "Publicado"
		}
	]

def get_balancetes():
	"""Retorna dados dos balancetes mais recentes."""
	return {
		"balancete_orcamentario": {
			"periodo": "Maio/2025",
			"receita_orcada": 24000000.00,
			"receita_arrecadada": 18450000.00,
			"percentual_receita": 76.9,
			"despesa_orcada": 23500000.00,
			"despesa_empenhada": 19650000.00,
			"despesa_liquidada": 17800000.00,
			"despesa_paga": 15600000.00,
			"percentual_empenho": 83.6,
			"percentual_liquidacao": 90.6,
			"percentual_pagamento": 87.6,
			"resultado_orcamentario": 2850000.00,
			"situacao": "Superávit"
		},
		"balancete_financeiro": {
			"periodo": "Maio/2025",
			"disponibilidades": 8920000.00,
			"conta_corrente": 6850000.00,
			"aplicacoes_financeiras": 2070000.00,
			"obrigacoes_financeiras": 4070000.00,
			"restos_pagar": 3550000.00,
			"depositos": 520000.00,
			"resultado_financeiro": 4850000.00,
			"situacao": "Positivo"
		},
		"balancete_patrimonial": {
			"periodo": "Maio/2025",
			"ativo_total": 185000000.00,
			"ativo_circulante": 15200000.00,
			"ativo_nao_circulante": 169800000.00,
			"passivo_total": 185000000.00,
			"passivo_circulante": 8500000.00,
			"passivo_nao_circulante": 12800000.00,
			"patrimonio_liquido": 163700000.00,
			"variacao_patrimonial": 2.3
		}
	}

def get_relatorios_gestao_fiscal():
	"""Retorna dados dos relatórios de gestão fiscal."""
	return {
		"limites_gastos_pessoal": {
			"limite_legal": 54.0,  # % da RCL
			"realizado": 42.5,
			"limite_prudencial": 51.3,  # 95% do limite legal
			"limite_alerta": 48.6,   # 90% do limite legal
			"situacao": "Dentro do limite",
			"folga": 11.5
		},
		"divida_consolidada": {
			"limite_legal": 120.0,  # % da RCL
			"realizado": 7.7,
			"situacao": "Dentro do limite",
			"folga": 112.3
		},
		"operacoes_credito": {
			"limite_legal": 16.0,  # % da RCL
			"realizado": 2.1,
			"situacao": "Dentro do limite",
			"folga": 13.9
		},
		"restos_pagar": {
			"disponibilidade_caixa": 8920000.00,
			"restos_pagar_processados": 2850000.00,
			"restos_pagar_nao_processados": 700000.00,
			"total_restos_pagar": 3550000.00,
			"capacidade_pagamento": "Suficiente"
		},
		"resultado_nominal": {
			"meta": -500000.00,
			"realizado": 2850000.00,
			"situacao": "Meta superada"
		},
		"resultado_primario": {
			"meta": 1200000.00,
			"realizado": 2850000.00,
			"situacao": "Meta superada"
		}
	}

def get_prestacao_contas_anual():
	"""Retorna dados da prestação de contas anual."""
	return [
		{
			"exercicio": "2024",
			"status": "Aprovada",
			"data_aprovacao": "2025-03-31",
			"parecer_tribunal": "Aprovado com ressalvas",
			"resultado_orcamentario": 3200000.00,
			"resultado_financeiro": 5800000.00,
			"cumprimento_educacao": 26.8,  # %
			"cumprimento_saude": 17.5,     # %
			"limite_pessoal": 41.2,        # %
			"principais_realizacoes": [
				"Construção de 3 novas escolas",
				"Pavimentação de 25 km de vias",
				"Implantação de 2 UBS",
				"Digitalização de 85% dos serviços"
			],
			"arquivo_completo": "prestacao_contas_2024.pdf"
		},
		{
			"exercicio": "2023",
			"status": "Aprovada",
			"data_aprovacao": "2024-03-28",
			"parecer_tribunal": "Aprovado",
			"resultado_orcamentario": 2800000.00,
			"resultado_financeiro": 4200000.00,
			"cumprimento_educacao": 25.9,
			"cumprimento_saude": 16.8,
			"limite_pessoal": 43.1,
			"principais_realizacoes": [
				"Revitalização do centro da cidade",
				"Criação de 5 praças públicas",
				"Modernização da frota escolar",
				"Implementação do prontuário eletrônico"
			],
			"arquivo_completo": "prestacao_contas_2023.pdf"
		}
	]

def get_indicadores_financeiros():
	"""Retorna indicadores financeiros do município."""
	return {
		"liquidez": {
			"ativo_circulante": 15200000.00,
			"passivo_circulante": 8500000.00,
			"indice_liquidez": 1.79,
			"interpretacao": "Boa capacidade de pagamento",
			"benchmark": "Acima de 1.0"
		},
		"endividamento": {
			"passivo_total": 21300000.00,
			"ativo_total": 185000000.00,
			"indice_endividamento": 11.5,
			"interpretacao": "Baixo endividamento",
			"benchmark": "Até 20%"
		},
		"autonomia_financeira": {
			"receitas_proprias": 6050000.00,
			"receitas_totais": 18450000.00,
			"indice_autonomia": 32.8,
			"interpretacao": "Dependência moderada de transferências",
			"benchmark": "Acima de 30%"
		},
		"eficiencia_arrecadacao": {
			"iptu_orcado": 2500000.00,
			"iptu_arrecadado": 1850000.00,
			"eficiencia_iptu": 74.0,
			"iss_orcado": 1800000.00,
			"iss_arrecadado": 1250000.00,
			"eficiencia_iss": 69.4,
			"eficiencia_geral": 71.7
		}
	}

def get_cumprimento_metas():
	"""Retorna dados sobre cumprimento de metas fiscais e constitucionais."""
	return {
		"educacao": {
			"aplicacao_minima": 25.0,  # %
			"aplicacao_realizada": 26.8,
			"valor_minimo": 4612500.00,
			"valor_aplicado": 4936000.00,
			"excesso": 323500.00,
			"status": "Cumprida com folga",
			"detalhamento": {
				"ensino_fundamental": 3200000.00,
				"educacao_infantil": 1200000.00,
				"outros": 536000.00
			}
		},
		"saude": {
			"aplicacao_minima": 15.0,  # %
			"aplicacao_realizada": 17.5,
			"valor_minimo": 2767500.00,
			"valor_aplicado": 3228750.00,
			"excesso": 461250.00,
			"status": "Cumprida com folga",
			"detalhamento": {
				"atencao_basica": 1800000.00,
				"assistencia_hospitalar": 900000.00,
				"vigilancia_saude": 350000.00,
				"outros": 178750.00
			}
		},
		"previdencia": {
			"deficit_atuarial": 0.00,
			"contribuicao_servidor": 11.0,
			"contribuicao_patronal": 22.0,
			"situacao": "Equilibrada",
			"observacoes": "RPPS em situação atuarial equilibrada"
		}
	}

@frappe.whitelist(allow_guest=True)
def get_relatorio_detalhes(codigo_relatorio):
	"""Endpoint para buscar detalhes de um relatório específico."""
	relatorios = get_relatorios_disponiveis()
	relatorio = next((r for r in relatorios if r["codigo"] == codigo_relatorio), None)

	if relatorio:
		# Adicionar dados específicos baseado no tipo
		if "RGF" in codigo_relatorio:
			relatorio["dados_especificos"] = get_relatorios_gestao_fiscal()
		elif "RREO" in codigo_relatorio:
			relatorio["dados_especificos"] = get_balancetes()["balancete_orcamentario"]
		elif "EDUC" in codigo_relatorio:
			relatorio["dados_especificos"] = get_cumprimento_metas()["educacao"]
		elif "SAUDE" in codigo_relatorio:
			relatorio["dados_especificos"] = get_cumprimento_metas()["saude"]

		return {
			"success": True,
			"data": relatorio
		}
	else:
		return {
			"success": False,
			"error": "Relatório não encontrado"
		}

@frappe.whitelist(allow_guest=True)
def download_relatorio(codigo_relatorio):
	"""Endpoint para download de relatório."""
	relatorios = get_relatorios_disponiveis()
	relatorio = next((r for r in relatorios if r["codigo"] == codigo_relatorio), None)

	if relatorio:
		# Incrementar contador de downloads
		# Em um ambiente real, atualizaria no banco de dados
		
		return {
			"success": True,
			"filename": relatorio["arquivo"],
			"url": f"/files/prestacao_contas/{relatorio['arquivo']}",
			"tamanho": relatorio["tamanho"]
		}
	else:
		return {
			"success": False,
			"error": "Relatório não encontrado"
		}

@frappe.whitelist(allow_guest=True)
def get_historico_relatorios(tipo=None, exercicio=None):
	"""Endpoint para buscar histórico de relatórios."""
	relatorios = get_relatorios_disponiveis()

	# Filtrar por tipo se especificado
	if tipo and tipo != "todos":
		relatorios = [r for r in relatorios if r["tipo"] == tipo]

	# Filtrar por exercício se especificado
	if exercicio:
		relatorios = [r for r in relatorios if exercicio in r["codigo"]]

	return {
		"success": True,
		"data": relatorios,
		"total": len(relatorios)
	}

@frappe.whitelist(allow_guest=True)
def exportar_prestacao_contas(formato="csv", tipo="completo"):
	"""Exporta dados de prestação de contas em diferentes formatos."""
	dados = {
		"relatorios": get_relatorios_disponiveis(),
		"balancetes": get_balancetes(),
		"indicadores": get_indicadores_financeiros(),
		"metas": get_cumprimento_metas()
	}

	if formato == "csv":
		return gerar_csv_prestacao_contas(dados, tipo)
	elif formato == "xlsx":
		return gerar_xlsx_prestacao_contas(dados, tipo)
	elif formato == "json":
		return json.dumps(dados, indent=2, ensure_ascii=False, default=str)

	return {"error": "Formato não suportado"}

def gerar_csv_prestacao_contas(dados, tipo):
	"""Gera arquivo CSV com dados de prestação de contas."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	if tipo == "relatorios":
		writer.writerow([
			"Código", "Nome", "Tipo", "Período", "Data Publicação",
			"Status", "Downloads", "Arquivo"
		])
		
		for relatorio in dados["relatorios"]:
			writer.writerow([
				relatorio["codigo"],
				relatorio["nome"],
				relatorio["tipo"],
				relatorio["periodo"],
				relatorio["data_publicacao"],
				relatorio["status"],
				relatorio["downloads"],
				relatorio["arquivo"]
			])
	
	elif tipo == "indicadores":
		writer.writerow([
			"Indicador", "Valor", "Interpretação", "Benchmark"
		])
		
		for categoria, dados_cat in dados["indicadores"].items():
			if isinstance(dados_cat, dict):
				for indicador, valor in dados_cat.items():
					if indicador not in ["interpretacao", "benchmark"]:
						writer.writerow([
							f"{categoria}_{indicador}",
							valor,
							dados_cat.get("interpretacao", ""),
							dados_cat.get("benchmark", "")
						])

	return {
		"content": output.getvalue(),
		"filename": f"prestacao_contas_{tipo}_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}