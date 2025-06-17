# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class DocumentoFiscalLiquidacao(Document):
	"""
	Classe para gerenciar os documentos fiscais utilizados na liquidação.

	Cada documento fiscal representa uma nota fiscal, fatura, recibo ou
	outro documento que comprove a entrega do bem ou prestação do serviço.
	"""

	def validate(self):
		"""
		Validações do documento fiscal antes de salvar:
		1. Valida o formato e consistência dos dados
		2. Verifica se os campos obrigatórios estão preenchidos
		"""
		self.validar_campos_obrigatorios()
		self.validar_datas()
		self.validar_valores()

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"tipo_documento", "numero_documento", "data_emissao", "valor"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório para o documento fiscal").format(
					frappe.bold(self.meta.get_label(campo))
				))

	def validar_datas(self):
		"""
		Valida as datas do documento fiscal:
		1. Data de emissão não pode ser maior que a data atual
		"""
		hoje = datetime.date.today()

		# Data de emissão não pode ser maior que hoje
		if self.data_emissao and self.data_emissao > hoje:
			frappe.throw(_("A data de emissão do documento fiscal não pode ser maior que a data atual"))

	def validar_valores(self):
		"""
		Valida os valores do documento fiscal:
		1. Valor deve ser maior que zero
		"""
		if not self.valor > 0:
			frappe.throw(_("O valor do documento fiscal deve ser maior que zero"))

		# Se houver valor de impostos, validar
		if hasattr(self, 'valor_imposto') and self.valor_imposto:
			if self.valor_imposto < 0:
				frappe.throw(_("O valor de impostos não pode ser negativo"))

			if self.valor_imposto > self.valor:
				frappe.throw(_("O valor de impostos não pode ser maior que o valor total do documento"))
