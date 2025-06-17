# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ItemEmpenho(Document):
	"""
	Classe para gerenciar os itens de empenho.

	Cada item representa um produto ou serviço que está sendo empenhado,
	com suas respectivas quantidades, valores unitários e totais.
	"""

	def validate(self):
		"""
		Validações do item de empenho antes de salvar:
		1. Valida os campos obrigatórios
		2. Calcula o valor total do item
		"""
		self.validar_campos_obrigatorios()
		self.calcular_valor_total()

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"descricao", "quantidade", "valor_unitario"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório para o item de empenho").format(
					frappe.bold(self.meta.get_label(campo))
				))

		if self.quantidade <= 0:
			frappe.throw(_("A quantidade deve ser maior que zero"))

		if self.valor_unitario <= 0:
			frappe.throw(_("O valor unitário deve ser maior que zero"))

	def calcular_valor_total(self):
		"""
		Calcula o valor total do item com base na quantidade e valor unitário.
		"""
		self.valor_total = self.quantidade * self.valor_unitario
