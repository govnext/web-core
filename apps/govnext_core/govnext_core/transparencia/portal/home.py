# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_context(context):
	"""
	Prepara o contexto para a página inicial do Portal da Transparência.

	Esta função carrega os dados necessários para exibir na página inicial,
	como serviços mais buscados, estatísticas e informações recentes.
	"""
	context.title = _("Portal da Transparência")
	context.subtitle = _("Fiscalize, questione e participe. Entenda como seu dinheiro está sendo usado. Transparência é confiança.")

	# Carrega os serviços mais buscados
	context.servicos_populares = get_servicos_populares()

	# Carrega mais serviços
	context.mais_servicos = get_mais_servicos()

	# Carrega estatísticas recentes
	context.estatisticas = get_estatisticas()

	# Carrega planejamentos
	context.planejamentos = get_planejamentos()

	# Carrega "Você também pode estar procurando"
	context.voce_pode_procurar = get_voce_pode_procurar()

	# Carrega "Mais do Portal da Transparência"
	context.mais_portal = get_mais_portal()

	# Carrega atualizações recentes
	context.atualizacoes_recentes = get_atualizacoes_recentes()

	# Carrega todos os serviços disponíveis
	context.todos_servicos = get_todos_servicos()

	# Carrega informações institucionais
	context.info_institucional = get_info_institucional()

	return context

def get_servicos_populares():
	"""Retorna os serviços mais buscados no portal."""
	return [
		{
			"titulo": _("Gestão de Pessoas"),
			"descricao": _("Consulte informações consolidadas sobre servidores, estrutura remuneratória, folha de pagamento, dentre outros."),
			"icone": "fa fa-users",
			"link": "/transparencia/gestao-pessoas"
		},
		{
			"titulo": _("Despesas"),
			"descricao": _("Demonstra os gastos da prefeitura, incluindo pagamentos realizados, destinatários, valores e descrição da despesa."),
			"icone": "fa fa-money-bill-alt",
			"link": "/transparencia/despesas"
		},
		{
			"titulo": _("Contratos"),
			"descricao": _("Acesse informações sobre todos os contratos firmados pela prefeitura, incluindo valores, fornecedores, vigências e objetos contratados."),
			"icone": "fa fa-file-contract",
			"link": "/transparencia/contratos"
		}
	]

def get_mais_servicos():
	"""Retorna os serviços da seção 'Mais serviços'."""
	return [
		{
			"titulo": _("Convênios sem Repasse"),
			"descricao": _("Exibe os objetos de cooperação entre o município e outros órgãos públicos que não envolvem repasse financeiro."),
			"link": "/transparencia/convenios-sem-repasse"
		},
		{
			"titulo": _("Receitas"),
			"descricao": _("Oferece informações detalhadas sobre as fontes de arrecadação do município, como impostos, transferências governamentais e outras receitas."),
			"link": "/transparencia/receitas"
		},
		{
			"titulo": _("Ordem Cronológica"),
			"descricao": _("Visualize a Ordem Cronológica dos Pagamentos realizados pela Prefeitura"),
			"link": "/transparencia/ordem-cronologica"
		},
		{
			"titulo": _("Convênios e Transferências"),
			"descricao": _("Exibe objetos de cooperação entre o município e as organizações da sociedade para execução de projetos visando o atendimento da população."),
			"link": "/transparencia/convenios-transferencias"
		},
		{
			"titulo": _("Concurso"),
			"descricao": _("Encontre informações sobre os processos seletivos realizados pelo município tais como editais e convocações."),
			"link": "/transparencia/concursos"
		},
		{
			"titulo": _("Diárias"),
			"descricao": _("Encontre informações de diárias concedidas a servidores da prefeitura incluindo nome do beneficiário, destino, motivo da viagem e valor concedido."),
			"link": "/transparencia/diarias"
		},
		{
			"titulo": _("Compras e Licitações"),
			"descricao": _("Acesse os procedimentos licitatórios realizados pela Prefeitura Municipal, os processos em andamento e as justificativas de contratações."),
			"link": "/transparencia/compras-licitacoes"
		},
		{
			"titulo": _("Adesão e Registro de Preço"),
			"descricao": _("Encontre informações sobre licitações realizadas por meio de registro de preços e as adesões a atas de outros órgãos públicos."),
			"link": "/transparencia/adesao-registro-preco"
		},
		{
			"titulo": _("Obras Públicas"),
			"descricao": _("Acesse as informações sobre obras públicas e serviços de engenharia do Município"),
			"link": "/transparencia/obras-publicas"
		},
		{
			"titulo": _("Prestação de Contas"),
			"descricao": _("Oferece relatórios detalhados sobre receitas, despesas e execução orçamentária permitindo acompanhar a gestão dos recursos públicos."),
			"link": "/transparencia/prestacao-contas"
		},
		{
			"titulo": _("Orçamento"),
			"descricao": _("Disponibiliza informações detalhadas sobre a previsão de receitas e despesas, esclarecendo como os recursos são planejados."),
			"link": "/transparencia/orcamento"
		},
		{
			"titulo": _("Renúncias de Receitas"),
			"descricao": _("Demonstra informações sobre valores de renúncia que a prefeitura ofereceu, como isenções fiscais, anistias, e incentivos concedidos a contribuintes."),
			"link": "/transparencia/renuncias-receitas"
		}
	]

def get_planejamentos():
	"""Retorna os itens da seção de planejamentos."""
	return [
		{
			"titulo": _("Metas Fiscais"),
			"descricao": _("Exibe números previstos e realizados pela prefeitura, incluindo receitas, despesas e gastos com pessoal."),
			"link": "/transparencia/metas-fiscais"
		},
		{
			"titulo": _("Plano de Metas"),
			"descricao": _("Encontre informações sobre as metas e objetivos estabelecidos pela prefeitura para o desenvolvimento do município."),
			"link": "/transparencia/plano-metas"
		}
	]

def get_voce_pode_procurar():
	"""Retorna os itens da seção 'Você também pode estar procurando'."""
	return [
		{
			"titulo": _("Serviço de Informação"),
			"descricao": _("O SIC (Serviço de Informação ao Cidadão) permite que pessoas, física ou jurídica, realize pedidos de acesso à informação para órgãos e entidades."),
			"link": "/transparencia/sic"
		},
		{
			"titulo": _("Ouvidoria"),
			"descricao": _("Canal direto de comunicação entre cidadão e governo, permitindo o registro de reclamações, sugestões e elogios, visando melhorar os serviços públicos."),
			"link": "/transparencia/ouvidoria"
		},
		{
			"titulo": _("Saúde"),
			"descricao": _("Explore os serviços e medicamentos disponibilizados para os cidadãos por meio do SUS."),
			"link": "/transparencia/saude"
		},
		{
			"titulo": _("Legislação"),
			"descricao": _("Acesse a legislação que rege a administração municipal, incluindo leis, decretos, portarias e resoluções."),
			"link": "/transparencia/legislacao"
		},
		{
			"titulo": _("Perguntas Frequentes"),
			"descricao": _("Acesse as perguntas e respostas relacionadas às atividades e aos serviços prestados pela Prefeitura Municipal."),
			"link": "/transparencia/perguntas-frequentes"
		},
		{
			"titulo": _("Radar da Transparência"),
			"descricao": _("Tenha acesso aos dados consolidados relativos à transparência pública (por Estados, Municípios, Poderes, órgãos etc)."),
			"link": "/transparencia/radar-transparencia"
		}
	]

def get_mais_portal():
	"""Retorna os itens da seção 'Mais do Portal da Transparência'."""
	return [
		{
			"titulo": _("Órgão Oficial"),
			"descricao": _("Tenha acesso às publicações oficiais da prefeitura, incluindo decretos, portarias, editais, contratos, e outras comunicações legais."),
			"link": "/transparencia/orgao-oficial"
		},
		{
			"titulo": _("Assistência Social"),
			"descricao": _("Acesse informações sobre os programas e ações de apoio à população desenvolvidos pela prefeitura."),
			"link": "/transparencia/assistencia-social"
		},
		{
			"titulo": _("Covid-19"),
			"descricao": _("Encontre informações detalhadas sobre as ações da prefeitura no combate à pandemia de Covid-19, incluindo casos registrados, vacinação e gastos."),
			"link": "/transparencia/covid-19"
		},
		{
			"titulo": _("Ajuda"),
			"descricao": _("Saiba os principais conceitos utilizados no Portal da Transparência."),
			"link": "/transparencia/ajuda"
		},
		{
			"titulo": _("Dados antes de 2016"),
			"descricao": _("Dados de receitas, despesas, contratos e licitações realizados antes de 2016."),
			"link": "/transparencia/dados-antes-2016"
		},
		{
			"titulo": _("Calendário Oficial"),
			"descricao": _("Encontre o calendário oficial da prefeitura com todos os feriados e pontos facultativos."),
			"link": "/transparencia/calendario-oficial"
		}
	]

def get_estatisticas():
	"""Retorna estatísticas recentes para exibir no portal."""
	# Em um ambiente real, esses dados viriam do banco de dados
	return {
		"orcamento_total": frappe.utils.fmt_money(100000000, currency="BRL"),
		"despesas_total": frappe.utils.fmt_money(45000000, currency="BRL"),
		"receitas_total": frappe.utils.fmt_money(52000000, currency="BRL"),
		"contratos_ativos": 156,
		"licitacoes_andamento": 23,
		"servidores_ativos": 1250
	}

def get_atualizacoes_recentes():
	"""Retorna as atualizações mais recentes do portal."""
	# Em um ambiente real, esses dados viriam do banco de dados
	return [
		{
			"titulo": _("Publicação do Relatório de Gestão Fiscal"),
			"data": "2025-06-10",
			"tipo": "Prestação de Contas",
			"link": "/transparencia/relatorio-gestao-fiscal-2025-q1"
		},
		{
			"titulo": _("Nova licitação para aquisição de medicamentos"),
			"data": "2025-06-05",
			"tipo": "Licitação",
			"link": "/transparencia/licitacao/2025-056"
		},
		{
			"titulo": _("Publicação da folha de pagamento de maio/2025"),
			"data": "2025-06-01",
			"tipo": "Folha de Pagamento",
			"link": "/transparencia/folha-pagamento/2025-05"
		},
		{
			"titulo": _("Atualização dos dados de receitas municipais"),
			"data": "2025-05-28",
			"tipo": "Receitas",
			"link": "/transparencia/receitas/maio-2025"
		},
		{
			"titulo": _("Novo contrato de limpeza urbana"),
			"data": "2025-05-25",
			"tipo": "Contratos",
			"link": "/transparencia/contrato/2025-089"
		}
	]

def get_todos_servicos():
	"""Retorna todos os serviços disponíveis no portal."""
	try:
		from apps.govnext_core.govnext_core.transparencia.portal.config import get_data

		servicos = []
		for secao in get_data():
			for item in secao.get("items", []):
				servicos.append({
					"titulo": item.get("label"),
					"descricao": item.get("description"),
					"link": get_item_link(item),
					"categoria": secao.get("label")
				})

		return servicos
	except:
		# Fallback caso o config não esteja disponível
		return []

def get_info_institucional():
	"""Retorna informações institucionais para exibir no rodapé."""
	return {
		"nome": _("Prefeitura Municipal de GovNext"),
		"endereco": _("Rua da Transparência, 123 • Centro • GovNext-BR • CEP. 12.345-678"),
		"telefone": _("(11) 3456-7890 • 3456-7000"),
		"email": "transparencia@govnext.gov.br",
		"horario": _("Segunda a sexta, das 8h às 17h")
	}

def get_item_link(item):
	"""Gera o link para um item do menu."""
	tipo = item.get("type")
	nome = item.get("name")

	if tipo == "doctype":
		return f"/transparencia/list/{nome}"
	elif tipo == "page":
		return f"/transparencia/{nome}"
	else:
		return "#"
