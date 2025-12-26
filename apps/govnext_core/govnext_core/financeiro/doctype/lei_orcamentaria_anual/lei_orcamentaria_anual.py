# -*- coding: utf-8 -*-
# Copyright (c) 2025, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_years
from datetime import datetime, date

class LeiOrcamentariaAnual(Document):
	"""
	Doctype para Lei Orçamentária Anual (LOA)
	Implementa as regras da Lei de Responsabilidade Fiscal e normas do STN
	"""
	
	def validate(self):
		"""Validações específicas da LOA conforme legislação brasileira"""
		self.validar_exercicio_financeiro()
		self.validar_equilibrio_orcamentario()
		self.validar_metas_fiscais()
		self.validar_limites_lrf()
		self.calcular_totais()
		
	def before_save(self):
		"""Processamento antes de salvar"""
		self.atualizar_status_aprovacao()
		self.validar_compatibilidade_ldo()
		
	def on_submit(self):
		"""Ao submeter a LOA"""
		self.validar_documentos_obrigatorios()
		self.criar_dotacoes_orcamentarias()
		
	def validar_exercicio_financeiro(self):
		"""Valida se o exercício financeiro está correto"""
		if not self.ano_exercicio:
			frappe.throw("Ano do exercício é obrigatório")
			
		if self.ano_exercicio < 2024:
			frappe.throw("Ano do exercício deve ser 2024 ou posterior")
			
		# Valida se já existe LOA para o mesmo exercício
		if self.is_new():
			existing_loa = frappe.db.exists("Lei Orcamentaria Anual", {
				"ano_exercicio": self.ano_exercicio,
				"status_aprovacao": ["in", ["Sancionada", "Promulgada", "Vigente"]],
				"name": ["!=", self.name]
			})
			if existing_loa:
				frappe.throw(f"Já existe LOA aprovada para o exercício {self.ano_exercicio}")
	
	def validar_equilibrio_orcamentario(self):
		"""Valida o equilíbrio orçamentário (art. 4º LRF)"""
		if not (self.total_receita_prevista and self.total_despesa_fixada):
			return
			
		diferenca = abs(flt(self.total_receita_prevista) - flt(self.total_despesa_fixada))
		
		if diferenca > 0.01:  # Tolerância de R$ 0,01
			frappe.msgprint(
				f"Atenção: Diferença de R$ {diferenca:.2f} entre receitas e despesas. "
				"O orçamento deve estar equilibrado conforme art. 4º da LRF.",
				alert=True
			)
	
	def validar_metas_fiscais(self):
		"""Valida as metas fiscais conforme LRF"""
		# Valida meta de resultado primário
		if self.meta_resultado_primario and flt(self.meta_resultado_primario) < 0:
			frappe.msgprint(
				"Meta de resultado primário negativa. Verifique a compatibilidade com a LDO.",
				alert=True
			)
			
		# Valida meta da dívida pública
		if self.meta_divida_publica_liquida:
			# Deve estar compatível com os limites da LRF (200% RCL para municípios)
			pass
	
	def validar_limites_lrf(self):
		"""Valida os limites da Lei de Responsabilidade Fiscal"""
		if self.limite_despesa_pessoal:
			# Limite prudencial: 54% da RCL (95% do limite de 60%)
			rcl_estimada = self.calcular_rcl_estimada()
			if rcl_estimada > 0:
				percentual_pessoal = (flt(self.limite_despesa_pessoal) / rcl_estimada) * 100
				if percentual_pessoal > 54:
					frappe.throw(
						f"Limite de despesa com pessoal ({percentual_pessoal:.1f}%) "
						"excede o limite prudencial de 54% da RCL"
					)
	
	def calcular_rcl_estimada(self):
		"""Calcula a Receita Corrente Líquida estimada"""
		# Implementar cálculo baseado nas receitas correntes
		receita_corrente = 0
		if self.receitas_orcamentarias:
			for receita in self.receitas_orcamentarias:
				if receita.categoria_economica == "Receitas Correntes":
					receita_corrente += flt(receita.valor_previsto)
		
		# Deduzir contribuições previdenciárias, transferências constitucionais, etc.
		# Simplificado - implementar cálculo completo conforme STN
		return receita_corrente * 0.85  # Estimativa aproximada
	
	def calcular_totais(self):
		"""Calcula os totais de receitas e despesas"""
		total_receita = 0
		total_despesa = 0
		
		# Calcula total de receitas
		if self.receitas_orcamentarias:
			for receita in self.receitas_orcamentarias:
				total_receita += flt(receita.valor_previsto)
		
		# Calcula total de despesas
		if self.despesas_orcamentarias:
			for despesa in self.despesas_orcamentarias:
				total_despesa += flt(despesa.valor_fixado)
		
		self.total_receita_prevista = total_receita
		self.total_despesa_fixada = total_despesa
	
	def atualizar_status_aprovacao(self):
		"""Atualiza o status conforme o ciclo de aprovação"""
		if self.data_promulgacao and not self.status_aprovacao in ["Promulgada", "Vigente", "Encerrada"]:
			self.status_aprovacao = "Promulgada"
			
		# Se está no período de vigência
		if (self.data_vigencia_inicio and self.data_vigencia_fim and 
			getdate() >= getdate(self.data_vigencia_inicio) and 
			getdate() <= getdate(self.data_vigencia_fim)):
			self.status_aprovacao = "Vigente"
			
		# Se passou do período de vigência
		if (self.data_vigencia_fim and 
			getdate() > getdate(self.data_vigencia_fim)):
			self.status_aprovacao = "Encerrada"
	
	def validar_compatibilidade_ldo(self):
		"""Valida se a LOA está compatível com a LDO"""
		# Buscar LDO do mesmo exercício
		ldo = frappe.get_value("Lei Diretrizes Orcamentarias", 
			{"ano_exercicio": self.ano_exercicio, "status": "Aprovada"}, 
			["name", "prioridades_governo"])
		
		if ldo:
			frappe.msgprint(
				f"LOA deve estar compatível com a LDO {ldo} do mesmo exercício.",
				alert=True
			)
	
	def validar_documentos_obrigatorios(self):
		"""Valida se os anexos obrigatórios estão presentes"""
		documentos_obrigatorios = [
			"anexo_receitas_despesas",
			"anexo_pessoal_encargos"
		]
		
		for doc in documentos_obrigatorios:
			if not self.get(doc):
				frappe.throw(f"Anexo obrigatório '{doc}' não foi incluído")
	
	def criar_dotacoes_orcamentarias(self):
		"""Cria as dotações orçamentárias baseadas na LOA aprovada"""
		if not self.despesas_orcamentarias:
			return
			
		for despesa in self.despesas_orcamentarias:
			# Criar dotação orçamentária
			dotacao = frappe.new_doc("DotacaoOrcamentaria")
			dotacao.update({
				"codigo_dotacao": f"{despesa.orgao}-{despesa.unidade}-{despesa.funcao}-{despesa.subfuncao}-{despesa.programa}",
				"exercicio_financeiro": self.ano_exercicio,
				"orgao": despesa.orgao,
				"unidade_orcamentaria": despesa.unidade,
				"funcao_governo": despesa.funcao,
				"subfuncao_governo": despesa.subfuncao,
				"programa_governo": despesa.programa,
				"elemento_despesa": despesa.elemento_despesa,
				"valor_inicial": despesa.valor_fixado,
				"valor_disponivel": despesa.valor_fixado,
				"lei_orcamentaria": self.name
			})
			dotacao.insert()
			
		frappe.msgprint(f"Criadas {len(self.despesas_orcamentarias)} dotações orçamentárias")
	
	def get_dashboard_data(self):
		"""Retorna dados para o dashboard"""
		return {
			'fieldname': 'lei_orcamentaria',
			'non_standard_fieldnames': {
				'Orcamento': 'lei_orcamentaria',
				'DotacaoOrcamentaria': 'lei_orcamentaria'
			},
			'transactions': [
				{
					'label': 'Execução',
					'items': ['Orcamento', 'DotacaoOrcamentaria', 'Empenho']
				},
				{
					'label': 'Relatórios',
					'items': ['Balancete', 'Balanço Orçamentário']
				}
			]
		}

@frappe.whitelist()
def get_receitas_por_categoria(ano_exercicio):
	"""Retorna receitas agrupadas por categoria para análise"""
	if not ano_exercicio:
		return []
		
	loa = frappe.get_doc("Lei Orcamentaria Anual", {"ano_exercicio": ano_exercicio})
	
	categorias = {}
	if loa.receitas_orcamentarias:
		for receita in loa.receitas_orcamentarias:
			categoria = receita.categoria_economica
			if categoria not in categorias:
				categorias[categoria] = 0
			categorias[categoria] += flt(receita.valor_previsto)
	
	return categorias

@frappe.whitelist()
def get_despesas_por_funcao(ano_exercicio):
	"""Retorna despesas agrupadas por função para análise"""
	if not ano_exercicio:
		return []
		
	loa = frappe.get_doc("Lei Orcamentaria Anual", {"ano_exercicio": ano_exercicio})
	
	funcoes = {}
	if loa.despesas_orcamentarias:
		for despesa in loa.despesas_orcamentarias:
			funcao = despesa.funcao_governo
			if funcao not in funcoes:
				funcoes[funcao] = 0
			funcoes[funcao] += flt(despesa.valor_fixado)
	
	return funcoes