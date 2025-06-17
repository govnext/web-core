# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class AnexoDocumento(Document):
	"""
	Classe para gerenciar anexos de documentos.

	Cada anexo representa um arquivo que pode ser associado a diversos
	tipos de documentos no sistema, como empenhos, liquidações, etc.
	"""

	def validate(self):
		"""
		Validações do anexo antes de salvar:
		1. Verifica se os campos obrigatórios estão preenchidos
		"""
		self.validar_campos_obrigatorios()

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		if not self.tipo_anexo:
			frappe.throw(_("O tipo de anexo é obrigatório"))

		if not self.arquivo_anexo:
			frappe.throw(_("É necessário anexar o arquivo"))
