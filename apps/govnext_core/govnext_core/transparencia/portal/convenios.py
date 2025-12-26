# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate, add_months
import json

def get_context(context):
	"""
	Prepara o contexto para a página de convênios do Portal da Transparência.
	"""
	context.title = _("Convênios e Transferências")
	context.subtitle = _("Exibe objetos de cooperação entre o município e as organizações da sociedade para execução de projetos visando o atendimento da população.")

	# Filtros de pesquisa
	context.filtros = get_filtros()

	# Dados de convênios
	context.convenios = get_convenios_data()

	# Estatísticas de convênios
	context.estatisticas_convenios = get_estatisticas_convenios()

	# Gráficos de convênios
	context.graficos = get_graficos_convenios()

	# Tipos de convênios
	context.tipos_convenios = get_tipos_convenios()

	# Convênios por área
	context.convenios_por_area = get_convenios_por_area()

	return context

def get_filtros():
	"""Retorna os filtros disponíveis para pesquisa de convênios."""
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
			{"label": _("Vigentes"), "value": "vigentes"},
			{"label": _("Assinados"), "value": "assinados"},
			{"label": _("Em execução"), "value": "execucao"},
			{"label": _("Concluídos"), "value": "concluidos"},
			{"label": _("Suspensos"), "value": "suspensos"},
			{"label": _("Rescindidos"), "value": "rescindidos"}
		],
		"tipo": [
			{"label": _("Todos os tipos"), "value": "todos"},
			{"label": _("Convênio de Repasse"), "value": "repasse"},
			{"label": _("Convênio de Cooperação"), "value": "cooperacao"},
			{"label": _("Termo de Parceria"), "value": "parceria"},
			{"label": _("Termo de Fomento"), "value": "fomento"},
			{"label": _("Termo de Colaboração"), "value": "colaboracao"},
			{"label": _("Contrato de Gestão"), "value": "gestao"}
		],
		"area": [
			{"label": _("Todas as áreas"), "value": "todas"},
			{"label": _("Educação"), "value": "educacao"},
			{"label": _("Saúde"), "value": "saude"},
			{"label": _("Assistência Social"), "value": "assistencia_social"},
			{"label": _("Cultura"), "value": "cultura"},
			{"label": _("Esporte"), "value": "esporte"},
			{"label": _("Meio Ambiente"), "value": "meio_ambiente"},
			{"label": _("Desenvolvimento Econômico"), "value": "desenvolvimento"}
		],
		"orgao": get_orgaos_list(),
		"ordenacao": [
			{"label": _("Data (mais recente)"), "value": "data_desc"},
			{"label": _("Data (mais antiga)"), "value": "data_asc"},
			{"label": _("Valor (maior)"), "value": "valor_desc"},
			{"label": _("Valor (menor)"), "value": "valor_asc"},
			{"label": _("Convenente A-Z"), "value": "convenente_asc"},
			{"label": _("Situação"), "value": "situacao"}
		]
	}

def get_convenios_data():
	"""Retorna os dados de convênios para exibição."""
	# Em um ambiente real, estes dados viriam do banco de dados

	convenios_exemplo = [
		{
			"id": "2025/CONV-001",
			"numero": "001/2025",
			"data_assinatura": "2025-03-15",
			"data_inicio": "2025-04-01",
			"data_fim": "2026-03-31",
			"convenente": "Instituto de Desenvolvimento Social",
			"cnpj": "12.345.678/0001-90",
			"tipo": "Termo de Fomento",
			"objeto": "Desenvolvimento de ações socioeducativas para crianças e adolescentes em situação de vulnerabilidade social",
			"area": "Assistência Social",
			"situacao": "Em execução",
			"valor_total": 450000.00,
			"valor_repasse": 450000.00,
			"valor_contrapartida": 0.00,
			"valor_executado": 225000.00,
			"percentual_execucao": 50.0,
			"orgao_responsavel": "Secretaria de Assistência Social",
			"gestor_convenio": "Maria Silva Santos",
			"meta_beneficiarios": 200,
			"beneficiarios_atendidos": 180,
			"prestacao_contas": "Em dia"
		},
		{
			"id": "2025/CONV-002",
			"numero": "002/2025",
			"data_assinatura": "2025-02-20",
			"data_inicio": "2025-03-01",
			"data_fim": "2025-12-31",
			"convenente": "Associação Cultural Arte & Vida",
			"cnpj": "98.765.432/0001-10",
			"tipo": "Termo de Colaboração",
			"objeto": "Realização de oficinas culturais e artísticas para jovens da periferia",
			"area": "Cultura",
			"situacao": "Em execução",
			"valor_total": 180000.00,
			"valor_repasse": 150000.00,
			"valor_contrapartida": 30000.00,
			"valor_executado": 120000.00,
			"percentual_execucao": 66.7,
			"orgao_responsavel": "Secretaria de Cultura",
			"gestor_convenio": "João Carlos Oliveira",
			"meta_beneficiarios": 300,
			"beneficiarios_atendidos": 285,
			"prestacao_contas": "Em dia"
		},
		{
			"id": "2025/CONV-003",
			"numero": "003/2025",
			"data_assinatura": "2025-01-10",
			"data_inicio": "2025-01-15",
			"data_fim": "2025-12-15",
			"convenente": "Centro de Reabilitação Vida Nova",
			"cnpj": "11.222.333/0001-44",
			"tipo": "Convênio de Repasse",
			"objeto": "Prestação de serviços de reabilitação física e terapia ocupacional",
			"area": "Saúde",
			"situacao": "Em execução",
			"valor_total": 320000.00,
			"valor_repasse": 320000.00,
			"valor_contrapartida": 0.00,
			"valor_executado": 160000.00,
			"percentual_execucao": 50.0,
			"orgao_responsavel": "Secretaria de Saúde",
			"gestor_convenio": "Dra. Ana Paula Costa",
			"meta_beneficiarios": 150,
			"beneficiarios_atendidos": 140,
			"prestacao_contas": "Em dia"
		},
		{
			"id": "2024/CONV-089",
			"numero": "089/2024",
			"data_assinatura": "2024-08-15",
			"data_inicio": "2024-09-01",
			"data_fim": "2025-08-31",
			"convenente": "Fundação Educacional Esperança",
			"cnpj": "33.444.555/0001-66",
			"tipo": "Termo de Parceria",
			"objeto": "Programa de educação complementar e reforço escolar",
			"area": "Educação",
			"situacao": "Concluído",
			"valor_total": 280000.00,
			"valor_repasse": 250000.00,
			"valor_contrapartida": 30000.00,
			"valor_executado": 280000.00,
			"percentual_execucao": 100.0,
			"orgao_responsavel": "Secretaria de Educação",
			"gestor_convenio": "Prof. Roberto Lima",
			"meta_beneficiarios": 500,
			"beneficiarios_atendidos": 520,
			"prestacao_contas": "Aprovada"
		}
	]

	# Formatar valores para exibição
	for convenio in convenios_exemplo:
		convenio["valor_total_formatado"] = fmt_money(convenio["valor_total"], currency="BRL")
		convenio["valor_repasse_formatado"] = fmt_money(convenio["valor_repasse"], currency="BRL")
		convenio["valor_contrapartida_formatado"] = fmt_money(convenio["valor_contrapartida"], currency="BRL")
		convenio["valor_executado_formatado"] = fmt_money(convenio["valor_executado"], currency="BRL")
		convenio["data_assinatura_formatada"] = frappe.utils.formatdate(convenio["data_assinatura"], "dd/MM/yyyy")
		convenio["data_inicio_formatada"] = frappe.utils.formatdate(convenio["data_inicio"], "dd/MM/yyyy")
		convenio["data_fim_formatada"] = frappe.utils.formatdate(convenio["data_fim"], "dd/MM/yyyy")

	return convenios_exemplo

def get_estatisticas_convenios():
	"""Retorna estatísticas resumidas dos convênios."""
	return {
		"total_convenios": 45,
		"convenios_vigentes": 28,
		"convenios_concluidos": 15,
		"convenios_suspensos": 2,
		"valor_total_convenios": fmt_money(5600000, currency="BRL"),
		"valor_repasses": fmt_money(4950000, currency="BRL"),
		"valor_contrapartidas": fmt_money(650000, currency="BRL"),
		"valor_executado": fmt_money(3750000, currency="BRL"),
		"percentual_execucao_media": 73.2,
		"beneficiarios_total": 8500,
		"organizacoes_parceiras": 32,
		"prestacao_contas_aprovadas": 42,
		"prestacao_contas_pendentes": 3
	}

def get_graficos_convenios():
	"""Retorna dados para gráficos de convênios."""
	return {
		"evolucao_mensal": {
			"labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
			"convenios_assinados": [3, 5, 4, 6, 3, 2],
			"valor_repasses": [580000, 920000, 750000, 1150000, 480000, 320000],
			"beneficiarios": [450, 720, 650, 980, 380, 280]
		},
		"por_area": {
			"labels": ["Assistência Social", "Educação", "Saúde", "Cultura", "Esporte", "Meio Ambiente"],
			"quantidade": [12, 10, 8, 7, 5, 3],
			"valor_total": [1680000, 1400000, 1120000, 840000, 420000, 140000],
			"cores": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1", "#fd7e14"]
		},
		"por_tipo": {
			"labels": ["Termo de Fomento", "Convênio de Repasse", "Termo de Colaboração", "Termo de Parceria", "Contrato de Gestão"],
			"quantidade": [15, 12, 8, 7, 3],
			"valor_medio": [280000, 350000, 180000, 220000, 450000]
		},
		"situacao_convenios": {
			"labels": ["Vigentes", "Concluídos", "Suspensos", "Rescindidos"],
			"quantidade": [28, 15, 2, 0],
			"cores": ["#28a745", "#007bff", "#ffc107", "#dc3545"]
		},
		"execucao_financeira": {
			"labels": ["0-25%", "26-50%", "51-75%", "76-99%", "100%"],
			"quantidade": [3, 8, 12, 7, 15],
			"valor_total": [180000, 1120000, 1680000, 980000, 1640000]
		}
	}

def get_tipos_convenios():
	"""Retorna informações sobre os tipos de convênios."""
	return [
		{
			"tipo": "Termo de Fomento",
			"quantidade": 15,
			"valor_total": 4200000,
			"percentual": 33.3,
			"execucao_media": 75.5,
			"descricao": "Instrumento para transferência de recursos para organizações da sociedade civil"
		},
		{
			"tipo": "Convênio de Repasse",
			"quantidade": 12,
			"valor_total": 4200000,
			"percentual": 26.7,
			"execucao_media": 68.2,
			"descricao": "Acordo para repasse de recursos para execução de ações de interesse público"
		},
		{
			"tipo": "Termo de Colaboração",
			"quantidade": 8,
			"valor_total": 1440000,
			"percentual": 17.8,
			"execucao_media": 82.1,
			"descricao": "Parceria para desenvolvimento de atividades de interesse público"
		},
		{
			"tipo": "Termo de Parceria",
			"quantidade": 7,
			"valor_total": 1540000,
			"percentual": 15.6,
			"execucao_media": 79.3,
			"descricao": "Acordo de cooperação com organizações para projetos específicos"
		},
		{
			"tipo": "Contrato de Gestão",
			"quantidade": 3,
			"valor_total": 1350000,
			"percentual": 6.7,
			"execucao_media": 85.7,
			"descricao": "Instrumento para gestão de serviços públicos por organizações sociais"
		}
	]

def get_convenios_por_area():
	"""Retorna convênios agrupados por área de atuação."""
	return [
		{
			"area": "Assistência Social",
			"quantidade": 12,
			"valor_total": 1680000,
			"beneficiarios": 2400,
			"organizacoes": 8,
			"principais_objetos": [
				"Atendimento a crianças e adolescentes",
				"Apoio a famílias vulneráveis",
				"Programas de geração de renda"
			]
		},
		{
			"area": "Educação",
			"quantidade": 10,
			"valor_total": 1400000,
			"beneficiarios": 2800,
			"organizacoes": 6,
			"principais_objetos": [
				"Educação complementar",
				"Reforço escolar",
				"Formação profissionalizante"
			]
		},
		{
			"area": "Saúde",
			"quantidade": 8,
			"valor_total": 1120000,
			"beneficiarios": 1500,
			"organizacoes": 5,
			"principais_objetos": [
				"Reabilitação física",
				"Apoio psicossocial",
				"Prevenção e promoção da saúde"
			]
		},
		{
			"area": "Cultura",
			"quantidade": 7,
			"valor_total": 840000,
			"beneficiarios": 1200,
			"organizacoes": 7,
			"principais_objetos": [
				"Oficinas culturais",
				"Eventos artísticos",
				"Preservação do patrimônio cultural"
			]
		},
		{
			"area": "Esporte",
			"quantidade": 5,
			"valor_total": 420000,
			"beneficiarios": 800,
			"organizacoes": 4,
			"principais_objetos": [
				"Escolinhas esportivas",
				"Competições e torneios",
				"Esporte adaptado"
			]
		},
		{
			"area": "Meio Ambiente",
			"quantidade": 3,
			"valor_total": 140000,
			"beneficiarios": 500,
			"organizacoes": 2,
			"principais_objetos": [
				"Educação ambiental",
				"Preservação de áreas verdes",
				"Coleta seletiva"
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
			{"label": _("Secretaria de Assistência Social"), "value": "assistencia"},
			{"label": _("Secretaria de Educação"), "value": "educacao"},
			{"label": _("Secretaria de Saúde"), "value": "saude"},
			{"label": _("Secretaria de Cultura"), "value": "cultura"},
			{"label": _("Secretaria de Esporte"), "value": "esporte"}
		]

@frappe.whitelist(allow_guest=True)
def get_convenios_ajax(filtros=None):
	"""Endpoint AJAX para buscar convênios com filtros."""
	if filtros:
		filtros = json.loads(filtros)

	# Aplicar filtros e retornar dados
	convenios = get_convenios_data()

	return {
		"success": True,
		"data": convenios,
		"total": len(convenios),
		"total_valor": sum([c["valor_total"] for c in convenios])
	}

@frappe.whitelist(allow_guest=True)
def get_convenio_detalhes(convenio_id):
	"""Endpoint para buscar detalhes de um convênio específico."""
	# Em um ambiente real, buscaria dados do banco
	convenios = get_convenios_data()
	convenio = next((c for c in convenios if c["id"] == convenio_id), None)

	if convenio:
		# Adicionar informações detalhadas
		convenio["cronograma_execucao"] = [
			{"etapa": "Planejamento", "prazo": "30 dias", "status": "Concluída"},
			{"etapa": "Mobilização", "prazo": "60 dias", "status": "Em andamento"},
			{"etapa": "Execução", "prazo": "300 dias", "status": "Planejada"},
			{"etapa": "Avaliação", "prazo": "30 dias", "status": "Planejada"}
		]
		
		convenio["prestacoes_contas"] = [
			{"periodo": "Jan-Mar/2025", "status": "Aprovada", "data_entrega": "2025-04-10"},
			{"periodo": "Abr-Jun/2025", "status": "Em análise", "data_entrega": "2025-07-08"},
			{"periodo": "Jul-Set/2025", "status": "Pendente", "data_previsao": "2025-10-10"}
		]

		return {
			"success": True,
			"data": convenio
		}
	else:
		return {
			"success": False,
			"error": "Convênio não encontrado"
		}

@frappe.whitelist(allow_guest=True)
def exportar_convenios(formato="csv", filtros=None):
	"""Exporta dados de convênios em diferentes formatos."""
	if filtros:
		filtros = json.loads(filtros)

	convenios = get_convenios_data()

	if formato == "csv":
		return gerar_csv_convenios(convenios)
	elif formato == "xlsx":
		return gerar_xlsx_convenios(convenios)
	elif formato == "pdf":
		return gerar_pdf_convenios(convenios)

	return {"error": "Formato não suportado"}

def gerar_csv_convenios(convenios):
	"""Gera arquivo CSV com dados de convênios."""
	import csv
	import io

	output = io.StringIO()
	writer = csv.writer(output)

	# Cabeçalho
	writer.writerow([
		"Número", "Data Assinatura", "Convenente", "CNPJ", "Tipo", "Objeto",
		"Área", "Situação", "Valor Total", "Valor Repasse", "Valor Executado",
		"% Execução", "Órgão Responsável", "Beneficiários"
	])

	# Dados
	for convenio in convenios:
		writer.writerow([
			convenio["numero"],
			convenio["data_assinatura_formatada"],
			convenio["convenente"],
			convenio["cnpj"],
			convenio["tipo"],
			convenio["objeto"],
			convenio["area"],
			convenio["situacao"],
			convenio["valor_total_formatado"],
			convenio["valor_repasse_formatado"],
			convenio["valor_executado_formatado"],
			f"{convenio['percentual_execucao']}%",
			convenio["orgao_responsavel"],
			convenio["beneficiarios_atendidos"]
		])

	return {
		"content": output.getvalue(),
		"filename": f"convenios_{frappe.utils.today()}.csv",
		"type": "text/csv"
	}