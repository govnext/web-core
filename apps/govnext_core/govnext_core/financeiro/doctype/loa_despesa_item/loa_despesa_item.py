# -*- coding: utf-8 -*-
# Copyright (c) 2025, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class LOADespesaItem(Document):
	"""
	Child doctype para itens de despesa da LOA
	Implementa classificação de despesas conforme STN e Portaria Interministerial STN/SOF
	"""
	
	def validate(self):
		"""Validações do item de despesa"""
		self.validar_classificacao_institucional()
		self.validar_classificacao_funcional()
		self.validar_classificacao_economica()
		self.validar_valores()
		self.calcular_campos_derivados()
		
	def validar_classificacao_institucional(self):
		"""Valida a classificação institucional (órgão/unidade)"""
		if not self.orgao:
			frappe.throw("Código do órgão é obrigatório")
			
		if not self.unidade:
			frappe.throw("Código da unidade orçamentária é obrigatório")
			
		# Validar formato do código do órgão (2 dígitos)
		if not self.orgao.isdigit() or len(self.orgao) != 2:
			frappe.throw("Código do órgão deve ter 2 dígitos numéricos")
			
		# Validar formato do código da unidade (2 dígitos)  
		if not self.unidade.isdigit() or len(self.unidade) != 2:
			frappe.throw("Código da unidade orçamentária deve ter 2 dígitos numéricos")
			
	def validar_classificacao_funcional(self):
		"""Valida a classificação funcional (função/subfunção)"""
		if not self.funcao:
			frappe.throw("Função de governo é obrigatória")
			
		if not self.subfuncao:
			frappe.throw("Subfunção de governo é obrigatória")
			
		# Validar formato da subfunção (3 dígitos)
		if not self.subfuncao.isdigit() or len(self.subfuncao) != 3:
			frappe.throw("Código da subfunção deve ter 3 dígitos numéricos")
			
		# Validar se subfunção é compatível com a função
		funcao_codigo = self.funcao.split(' - ')[0] if ' - ' in self.funcao else self.funcao
		subfuncao_primeiro_digito = self.subfuncao[0]
		
		# Algumas subfunções são típicas e podem ser usadas com qualquer função
		subfuncoes_tipicas = ['122', '123', '124', '125', '126', '127', '128', '129', '130', '131']
		
		if self.subfuncao not in subfuncoes_tipicas:
			# Para subfunções não típicas, o primeiro dígito deve corresponder à função
			if funcao_codigo.zfill(2) != subfuncao_primeiro_digito.zfill(2):
				frappe.msgprint(
					f"Atenção: Subfunção {self.subfuncao} pode não ser típica da função {self.funcao}",
					alert=True
				)
				
	def validar_classificacao_economica(self):
		"""Valida a classificação por natureza da despesa"""
		if not self.categoria_economica:
			frappe.throw("Categoria econômica é obrigatória")
			
		if not self.grupo_natureza:
			frappe.throw("Grupo de natureza é obrigatório")
			
		if not self.modalidade_aplicacao:
			frappe.throw("Modalidade de aplicação é obrigatória")
			
		if not self.elemento_despesa:
			frappe.throw("Elemento de despesa é obrigatório")
			
		# Validar consistência entre categoria econômica e grupo de natureza
		categoria_num = self.categoria_economica.split(' - ')[0]
		grupo_num = self.grupo_natureza.split(' - ')[0]
		
		if categoria_num == "3":  # Despesas Correntes
			if grupo_num not in ["1", "2", "3"]:
				frappe.throw("Despesas Correntes devem ter grupos 1, 2 ou 3")
		elif categoria_num == "4":  # Despesas de Capital
			if grupo_num not in ["4", "5", "6"]:
				frappe.throw("Despesas de Capital devem ter grupos 4, 5 ou 6")
				
		# Validar elemento de despesa (2 dígitos)
		if not self.elemento_despesa.isdigit() or len(self.elemento_despesa) != 2:
			frappe.throw("Elemento de despesa deve ter 2 dígitos numéricos")
			
		# Validar subelemento se informado (2 dígitos)
		if self.subelemento_despesa:
			if not self.subelemento_despesa.isdigit() or len(self.subelemento_despesa) != 2:
				frappe.throw("Subelemento de despesa deve ter 2 dígitos numéricos")
				
	def validar_valores(self):
		"""Valida os valores orçamentários"""
		if not self.valor_fixado or flt(self.valor_fixado) <= 0:
			frappe.throw("Valor fixado deve ser maior que zero")
			
		# Validar se valores empenhado/liquidado/pago não excedem o fixado
		if flt(self.valor_empenhado) > flt(self.valor_fixado):
			frappe.throw("Valor empenhado não pode exceder o valor fixado")
			
		if flt(self.valor_liquidado) > flt(self.valor_empenhado):
			frappe.throw("Valor liquidado não pode exceder o valor empenhado")
			
		if flt(self.valor_pago) > flt(self.valor_liquidado):
			frappe.throw("Valor pago não pode exceder o valor liquidado")
			
	def calcular_campos_derivados(self):
		"""Calcula campos derivados"""
		# Calcular saldo disponível
		self.saldo_disponivel = flt(self.valor_fixado) - flt(self.valor_empenhado)
		
		# Calcular percentual de execução
		if flt(self.valor_fixado) > 0:
			self.percentual_execucao = (flt(self.valor_empenhado) / flt(self.valor_fixado)) * 100
		else:
			self.percentual_execucao = 0
			
	def get_dotacao_code(self):
		"""Retorna o código completo da dotação orçamentária"""
		return f"{self.orgao}.{self.unidade}.{self.funcao.split(' - ')[0]}.{self.subfuncao}.{self.programa}.{self.acao}.{self.elemento_despesa}"
		
	def get_natureza_despesa_code(self):
		"""Retorna o código da natureza da despesa"""
		categoria = self.categoria_economica.split(' - ')[0]
		grupo = self.grupo_natureza.split(' - ')[0] 
		modalidade = self.modalidade_aplicacao.split(' - ')[0]
		elemento = self.elemento_despesa
		subelemento = self.subelemento_despesa or "00"
		
		return f"{categoria}.{grupo}.{modalidade}.{elemento}.{subelemento}"