# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months, nowdate
import json
import datetime

def get_context(context):
	"""
	Prepara o contexto para o Dashboard Executivo do Portal da Transparência.
	"""
	context.title = _("Dashboard Executivo")
	context.subtitle = _("Visão consolidada dos principais indicadores de transparência e gestão pública municipal.")

	# KPIs principais
	context.kpis_principais = get_kpis_principais()

	# Indicadores de transparência
	context.indicadores_transparencia = get_indicadores_transparencia()

	# Dados para gráficos
	context.graficos_dados = get_dados_graficos_dashboard()

	# Alertas e notificações
	context.alertas = get_alertas_sistema()

	# Últimas atualizações
	context.ultimas_atualizacoes = get_ultimas_atualizacoes()

	# Ranking de transparência
	context.ranking_transparencia = get_ranking_transparencia()

	# Metas e indicadores de desempenho
	context.metas_desempenho = get_metas_desempenho()

	return context

def get_kpis_principais():
	"""Retorna os KPIs principais do dashboard."""
	return {
		"financeiro": {
			"orcamento_total": {
				"valor": 24000000,
				"formatado": fmt_money(24000000, currency="BRL"),
				"variacao": 8.5,
				"tendencia": "alta",
				"icone": "fa-chart-line",
				"cor": "success"
			},
			"receitas_arrecadadas": {
				"valor": 18450000,
				"formatado": fmt_money(18450000, currency="BRL"),
				"variacao": 12.3,
				"tendencia": "alta",
				"percentual_meta": 76.9,
				"icone": "fa-money-bill-wave",
				"cor": "primary"
			},
			"despesas_executadas": {
				"valor": 15600000,
				"formatado": fmt_money(15600000, currency="BRL"),
				"variacao": -3.2,
				"tendencia": "baixa",
				"percentual_orcamento": 66.4,
				"icone": "fa-hand-holding-usd",
				"cor": "warning"
			},
			"resultado_orcamentario": {
				"valor": 2850000,
				"formatado": fmt_money(2850000, currency="BRL"),
				"tipo": "Superávit",
				"variacao": 45.2,
				"tendencia": "alta",
				"icone": "fa-balance-scale",
				"cor": "success"
			}
		},
		"operacional": {
			"contratos_ativos": {
				"valor": 156,
				"variacao": 5.4,
				"tendencia": "alta",
				"icone": "fa-file-contract",
				"cor": "info"
			},
			"licitacoes_andamento": {
				"valor": 23,
				"variacao": -12.3,
				"tendencia": "baixa",
				"icone": "fa-gavel",
				"cor": "warning"
			},
			"obras_execucao": {
				"valor": 12,
				"variacao": 9.1,
				"tendencia": "alta",
				"icone": "fa-tools",
				"cor": "primary"
			},
			"servidores_ativos": {
				"valor": 1250,
				"variacao": 2.1,
				"tendencia": "alta",
				"icone": "fa-users",
				"cor": "secondary"
			}
		},
		"transparencia": {
			"indice_transparencia": {
				"valor": 8.7,
				"maximo": 10,
				"variacao": 0.3,
				"tendencia": "alta",
				"classificacao": "Excelente",
				"icone": "fa-eye",
				"cor": "success"
			},
			"acessos_portal": {
				"valor": 15420,
				"periodo": "último mês",
				"variacao": 18.5,
				"tendencia": "alta",
				"icone": "fa-chart-bar",
				"cor": "info"
			},
			"downloads_dados": {
				"valor": 2340,
				"periodo": "último mês",
				"variacao": 25.8,
				"tendencia": "alta",
				"icone": "fa-download",
				"cor": "primary"
			},
			"consultas_cidadao": {
				"valor": 485,
				"periodo": "último mês",
				"variacao": 12.7,
				"tendencia": "alta",
				"icone": "fa-question-circle",
				"cor": "secondary"
			}
		}
	}

def get_indicadores_transparencia():
	"""Retorna indicadores específicos de transparência."""
	return {
		"indice_geral": {
			"pontuacao": 8.7,
			"maximo": 10.0,
			"classificacao": "Excelente",
			"posicao_ranking": 15,
			"total_municipios": 645,
			"percentil": 97.7
		},
		"dimensoes": [
			{
				"nome": "Dados Abertos",
				"pontuacao": 9.2,
				"peso": 25,
				"status": "Excelente",
				"melhorias": []
			},
			{
				"nome": "Prestação de Contas",
				"pontuacao": 8.8,
				"peso": 30,
				"status": "Excelente",
				"melhorias": []
			},
			{
				"nome": "Participação Social",
				"pontuacao": 7.5,
				"peso": 20,
				"status": "Bom",
				"melhorias": ["Ampliar canais de participação", "Criar ouvidoria online"]
			},
			{
				"nome": "Acessibilidade",
				"pontuacao": 8.9,
				"peso": 15,
				"status": "Excelente",
				"melhorias": []
			},
			{
				"nome": "Atualização de Dados",
				"pontuacao": 9.4,
				"peso": 10,
				"status": "Excelente",
				"melhorias": []
			}
		],
		"evolucao_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"pontuacoes": [8.1, 8.3, 8.4, 8.5, 8.6, 8.7],
			"meta": [8.5, 8.5, 8.5, 8.5, 8.5, 8.5]
		}
	}

def get_dados_graficos_dashboard():
	"""Retorna dados estruturados para todos os gráficos do dashboard."""
	return {
		"execucao_orcamentaria": {
			"type": "line",
			"title": "Execução Orçamentária Mensal (R$ milhões)",
			"data": {
				"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
				"datasets": [
					{
						"label": "Receitas",
						"data": [2.8, 2.95, 2.75, 3.1, 3.2, 3.65],
						"borderColor": "#28a745",
						"backgroundColor": "rgba(40, 167, 69, 0.1)",
						"tension": 0.4
					},
					{
						"label": "Despesas",
						"data": [2.65, 2.88, 2.58, 2.89, 2.45, 2.15],
						"borderColor": "#dc3545",
						"backgroundColor": "rgba(220, 53, 69, 0.1)",
						"tension": 0.4
					},
					{
						"label": "Meta Receitas",
						"data": [4.0, 4.0, 4.0, 4.0, 4.0, 4.0],
						"borderColor": "#6c757d",
						"borderDash": [5, 5],
						"fill": false
					}
				]
			},
			"options": {
				"responsive": True,
				"scales": {
					"y": {
						"beginAtZero": True,
						"title": {"display": True, "text": "Valores (R$ milhões)"}
					}
				}
			}
		},
		"distribuicao_despesas": {
			"type": "doughnut",
			"title": "Distribuição de Despesas por Categoria",
			"data": {
				"labels": ["Pessoal", "Custeio", "Investimentos", "Inversões", "Amortização"],
				"datasets": [{
					"data": [10.2, 4.2, 1.2, 0, 0],
					"backgroundColor": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"],
					"borderWidth": 2
				}]
			},
			"options": {
				"responsive": True,
				"plugins": {
					"legend": {"position": "bottom"},
					"tooltip": {
						"callbacks": {
							"label": "function(context) { return context.label + ': R$ ' + context.parsed + 'M'; }"
						}
					}
				}
			}
		},
		"receitas_por_fonte": {
			"type": "bar",
			"title": "Receitas por Fonte (R$ milhões)",
			"data": {
				"labels": ["IPTU", "ISS", "FPM", "ICMS", "FUNDEB", "SUS"],
				"datasets": [{
					"label": "Arrecadado",
					"data": [1.85, 1.25, 5.85, 3.8, 3.3, 2.4],
					"backgroundColor": "#007bff"
				}, {
					"label": "Orçado",
					"data": [2.5, 1.8, 6.2, 4.2, 3.6, 2.8],
					"backgroundColor": "#6c757d"
				}]
			},
			"options": {
				"responsive": True,
				"scales": {
					"y": {
						"beginAtZero": True,
						"title": {"display": True, "text": "Valores (R$ milhões)"}
					}
				}
			}
		},
		"obras_por_situacao": {
			"type": "pie",
			"title": "Situação das Obras Públicas",
			"data": {
				"labels": ["Em Execução", "Concluídas", "Licitação", "Paralisadas"],
				"datasets": [{
					"data": [12, 28, 8, 2],
					"backgroundColor": ["#007bff", "#28a745", "#ffc107", "#dc3545"]
				}]
			},
			"options": {
				"responsive": True,
				"plugins": {"legend": {"position": "bottom"}}
			}
		},
		"contratos_por_modalidade": {
			"type": "horizontalBar",
			"title": "Contratos por Modalidade de Licitação",
			"data": {
				"labels": ["Pregão Eletrônico", "Concorrência", "Tomada de Preços", "Dispensa", "Inexigibilidade"],
				"datasets": [{
					"label": "Quantidade",
					"data": [45, 25, 18, 32, 8],
					"backgroundColor": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"]
				}]
			},
			"options": {
				"responsive": True,
				"scales": {
					"x": {
						"beginAtZero": True,
						"title": {"display": True, "text": "Quantidade de Contratos"}
					}
				}
			}
		},
		"indicadores_transparencia": {
			"type": "radar",
			"title": "Indicadores de Transparência",
			"data": {
				"labels": ["Dados Abertos", "Prestação Contas", "Participação Social", "Acessibilidade", "Atualização"],
				"datasets": [{
					"label": "Atual",
					"data": [9.2, 8.8, 7.5, 8.9, 9.4],
					"borderColor": "#007bff",
					"backgroundColor": "rgba(0, 123, 255, 0.2)"
				}, {
					"label": "Meta",
					"data": [9.0, 9.0, 8.5, 9.0, 9.5],
					"borderColor": "#28a745",
					"backgroundColor": "rgba(40, 167, 69, 0.1)"
				}]
			},
			"options": {
				"responsive": True,
				"scales": {
					"r": {
						"beginAtZero": True,
						"max": 10,
						"ticks": {"stepSize": 2}
					}
				}
			}
		},
		"evolucao_acessos": {
			"type": "line",
			"title": "Evolução de Acessos ao Portal",
			"data": {
				"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
				"datasets": [{
					"label": "Acessos Únicos",
					"data": [12500, 13200, 14100, 13800, 15400, 15420],
					"borderColor": "#007bff",
					"backgroundColor": "rgba(0, 123, 255, 0.1)",
					"tension": 0.4
				}, {
					"label": "Downloads",
					"data": [1850, 2100, 2250, 2180, 2340, 2380],
					"borderColor": "#28a745",
					"backgroundColor": "rgba(40, 167, 69, 0.1)",
					"tension": 0.4
				}]
			},
			"options": {
				"responsive": True,
				"scales": {
					"y": {
						"beginAtZero": True,
						"title": {"display": True, "text": "Quantidade"}
					}
				}
			}
		}
	}

def get_alertas_sistema():
	"""Retorna alertas e notificações do sistema."""
	return [
		{
			"tipo": "warning",
			"titulo": "Prazo de Publicação",
			"mensagem": "Relatório de Gestão Fiscal deve ser publicado até 30/07/2025",
			"prazo": "2025-07-30",
			"dias_restantes": 11,
			"prioridade": "alta",
			"acao": "Elaborar RGF 3º Bimestre"
		},
		{
			"tipo": "info",
			"titulo": "Atualização de Dados",
			"mensagem": "Novos dados de contratos disponíveis para publicação",
			"data": "2025-06-18",
			"prioridade": "media",
			"acao": "Publicar contratos junho"
		},
		{
			"tipo": "success",
			"titulo": "Meta Alcançada",
			"mensagem": "Índice de Transparência ultrapassou meta mensal (8.7/8.5)",
			"data": "2025-06-15",
			"prioridade": "baixa",
			"acao": "Manter nível"
		},
		{
			"tipo": "warning",
			"titulo": "Limite de Gastos",
			"mensagem": "Gastos com pessoal em 42.5% da RCL (limite: 54%)",
			"percentual": 42.5,
			"limite": 54.0,
			"prioridade": "media",
			"acao": "Monitorar evolução"
		}
	]

def get_ultimas_atualizacoes():
	"""Retorna as últimas atualizações do portal."""
	return [
		{
			"modulo": "Despesas",
			"acao": "Publicação",
			"descricao": "145 novos registros de despesas adicionados",
			"data": "2025-06-19 09:30",
			"usuario": "Sistema Automático",
			"icone": "fa-money-bill-alt"
		},
		{
			"modulo": "Contratos",
			"acao": "Atualização",
			"descricao": "Contrato 089/2025 atualizado - 75% executado",
			"data": "2025-06-18 16:45",
			"usuario": "Maria Silva",
			"icone": "fa-file-contract"
		},
		{
			"modulo": "Obras",
			"acao": "Nova Obra",
			"descricao": "Obra de pavimentação Rua das Flores iniciada",
			"data": "2025-06-18 14:20",
			"usuario": "João Santos",
			"icone": "fa-tools"
		},
		{
			"modulo": "Licitações",
			"acao": "Homologação",
			"descricao": "Pregão 003/2025 homologado - R$ 1.150.000",
			"data": "2025-06-17 11:15",
			"usuario": "Ana Paula",
			"icone": "fa-gavel"
		},
		{
			"modulo": "Receitas",
			"acao": "Arrecadação",
			"descricao": "FPM junho depositado - R$ 485.000",
			"data": "2025-06-17 08:00",
			"usuario": "Sistema Bancário",
			"icone": "fa-university"
		}
	]

def get_ranking_transparencia():
	"""Retorna dados do ranking de transparência."""
	return {
		"posicao_atual": 15,
		"total_municipios": 645,
		"percentil": 97.7,
		"evolucao": {
			"2024": 18,
			"2023": 22,
			"2022": 28,
			"2021": 35
		},
		"comparacao_regional": [
			{"municipio": "Nossa Cidade", "pontuacao": 8.7, "posicao": 1, "destaque": True},
			{"municipio": "Cidade Vizinha A", "pontuacao": 8.5, "posicao": 2},
			{"municipio": "Cidade Vizinha B", "pontuacao": 8.2, "posicao": 3},
			{"municipio": "Cidade Vizinha C", "pontuacao": 7.9, "posicao": 4},
			{"municipio": "Cidade Vizinha D", "pontuacao": 7.6, "posicao": 5}
		],
		"melhores_praticas": [
			"Publicação automática de dados",
			"Portal responsivo e acessível",
			"Dados em formatos abertos",
			"Atualização em tempo real",
			"Interface intuitiva"
		]
	}

def get_metas_desempenho():
	"""Retorna metas e indicadores de desempenho."""
	return {
		"financeiras": [
			{
				"meta": "Arrecadação Própria",
				"valor_meta": 7500000,
				"valor_atual": 6050000,
				"percentual": 80.7,
				"status": "Em andamento",
				"prazo": "2025-12-31"
			},
			{
				"meta": "Execução Orçamentária",
				"valor_meta": 85.0,
				"valor_atual": 83.6,
				"percentual": 98.4,
				"status": "Próximo da meta",
				"prazo": "2025-12-31"
			}
		],
		"transparencia": [
			{
				"meta": "Índice de Transparência",
				"valor_meta": 9.0,
				"valor_atual": 8.7,
				"percentual": 96.7,
				"status": "Próximo da meta",
				"prazo": "2025-12-31"
			},
			{
				"meta": "Tempo Resposta SIC",
				"valor_meta": 15,  # dias
				"valor_atual": 12,
				"percentual": 125.0,  # Menor é melhor
				"status": "Meta superada",
				"prazo": "Contínuo"
			}
		],
		"operacionais": [
			{
				"meta": "Obras Concluídas no Prazo",
				"valor_meta": 90.0,  # %
				"valor_atual": 85.7,
				"percentual": 95.2,
				"status": "Em andamento",
				"prazo": "2025-12-31"
			},
			{
				"meta": "Licitações Homologadas",
				"valor_meta": 45,
				"valor_atual": 42,
				"percentual": 93.3,
				"status": "Em andamento",
				"prazo": "2025-12-31"
			}
		]
	}

@frappe.whitelist(allow_guest=True)
def get_dashboard_data(periodo="atual"):
	"""API para carregar dados do dashboard dinamicamente."""
	return {
		"kpis": get_kpis_principais(),
		"graficos": get_dados_graficos_dashboard(),
		"indicadores": get_indicadores_transparencia(),
		"alertas": get_alertas_sistema(),
		"ranking": get_ranking_transparencia(),
		"ultima_atualizacao": nowdate()
	}

@frappe.whitelist(allow_guest=True)
def get_historico_kpi(kpi, periodo_dias=30):
	"""API para buscar histórico de um KPI específico."""
	# Em um ambiente real, buscaria dados históricos do banco
	dados_exemplo = {
		"receitas_arrecadadas": {
			"labels": ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
			"valores": [4200000, 4650000, 4900000, 5100000]
		},
		"despesas_executadas": {
			"labels": ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
			"valores": [3800000, 4100000, 3900000, 3800000]
		}
	}
	
	return dados_exemplo.get(kpi, {"labels": [], "valores": []})

@frappe.whitelist(allow_guest=True)
def atualizar_meta_desempenho(meta_id, novo_valor):
	"""API para atualizar metas de desempenho."""
	# Em um ambiente real, atualizaria no banco de dados
	return {
		"success": True,
		"message": f"Meta {meta_id} atualizada para {novo_valor}",
		"data": {
			"meta_id": meta_id,
			"valor_anterior": 85.0,
			"valor_novo": float(novo_valor),
			"data_atualizacao": nowdate()
		}
	}

@frappe.whitelist(allow_guest=True)
def exportar_dashboard(formato="pdf"):
	"""API para exportar dados do dashboard."""
	dados = get_dashboard_data()
	
	if formato == "pdf":
		return gerar_pdf_dashboard(dados)
	elif formato == "xlsx":
		return gerar_excel_dashboard(dados)
	elif formato == "json":
		return json.dumps(dados, indent=2, ensure_ascii=False, default=str)
	
	return {"error": "Formato não suportado"}

def gerar_pdf_dashboard(dados):
	"""Gera relatório PDF do dashboard."""
	# Em um ambiente real, usaria bibliotecas como ReportLab
	return {
		"success": True,
		"filename": f"dashboard_executivo_{nowdate()}.pdf",
		"url": f"/files/relatorios/dashboard_executivo_{nowdate()}.pdf"
	}

def gerar_excel_dashboard(dados):
	"""Gera relatório Excel do dashboard."""
	# Em um ambiente real, usaria bibliotecas como openpyxl
	return {
		"success": True,
		"filename": f"dashboard_executivo_{nowdate()}.xlsx",
		"url": f"/files/relatorios/dashboard_executivo_{nowdate()}.xlsx"
	}