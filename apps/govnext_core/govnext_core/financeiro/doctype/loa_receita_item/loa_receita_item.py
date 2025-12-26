# -*- coding: utf-8 -*-
# Copyright (c) 2025, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class LOAReceitaItem(Document):
	"""
	Child doctype para itens de receita da LOA
	Implementa classificação de receitas conforme STN
	"""
	
	def validate(self):
		"""Validações do item de receita"""
		self.validar_codigo_receita()
		self.validar_valor_previsto()
		self.validar_classificacao()
		
	def validar_codigo_receita(self):
		"""Valida o código da receita conforme padrão STN"""
		if not self.codigo_receita:
			frappe.throw("Código da receita é obrigatório")
			
		# Código deve ter formato: X.X.XX.XX.XX (categoria.origem.espécie.rubrica.alínea)
		codigo_parts = self.codigo_receita.split('.')
		if len(codigo_parts) < 2:
			frappe.throw("Código da receita deve seguir o padrão: categoria.origem.espécie.rubrica")
			
		# Validar categoria econômica
		categoria_codigo = codigo_parts[0]
		if categoria_codigo == "1" and self.categoria_economica != "Receitas Correntes":
			frappe.throw("Código iniciado com '1' deve ser classificado como 'Receitas Correntes'")
		elif categoria_codigo == "2" and self.categoria_economica != "Receitas de Capital":
			frappe.throw("Código iniciado com '2' deve ser classificado como 'Receitas de Capital'")
			
	def validar_valor_previsto(self):
		"""Valida o valor previsto"""
		if not self.valor_previsto or flt(self.valor_previsto) <= 0:
			frappe.throw("Valor previsto deve ser maior que zero")
			
	def validar_classificacao(self):
		"""Valida a consistência da classificação"""
		# Mapear origens por categoria econômica
		receitas_correntes = [
			"Receitas Tributárias", "Receitas de Contribuições", "Receitas Patrimoniais",
			"Receitas Agropecuárias", "Receitas Industriais", "Receitas de Serviços",
			"Transferências Correntes", "Outras Receitas Correntes"
		]
		
		receitas_capital = [
			"Operações de Crédito", "Alienação de Bens", "Amortização de Empréstimos",
			"Transferências de Capital", "Outras Receitas de Capital"
		]
		
		if self.categoria_economica == "Receitas Correntes" and self.origem_receita not in receitas_correntes:
			frappe.throw(f"Origem '{self.origem_receita}' não é compatível com Receitas Correntes")
			
		if self.categoria_economica == "Receitas de Capital" and self.origem_receita not in receitas_capital:
			frappe.throw(f"Origem '{self.origem_receita}' não é compatível com Receitas de Capital")