# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ComprovantePagamento(Document):
	"""
	Classe para gerenciar os comprovantes de pagamento.

	Cada comprovante representa um documento que comprova a realização
	do pagamento, como comprovante de transferência, recibo, etc.
	"""

	def validate(self):
		"""
		Validações do comprovante de pagamento antes de salvar:
		1. Verifica se os campos obrigatórios estão preenchidos
		"""
		self.validar_campos_obrigatorios()

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		if not self.tipo_comprovante:
			frappe.throw(frappe._("O tipo de comprovante é obrigatório"))

		if not self.arquivo_comprovante:
			frappe.throw(frappe._("É necessário anexar o arquivo do comprovante"))
