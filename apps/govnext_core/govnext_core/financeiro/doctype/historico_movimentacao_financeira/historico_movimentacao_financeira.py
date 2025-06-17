# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class HistoricoMovimentacaoFinanceira(Document):
	"""
	Classe para gerenciar o histórico de movimentações financeiras.

	Registra todas as operações financeiras realizadas no sistema,
	como empenhos, liquidações, pagamentos e estornos.
	"""

	def validate(self):
		"""
		Validações do histórico de movimentação financeira antes de salvar:
		1. Verifica se os campos obrigatórios estão preenchidos
		"""
		self.validar_campos_obrigatorios()

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"tipo_documento", "documento_referencia", "descricao",
			"valor", "data_movimento"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório para o histórico de movimentação").format(
					frappe.bold(self.meta.get_label(campo))
				))

	def before_insert(self):
		"""
		Ações antes de inserir o registro:
		1. Define o usuário atual como responsável pela operação
		2. Define a data atual se não informada
		"""
		if not self.usuario:
			self.usuario = frappe.session.user

		if not self.data_movimento:
			self.data_movimento = datetime.date.today()

	def on_submit(self):
		"""
		Ações ao submeter o histórico de movimentação:
		1. Notifica os usuários interessados
		"""
		self.notificar_usuarios()

	def notificar_usuarios(self):
		"""
		Notifica os usuários interessados sobre a movimentação financeira.
		"""
		# Implementar lógica de notificação
		pass
