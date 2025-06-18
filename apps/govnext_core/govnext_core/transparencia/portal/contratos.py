# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de contratos do Portal da Transparência.
	"""
	context.title = _("Contratos")
	context.subtitle = _("Acesse informações sobre todos os contratos firmados pela prefeitura, incluindo valores, fornecedores, vigências e objetos contratados.")

	# Dados de contratos
	context.contratos = get_contratos_data()

	# Estatísticas de contratos
	context.estatisticas_contratos = get_estatisticas_contratos()

	# Filtros disponíveis
	context.filtros = get_filtros()

	return context

def get_contratos_data():
	"""Retorna os dados de contratos para exibição."""
	contratos_exemplo = [
		{
			"id": "2025/CT-089",
			"numero": "089/2025",
			"fornecedor": "Empresa de Limpeza Municipal Ltda",
			"cnpj": "12.345.678/0001-90",
			"objeto": "Prestação de serviços de limpeza urbana",
			"valor_inicial": 540000.00,
			"valor_atual": 540000.00,
			"data_assinatura": "2025-01-15",
			"data_inicio": "2025-02-01",
			"data_fim": "2026-01-31",
			"situacao": "Vigente",
			"orgao": "Secretaria de Serviços Urbanos",
			"modalidade": "Pregão Eletrônico",
			"processo": "2024.001.987654-3",
			"fiscal": "João Silva Santos",
			"aditivos": 0,
			"percentual_executado": 45.2
		},
		{
			"id": "2025/CT-156",
			"numero": "156/2025",
			"fornecedor": "Construtora ABC S.A.",
			"cnpj": "98.765.432/0001-10",
			"objeto": "Construção de praça pública no bairro Centro",
			"valor_inicial": 850000.00,
			"valor_atual": 920000.00,
			"data_assinatura": "2025-03-10",
			"data_inicio": "2025-03-20",
			"data_fim": "2025-09-20",
			"situacao": "Em execução",
			"orgao": "Secretaria de Obras",
			"modalidade": "Tomada de Preços",
			"processo": "2024.002.123456-7",
			"fiscal": "Maria Oliveira Costa",
			"aditivos": 1,
			"percentual_executado": 68.5
		},
		{
			"id": "2025/CT-203",
			"numero": "203/2025",
			"fornecedor": "Farmácia Saúde & Vida",
			"cnpj": "11.222.333/0001-44",
			"objeto": "Fornecimento de medicamentos básicos",
			"valor_inicial": 125000.00,
			"valor_atual": 125000.00,
			"data_assinatura": "2025-04-05",
			"data_inicio": "2025-04-15",
			"data_fim": "2025-10-15",
			"situacao": "Vigente",
			"orgao": "Secretaria de Saúde",
			"modalidade": "Dispensa de Licitação",
			"processo": "2025.003.456789-1",
			"fiscal": "Pedro Almeida Lima",
			"aditivos": 0,
			"percentual_executado": 32.1
		}
	]

	# Formatar valores e datas
	for contrato in contratos_exemplo:
		contrato["valor_inicial_formatado"] = fmt_money(contrato["valor_inicial"], currency="BRL")
		contrato["valor_atual_formatado"] = fmt_money(contrato["valor_atual"], currency="BRL")
		contrato["data_assinatura_formatada"] = frappe.utils.formatdate(contrato["data_assinatura"], "dd/MM/yyyy")
		contrato["data_inicio_formatada"] = frappe.utils.formatdate(contrato["data_inicio"], "dd/MM/yyyy")
		contrato["data_fim_formatada"] = frappe.utils.formatdate(contrato["data_fim"], "dd/MM/yyyy")

		# Calcular dias restantes
		data_fim = getdate(contrato["data_fim"])
		hoje = getdate()
		contrato["dias_restantes"] = (data_fim - hoje).days if data_fim > hoje else 0

		# Definir cor do status
		if contrato["situacao"] == "Vigente":
			contrato["status_cor"] = "success"
		elif contrato["situacao"] == "Em execução":
			contrato["status_cor"] = "primary"
		elif contrato["situacao"] == "Encerrado":
			contrato["status_cor"] = "secondary"
		else:
			contrato["status_cor"] = "warning"

	return contratos_exemplo

def get_estatisticas_contratos():
	"""Retorna estatísticas resumidas dos contratos."""
	return {
		"total_contratos_vigentes": 89,
		"valor_total_contratos": fmt_money(12500000, currency="BRL"),
		"contratos_vencendo": 8,
		"valor_medio_contrato": fmt_money(140450, currency="BRL"),
		"total_aditivos": 23,
		"economia_licitacoes": fmt_money(890000, currency="BRL"),
		"percentual_execucao_media": 48.7,
		"fornecedores_ativos": 156
	}

def get_filtros():
	"""Retorna os filtros disponíveis."""
	return {
		"situacao": [
			{"label": _("Todas as situações"), "value": "todas"},
			{"label": _("Vigente"), "value": "vigente"},
			{"label": _("Em execução"), "value": "em_execucao"},
			{"label": _("Encerrado"), "value": "encerrado"},
			{"label": _("Suspenso"), "value": "suspenso"}
		],
		"modalidade": [
			{"label": _("Todas as modalidades"), "value": "todas"},
			{"label": _("Pregão Eletrônico"), "value": "pregao_eletronico"},
			{"label": _("Tomada de Preços"), "value": "tomada_precos"},
			{"label": _("Concorrência"), "value": "concorrencia"},
			{"label": _("Dispensa de Licitação"), "value": "dispensa"},
			{"label": _("Inexigibilidade"), "value": "inexigibilidade"}
		],
		"orgao": [
			{"label": _("Todos os órgãos"), "value": "todos"},
			{"label": _("Secretaria de Obras"), "value": "obras"},
			{"label": _("Secretaria de Saúde"), "value": "saude"},
			{"label": _("Secretaria de Educação"), "value": "educacao"},
			{"label": _("Secretaria de Serviços Urbanos"), "value": "servicos_urbanos"}
		]
	}

@frappe.whitelist(allow_guest=True)
def get_contrato_detalhes(contrato_id):
	"""Retorna detalhes completos de um contrato específico."""
	# Em um ambiente real, buscaria no banco de dados
	return {
		"id": contrato_id,
		"detalhes_completos": "Dados detalhados do contrato...",
		"historico_pagamentos": [],
		"aditivos": [],
		"documentos": []
	}
