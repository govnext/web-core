# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate
import json
import re

def get_context(context):
	"""
	Prepara o contexto para a página de busca do Portal da Transparência.
	"""
	context.title = _("Busca no Portal da Transparência")
	context.subtitle = _("Encontre informações sobre receitas, despesas, contratos, licitações e muito mais.")

	# Termo de busca
	query = frappe.form_dict.get('q', '').strip()
	context.query = query

	if query:
		# Realizar busca
		context.resultados = realizar_busca(query)
		context.total_resultados = len(context.resultados)

		# Estatísticas da busca
		context.stats_busca = get_stats_busca(context.resultados)
	else:
		context.resultados = []
		context.total_resultados = 0
		context.stats_busca = {}

	# Sugestões de busca
	context.sugestoes = get_sugestoes_busca()

	# Termos mais buscados
	context.termos_populares = get_termos_populares()

	return context

def realizar_busca(query):
	"""
	Realiza a busca nos diferentes módulos do portal.
	"""
	resultados = []

	# Buscar em despesas
	resultados_despesas = buscar_despesas(query)
	resultados.extend(resultados_despesas)

	# Buscar em receitas
	resultados_receitas = buscar_receitas(query)
	resultados.extend(resultados_receitas)

	# Buscar em contratos
	resultados_contratos = buscar_contratos(query)
	resultados.extend(resultados_contratos)

	# Buscar em licitações
	resultados_licitacoes = buscar_licitacoes(query)
	resultados.extend(resultados_licitacoes)

	# Buscar em servidores (se termo relacionado)
	if any(termo in query.lower() for termo in ['servidor', 'funcionario', 'salario', 'folha']):
		resultados_servidores = buscar_servidores(query)
		resultados.extend(resultados_servidores)

	# Ordenar por relevância
	resultados = sorted(resultados, key=lambda x: x.get('relevancia', 0), reverse=True)

	return resultados

def buscar_despesas(query):
	"""Busca em despesas."""
	resultados = []

	# Dados de exemplo - em produção viria do banco
	despesas_exemplo = [
		{
			"id": "2025/001234",
			"fornecedor": "Empresa de Limpeza Municipal Ltda",
			"descricao": "Serviços de limpeza urbana - Contrato 2025/089",
			"valor": 45000.00,
			"data": "2025-06-15",
			"categoria": "Serviços de Terceiros"
		},
		{
			"id": "2025/001235",
			"fornecedor": "Construtora ABC S.A.",
			"descricao": "Obra de pavimentação da Rua das Flores",
			"valor": 125000.00,
			"data": "2025-06-14",
			"categoria": "Obras e Instalações"
		}
	]

	for despesa in despesas_exemplo:
		if busca_match(query, [despesa["fornecedor"], despesa["descricao"], despesa["categoria"]]):
			resultado = {
				"tipo": "despesa",
				"titulo": f"Despesa: {despesa['fornecedor']}",
				"descricao": despesa["descricao"],
				"valor": fmt_money(despesa["valor"], currency="BRL"),
				"data": frappe.utils.formatdate(despesa["data"], "dd/MM/yyyy"),
				"link": f"/transparencia/despesas?id={despesa['id']}",
				"categoria": despesa["categoria"],
				"relevancia": calcular_relevancia(query, despesa["descricao"] + " " + despesa["fornecedor"])
			}
			resultados.append(resultado)

	return resultados

def buscar_receitas(query):
	"""Busca em receitas."""
	resultados = []

	receitas_exemplo = [
		{
			"id": "2025/REC001234",
			"fonte": "IPTU - Imposto Predial e Territorial Urbano",
			"descricao": "Arrecadação IPTU - Parcela 6/10 - Exercício 2025",
			"valor": 156000.00,
			"data": "2025-06-15",
			"categoria": "Impostos"
		},
		{
			"id": "2025/REC001235",
			"fonte": "FPM - Fundo de Participação dos Municípios",
			"descricao": "Transferência FPM - 2º decêndio de junho/2025",
			"valor": 485000.00,
			"data": "2025-06-14",
			"categoria": "Transferências da União"
		}
	]

	for receita in receitas_exemplo:
		if busca_match(query, [receita["fonte"], receita["descricao"], receita["categoria"]]):
			resultado = {
				"tipo": "receita",
				"titulo": f"Receita: {receita['fonte']}",
				"descricao": receita["descricao"],
				"valor": fmt_money(receita["valor"], currency="BRL"),
				"data": frappe.utils.formatdate(receita["data"], "dd/MM/yyyy"),
				"link": f"/transparencia/receitas?id={receita['id']}",
				"categoria": receita["categoria"],
				"relevancia": calcular_relevancia(query, receita["descricao"] + " " + receita["fonte"])
			}
			resultados.append(resultado)

	return resultados

def buscar_contratos(query):
	"""Busca em contratos."""
	resultados = []

	contratos_exemplo = [
		{
			"id": "2025/CT-089",
			"numero": "089/2025",
			"fornecedor": "Empresa de Limpeza Municipal Ltda",
			"objeto": "Prestação de serviços de limpeza urbana",
			"valor": 540000.00,
			"situacao": "Vigente"
		},
		{
			"id": "2025/CT-156",
			"numero": "156/2025",
			"fornecedor": "Construtora ABC S.A.",
			"objeto": "Construção de praça pública no bairro Centro",
			"valor": 850000.00,
			"situacao": "Em execução"
		}
	]

	for contrato in contratos_exemplo:
		if busca_match(query, [contrato["fornecedor"], contrato["objeto"], contrato["numero"]]):
			resultado = {
				"tipo": "contrato",
				"titulo": f"Contrato {contrato['numero']}: {contrato['fornecedor']}",
				"descricao": contrato["objeto"],
				"valor": fmt_money(contrato["valor"], currency="BRL"),
				"data": contrato["situacao"],
				"link": f"/transparencia/contratos?id={contrato['id']}",
				"categoria": "Contratos",
				"relevancia": calcular_relevancia(query, contrato["objeto"] + " " + contrato["fornecedor"])
			}
			resultados.append(resultado)

	return resultados

def buscar_licitacoes(query):
	"""Busca em licitações."""
	resultados = []

	licitacoes_exemplo = [
		{
			"id": "2025/LIC-045",
			"numero": "045/2025",
			"objeto": "Aquisição de material de limpeza",
			"modalidade": "Pregão Eletrônico",
			"situacao": "Em andamento",
			"valor_estimado": 75000.00
		}
	]

	for licitacao in licitacoes_exemplo:
		if busca_match(query, [licitacao["objeto"], licitacao["numero"], licitacao["modalidade"]]):
			resultado = {
				"tipo": "licitacao",
				"titulo": f"Licitação {licitacao['numero']}: {licitacao['modalidade']}",
				"descricao": licitacao["objeto"],
				"valor": fmt_money(licitacao["valor_estimado"], currency="BRL"),
				"data": licitacao["situacao"],
				"link": f"/transparencia/licitacoes?id={licitacao['id']}",
				"categoria": "Licitações",
				"relevancia": calcular_relevancia(query, licitacao["objeto"])
			}
			resultados.append(resultado)

	return resultados

def buscar_servidores(query):
	"""Busca em dados de servidores (resumidos por privacidade)."""
	resultados = []

	# Dados agregados apenas - sem informações pessoais específicas
	if any(termo in query.lower() for termo in ['folha', 'salario', 'pagamento', 'servidor']):
		resultado = {
			"tipo": "servidor",
			"titulo": "Folha de Pagamento de Servidores",
			"descricao": "Consulte informações agregadas sobre a folha de pagamento dos servidores públicos",
			"valor": "R$ 8.500.000,00",
			"data": "Junho/2025",
			"link": "/transparencia/gestao-pessoas",
			"categoria": "Gestão de Pessoas",
			"relevancia": 80
		}
		resultados.append(resultado)

	return resultados

def busca_match(query, campos):
	"""
	Verifica se a query coincide com algum dos campos.
	"""
	query_lower = query.lower()
	for campo in campos:
		if campo and query_lower in campo.lower():
			return True
	return False

def calcular_relevancia(query, texto):
	"""
	Calcula a relevância de um resultado com base na query.
	"""
	if not texto:
		return 0

	texto_lower = texto.lower()
	query_lower = query.lower()

	# Pontuação base
	relevancia = 0

	# Match exato
	if query_lower == texto_lower:
		relevancia += 100

	# Match no início
	elif texto_lower.startswith(query_lower):
		relevancia += 80

	# Match em palavras
	elif query_lower in texto_lower:
		relevancia += 60

	# Match de palavras individuais
	else:
		palavras_query = query_lower.split()
		palavras_texto = texto_lower.split()
		matches = sum(1 for palavra in palavras_query if palavra in palavras_texto)
		relevancia += (matches / len(palavras_query)) * 40

	return relevancia

def get_stats_busca(resultados):
	"""
	Gera estatísticas dos resultados da busca.
	"""
	if not resultados:
		return {}

	stats = {}

	# Contar por tipo
	tipos = {}
	for resultado in resultados:
		tipo = resultado.get("tipo", "outro")
		tipos[tipo] = tipos.get(tipo, 0) + 1

	stats["por_tipo"] = tipos

	# Valor total (onde aplicável)
	valor_total = 0
	for resultado in resultados:
		valor_str = resultado.get("valor", "")
		if valor_str and "R$" in valor_str:
			# Extrair valor numérico
			try:
				valor_numerico = re.sub(r'[^\d,]', '', valor_str).replace(',', '.')
				if valor_numerico:
					valor_total += float(valor_numerico)
			except:
				pass

	if valor_total > 0:
		stats["valor_total"] = fmt_money(valor_total, currency="BRL")

	return stats

def get_sugestoes_busca():
	"""
	Retorna sugestões de busca populares.
	"""
	return [
		"IPTU",
		"Folha de pagamento",
		"Contratos de limpeza",
		"Transferências FPM",
		"Obras públicas",
		"Licitações medicamentos",
		"ISS",
		"Servidores educação",
		"Prestação de contas",
		"Orçamento 2025"
	]

def get_termos_populares():
	"""
	Retorna os termos mais buscados.
	"""
	return [
		{"termo": "IPTU", "frequencia": 245},
		{"termo": "Folha pagamento", "frequencia": 189},
		{"termo": "Contratos", "frequencia": 156},
		{"termo": "Licitações", "frequencia": 134},
		{"termo": "Receitas", "frequencia": 98},
		{"termo": "Obras", "frequencia": 87}
	]

@frappe.whitelist(allow_guest=True)
def busca_ajax(query):
	"""
	Endpoint AJAX para busca em tempo real.
	"""
	if not query or len(query) < 3:
		return {"resultados": [], "total": 0}

	resultados = realizar_busca(query)

	# Limitar resultados para AJAX
	resultados = resultados[:10]

	return {
		"resultados": resultados,
		"total": len(resultados),
		"query": query
	}

@frappe.whitelist(allow_guest=True)
def registrar_busca(query):
	"""
	Registra uma busca para estatísticas (sem dados pessoais).
	"""
	if query and len(query.strip()) >= 3:
		# Em produção, salvar em log de buscas para melhorar sugestões
		frappe.logger().info(f"Busca realizada: {query}")

	return {"success": True}
