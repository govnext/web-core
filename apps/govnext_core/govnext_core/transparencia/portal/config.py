# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_data():
	"""
	Retorna a configuração do Portal da Transparência.

	Esta função define as seções e os itens que serão exibidos no Portal da Transparência.
	Cada seção contém um conjunto de itens que representam as funcionalidades disponíveis.
	"""
	return [
		{
			"label": _("Transparência Financeira"),
			"icon": "fa fa-money-bill-alt",
			"items": [
				{
					"type": "doctype",
					"name": "Receita",
					"label": _("Receitas"),
					"description": _("Informações detalhadas sobre as fontes de arrecadação do município")
				},
				{
					"type": "doctype",
					"name": "Empenho",
					"label": _("Despesas"),
					"description": _("Demonstra os gastos da prefeitura, incluindo pagamentos realizados")
				},
				{
					"type": "doctype",
					"name": "Orcamento",
					"label": _("Orçamento"),
					"description": _("Informações detalhadas sobre a previsão de receitas e despesas")
				},
				{
					"type": "page",
					"name": "prestacao-contas",
					"label": _("Prestação de Contas"),
					"description": _("Relatórios detalhados sobre receitas, despesas e execução orçamentária")
				},
				{
					"type": "page",
					"name": "renuncias-receitas",
					"label": _("Renúncias de Receitas"),
					"description": _("Informações sobre isenções fiscais, anistias e incentivos concedidos")
				}
			]
		},
		{
			"label": _("Gestão de Pessoas"),
			"icon": "fa fa-users",
			"items": [
				{
					"type": "page",
					"name": "estrutura-remuneratoria",
					"label": _("Estrutura Remuneratória"),
					"description": _("Informações sobre os cargos e salários dos servidores")
				},
				{
					"type": "page",
					"name": "folha-pagamento",
					"label": _("Folha de Pagamento"),
					"description": _("Detalhes sobre os pagamentos realizados aos servidores")
				},
				{
					"type": "doctype",
					"name": "ServidorPublico",
					"label": _("Servidores"),
					"description": _("Lista de servidores públicos com informações detalhadas")
				},
				{
					"type": "page",
					"name": "diarias-passagens",
					"label": _("Diárias e Passagens"),
					"description": _("Informações sobre diárias concedidas e passagens emitidas")
				},
				{
					"type": "page",
					"name": "concursos",
					"label": _("Concursos Públicos"),
					"description": _("Informações sobre os processos seletivos realizados pelo município")
				}
			]
		},
		{
			"label": _("Contratos e Licitações"),
			"icon": "fa fa-file-contract",
			"items": [
				{
					"type": "doctype",
					"name": "ProcessoLicitatorio",
					"label": _("Licitações"),
					"description": _("Procedimentos licitatórios realizados pela prefeitura")
				},
				{
					"type": "doctype",
					"name": "ContratoPublico",
					"label": _("Contratos"),
					"description": _("Informações sobre contratos firmados pela prefeitura")
				},
				{
					"type": "page",
					"name": "ordem-cronologica",
					"label": _("Ordem Cronológica"),
					"description": _("Ordem cronológica dos pagamentos realizados pela prefeitura")
				},
				{
					"type": "page",
					"name": "empresas-sancionadas",
					"label": _("Empresas Sancionadas"),
					"description": _("Empresas penalizadas por irregularidades em contratos ou licitações")
				},
				{
					"type": "page",
					"name": "fiscais-contrato",
					"label": _("Fiscais de Contrato"),
					"description": _("Servidores responsáveis por acompanhar o cumprimento dos contratos")
				}
			]
		},
		{
			"label": _("Convênios e Transferências"),
			"icon": "fa fa-handshake",
			"items": [
				{
					"type": "page",
					"name": "convenios-sem-repasse",
					"label": _("Convênios sem Repasse"),
					"description": _("Cooperação entre o município e outros órgãos sem repasse financeiro")
				},
				{
					"type": "page",
					"name": "transferencias-recebidas",
					"label": _("Transferências Recebidas"),
					"description": _("Recursos financeiros transferidos ao município por outros entes")
				},
				{
					"type": "page",
					"name": "bolsa-familia",
					"label": _("Bolsa Família"),
					"description": _("Informações sobre a execução do programa no município")
				},
				{
					"type": "page",
					"name": "emendas-parlamentares",
					"label": _("Emendas Parlamentares"),
					"description": _("Recursos provenientes de emendas parlamentares destinados ao município")
				}
			]
		},
		{
			"label": _("Obras Públicas"),
			"icon": "fa fa-hard-hat",
			"items": [
				{
					"type": "doctype",
					"name": "ObraPublica",
					"label": _("Obras"),
					"description": _("Informações sobre obras públicas e serviços de engenharia")
				},
				{
					"type": "page",
					"name": "obras-andamento",
					"label": _("Obras em Andamento"),
					"description": _("Lista de obras públicas em execução")
				},
				{
					"type": "page",
					"name": "obras-concluidas",
					"label": _("Obras Concluídas"),
					"description": _("Lista de obras públicas concluídas")
				}
			]
		},
		{
			"label": _("Serviços ao Cidadão"),
			"icon": "fa fa-user",
			"items": [
				{
					"type": "page",
					"name": "carta-servicos",
					"label": _("Carta de Serviços"),
					"description": _("Serviços oferecidos pelo município aos cidadãos")
				},
				{
					"type": "page",
					"name": "ouvidoria",
					"label": _("Ouvidoria"),
					"description": _("Canal de comunicação entre cidadão e governo")
				},
				{
					"type": "page",
					"name": "sic",
					"label": _("Serviço de Informação ao Cidadão"),
					"description": _("Solicitação de acesso à informação para órgãos e entidades")
				},
				{
					"type": "page",
					"name": "perguntas-frequentes",
					"label": _("Perguntas Frequentes"),
					"description": _("Perguntas e respostas relacionadas às atividades da prefeitura")
				},
				{
					"type": "page",
					"name": "pesquisa-satisfacao",
					"label": _("Pesquisa de Satisfação"),
					"description": _("Relatório de satisfação da população com o Portal da Transparência")
				}
			]
		},
		{
			"label": _("Planejamento"),
			"icon": "fa fa-chart-line",
			"items": [
				{
					"type": "page",
					"name": "metas-fiscais",
					"label": _("Metas Fiscais"),
					"description": _("Números previstos e realizados pela prefeitura")
				},
				{
					"type": "page",
					"name": "plano-metas",
					"label": _("Plano de Metas"),
					"description": _("Metas e objetivos estabelecidos pela prefeitura")
				}
			]
		},
		{
			"label": _("Institucional"),
			"icon": "fa fa-building",
			"items": [
				{
					"type": "doctype",
					"name": "OrgaoPublico",
					"label": _("Estrutura Organizacional"),
					"description": _("Estrutura organizacional da prefeitura")
				},
				{
					"type": "page",
					"name": "legislacao",
					"label": _("Legislação"),
					"description": _("Leis, decretos, portarias e resoluções")
				},
				{
					"type": "page",
					"name": "relatorio-atividades",
					"label": _("Relatório de Atividades"),
					"description": _("Atividades desenvolvidas pelas secretarias do município")
				}
			]
		}
	]
