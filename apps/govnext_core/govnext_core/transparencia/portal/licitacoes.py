# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de licitações do Portal da Transparência.
	"""
	context.title = _("Licitações")
	context.subtitle = _("Acesse os procedimentos licitatórios realizados pela Prefeitura Municipal, os processos em andamento e as justificativas de contratações.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Dados de licitações
	context.licitacoes = get_licitacoes_data()

	# Estatísticas de licitações
	context.estatisticas_licitacoes = get_estatisticas_licitacoes()

	# Gráficos de licitações
	context.graficos = get_graficos_licitacoes()

	# Modalidades de licitação
	context.modalidades = get_modalidades_licitacao()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa de licitações."""
	return {
		"periodo": [
			{"label": _("Último mês"), "value": "ultimo_mes"},
			{"label": _("Últimos 3 meses"), "value": "ultimo_trimestre"},
			{"label": _("Último semestre"), "value": "ultimo_semestre"},
			{"label": _("Último ano"), "value": "ultimo_ano"},
			{"label": _("Período personalizado"), "value": "personalizado"}
		],
		"situacao": [
			{"label": _("Todas as situações"), "value": "todas"},
			{"label": _("Em andamento"), "value": "andamento"},
			{"label": _("Homologadas"), "value": "homologadas"},
			{"label": _("Suspensas"), "value": "suspensas"},
			{"label": _("Canceladas"), "value": "canceladas"},
			{"label": _("Desertas"), "value": "desertas"}
		],
		"modalidade": [
			{"label": _("Todas as modalidades"), "value": "todas"},
			{"label": _("Pregão Eletrônico"), "value": "pregao_eletronico"},
			{"label": _("Pregão Presencial"), "value": "pregao_presencial"},
			{"label": _("Concorrência"), "value": "concorrencia"},
			{"label": _("Tomada de Preços"), "value": "tomada_precos"},
			{"label": _("Convite"), "value": "convite"},
			{"label": _("Dispensa de Licitação"), "value": "dispensa"},
			{"label": _("Inexigibilidade"), "value": "inexigibilidade"}
		],
		"orgao": get_orgaos_list(),
		"ordenacao": [
			{"label": _("Data (mais recente)"), "value": "data_desc"},
			{"label": _("Data (mais antiga)"), "value": "data_asc"},
			{"label": _("Valor (maior)"), "value": "valor_desc"},
			{"label": _("Valor (menor)"), "value": "valor_asc"},
			{"label": _("Situação"), "value": "situacao"},
			{"label": _("Modalidade"), "value": "modalidade"}
		]
	}

def get_licitacoes_data():
	"""Retorna os dados de licitações para exibição."""
	# Em um ambiente real, estes dados viriam do banco de dados

	licitacoes_exemplo = [
		{
			"id": "2025/LIC-001",
			"numero": "001/2025",
			"data_abertura": "2025-06-20",
			"data_entrega": "2025-06-18",
			"modalidade": "Pregão Eletrônico",
			"objeto": "Aquisição de medicamentos básicos para as unidades de saúde",
			"situacao": "Em andamento",
			"valor_estimado": 245000.00,
			"orgao": "Secretaria de Saúde",
			"processo": "2025.003.012345-8",
			"edital": "001_2025_pregao_medicamentos.pdf",
			"participantes": 8,
			"tipo": "Menor Preço",
			"comissao": "Comissão Permanente de Licitação"
		},
		{
			"id": "2025/LIC-002",
			"numero": "002/2025",
			"data_abertura": "2025-06-15",
			"data_entrega": "2025-06-13",
			"modalidade": "Tomada de Preços",
			"objeto": "Pavimentação asfáltica da Rua das Flores",
			"situacao": "Homologada",
			"valor_estimado": 850000.00,
			"valor_homologado": 795000.00,
			"vencedor": "Construtora ABC S.A.",
			"orgao": "Secretaria de Obras",
			"processo": "2025.002.008765-4",
			"edital": "002_2025_tomada_precos_pavimentacao.pdf",
			"participantes": 5,
			"tipo": "Menor Preço",
			"comissao": "Comissão Especial de Obras"
		},
		{
			"id": "2025/LIC-003",
			"numero": "003/2025",
			"data_abertura": "2025-06-10",
			"data_entrega": "2025-06-08",
			"modalidade": "Pregão Eletrônico",
			"objeto": "Contratação de empresa para serviços de limpeza urbana",
			"situacao": "Homologada",
			"valor_estimado": 1200000.00,
			"valor_homologado": 1150000.00,
			"vencedor": "Empresa de Limpeza Municipal Ltda",
			"orgao": "Secretaria de Serviços Urbanos",
			"processo": "2025.004.015678-9",
			"edital": "003_2025_pregao_limpeza.pdf",
			"participantes": 12,
			"tipo": "Menor Preço",
			"comissao": "Comissão Permanente de Licitação"
		},
		{
			"id": "2025/LIC-004",
			"numero": "004/2025",
			"data_abertura": "2025-06-25",
			"data_entrega": "2025-06-23",
			"modalidade": "Concorrência",
			"objeto": "Construção de Centro de Educação Infantil",
			"situacao": "Em andamento",
			"valor_estimado": 2500000.00,
			"orgao": "Secretaria de Educação",
			"processo": "2025.001.018901-2",
			"edital": "004_2025_concorrencia_escola.pdf",
			"participantes": 6,
			"tipo": "Menor Preço",
			"comissao": "Comissão Especial de Obras"
		}
	]

	# Formatar valores para exibição
	for licitacao in licitacoes_exemplo:
		licitacao["valor_estimado_formatado"] = fmt_money(licitacao["valor_estimado"], currency="BRL")
		if licitacao.get("valor_homologado"):
			licitacao["valor_homologado_formatado"] = fmt_money(licitacao["valor_homologado"], currency="BRL")
		licitacao["data_abertura_formatada"] = frappe.utils.formatdate(licitacao["data_abertura"], "dd/MM/yyyy")
		licitacao["data_entrega_formatada"] = frappe.utils.formatdate(licitacao["data_entrega"], "dd/MM/yyyy")

	return licitacoes_exemplo

def get_estatisticas_licitacoes():
	"""Retorna estatísticas resumidas das licitações."""
	return {
		"total_licitacoes": 45,
		"em_andamento": 12,
		"homologadas": 28,
		"canceladas": 3,
		"desertas": 2,
		"valor_total_estimado": fmt_money(18500000, currency="BRL"),
		"valor_total_homologado": fmt_money(16750000, currency="BRL"),
		"economia_gerada": fmt_money(1750000, currency="BRL"),
		"percentual_economia": 9.5,
		"media_participantes": 8.3,
		"prazo_medio_processo": 45  # dias
	}

def get_graficos_licitacoes():
	"""Retorna dados para gráficos de licitações."""
	return {
		"evolucao_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"licitacoes": [8, 12, 6, 9, 11, 7],
			"valor_estimado": [2800000, 4200000, 1800000, 3100000, 3800000, 2500000],
			"valor_homologado": [2650000, 3950000, 1650000, 2890000, 3450000, 2300000]
		},
		"por_modalidade": {
			"labels": ["Pregão Eletrônico", "Pregão Presencial", "Concorrência", "Tomada de Preços", "Convite", "Dispensa"],
			"valores": [8500000, 1200000, 4800000, 2400000, 850000, 1250000],
			"quantidade": [18, 4, 8, 6, 5, 12],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1", "#fd7e14"]
		},
		"situacao_licitacoes": {
			"labels": ["Homologadas", "Em Andamento", "Canceladas", "Desertas", "Suspensas"],
			"valores": [28, 12, 3, 2, 0],
			"cores": ["#28a745", "#007bff", "#dc3545", "#6c757d", "#ffc107"]
		},
		"economia_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"economia": [150000, 250000, 150000, 210000, 350000, 200000],
			"percentual": [5.4, 6.0, 8.3, 6.8, 9.2, 8.0]
		}
	}

def get_modalidades_licitacao():
	"""Retorna informações sobre as modalidades de licitação utilizadas."""
	return [
		{
			"nome": "Pregão Eletrônico",
			"quantidade": 18,
			"valor_total": 8500000,
			"percentual": 40.0,
			"prazo_medio": 30,
			"economia_media": 8.5,
			"descricao": "Modalidade de licitação para aquisição de bens e serviços comuns realizados por meio da internet"
		},
		{
			"nome": "Concorrência",
			"quantidade": 8,
			"valor_total": 4800000,
			"percentual": 17.8,
			"prazo_medio": 60,
			"economia_media": 7.2,
			"descricao": "Modalidade de licitação para obras, serviços e compras de grande valor"
		},
		{
			"nome": "Tomada de Preços",
			"quantidade": 6,
			"valor_total": 2400000,
			"percentual": 13.3,
			"prazo_medio": 45,
			"economia_media": 6.8,
			"descricao": "Modalidade de licitação para obras, serviços e compras de valor intermediário"
		},
		{
			"nome": "Dispensa de Licitação",
			"quantidade": 12,
			"valor_total": 1250000,
			"percentual": 26.7,
			"prazo_medio": 15,
			"economia_media": 0.0,
			"descricao": "Contratações diretas permitidas por lei em situações específicas"
		},
		{
			"nome": "Pregão Presencial",
			"quantidade": 4,
			"valor_total": 1200000,
			"percentual": 8.9,
			"prazo_medio": 35,
			"economia_media": 9.1,
			"descricao": "Modalidade de licitação presencial para aquisição de bens e serviços comuns"
		},
		{
			"nome": "Convite",
			"quantidade": 5,
			"valor_total": 850000,
			"percentual": 11.1,
			"prazo_medio": 25,
			"economia_media": 5.5,
			"descricao": "Modalidade de licitação para obras, serviços e compras de pequeno valor"
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
			{"label": _("Secretaria de Serviços Urbanos"), "value": "servicos_urbanos"}
		]

@frappe.whitelist(allow_guest=True)
def get_licitacoes_ajax(filtros=None):
	"""Endpoint AJAX para buscar licitações com filtros."""
	if filtros:
		filtros = json.loads(filtros)

	# Aplicar filtros e retornar dados
	licitacoes = get_licitacoes_data()

	return {
		"success": True,
		"data": licitacoes,
		"total": len(licitacoes),
		"total_valor": sum([l["valor_estimado"] for l in licitacoes])
	}

@frappe.whitelist(allow_guest=True)
def get_edital_download(licitacao_id):
	"""Endpoint para download de edital."""
	# Em um ambiente real, buscaria o arquivo do edital
	return {
		"success": True,
		"filename": f"edital_{licitacao_id}.pdf",
		"url": f"/files/editais/edital_{licitacao_id}.pdf"
	}

@frappe.whitelist(allow_guest=True)
def exportar_licitacoes(formato="csv", filtros=None):
	"""Exporta dados de licitações em diferentes formatos."""
	if filtros:
		filtros = json.loads(filtros)

	licitacoes = get_licitacoes_data()

	if formato == "csv":
		return gerar_csv_licitacoes(licitacoes)
	elif formato == "xlsx":
		return gerar_xlsx_licitacoes(licitacoes)
	elif formato == "pdf":
		return gerar_pdf_licitacoes(licitacoes)

	return {"error": "Formato não suportado"}

def gerar_csv_licitacoes(licitacoes):
	"""Gera arquivo CSV com dados de licitações."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	# Cabeçalho
	writer.writerow([
		"Número", "Data Abertura", "Modalidade", "Objeto", "Situação",
		"Valor Estimado", "Valor Homologado", "Órgão", "Participantes", "Vencedor"
	])

	# Dados
	for licitacao in licitacoes:
		writer.writerow([
			licitacao["numero"],
			licitacao["data_abertura_formatada"],
			licitacao["modalidade"],
			licitacao["objeto"],
			licitacao["situacao"],
			licitacao["valor_estimado_formatado"],
			licitacao.get("valor_homologado_formatado", ""),
			licitacao["orgao"],
			licitacao["participantes"],
			licitacao.get("vencedor", "")
		])

	return {
		"content": output.getvalue(),
		"filename": f"licitacoes_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}