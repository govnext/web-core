# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class UnidadeOrcamentaria(Document):
	"""
	Classe para gerenciar unidades orçamentárias.

	A unidade orçamentária é a entidade administrativa responsável
	pela execução de parte do orçamento.
	"""

	def validate(self):
		"""
		Validações da unidade orçamentária antes de salvar:
		1. Valida os campos obrigatórios
		2. Valida o código da unidade orçamentária
		"""
		self.validar_codigo()
		self.validar_vinculacao_orgao()

	def validar_codigo(self):
		"""
		Valida o código da unidade orçamentária:
		- Deve ser numérico
		- Deve ter o tamanho correto (geralmente 6 dígitos)
		"""
		if not self.codigo:
			frappe.throw(_("O código da unidade orçamentária é obrigatório"))

		if not self.codigo.isdigit():
			frappe.throw(_("O código da unidade orçamentária deve conter apenas números"))

		if len(self.codigo) != 6:
			frappe.msgprint(
				_("O código da unidade orçamentária deve ter 6 dígitos. O código informado tem {0} dígitos.").format(len(self.codigo)),
				indicator="orange",
				alert=True
			)

	def validar_vinculacao_orgao(self):
		"""
		Valida se a unidade orçamentária está vinculada a um órgão público.
		"""
		if not self.orgao_publico:
			frappe.throw(_("A unidade orçamentária deve estar vinculada a um órgão público"))

		# Verifica se o órgão existe
		if not frappe.db.exists("OrgaoPublico", self.orgao_publico):
			frappe.throw(_("O órgão público {0} não existe").format(self.orgao_publico))

	def on_update(self):
		"""
		Ações ao atualizar a unidade orçamentária:
		1. Atualiza informações nas dotações orçamentárias vinculadas
		"""
		if self.has_value_changed("nome"):
			self.atualizar_dotacoes()

	def atualizar_dotacoes(self):
		"""
		Atualiza as dotações orçamentárias vinculadas a esta unidade.
		"""
		# Implementação futura se necessário
		pass

	def before_rename(self, old_name, new_name, merge=False):
		"""
		Ações antes de renomear a unidade orçamentária:
		1. Verifica se há dotações orçamentárias vinculadas
		"""
		dotacoes = frappe.get_all(
			"DotacaoOrcamentaria",
			filters={"unidade_orcamentaria": old_name, "docstatus": 1}
		)

		if dotacoes:
			frappe.throw(_(
				"Não é possível renomear esta unidade orçamentária pois existem {0} dotações orçamentárias vinculadas a ela."
			).format(len(dotacoes)))

	def on_trash(self):
		"""
		Ações ao excluir a unidade orçamentária:
		1. Verifica se há dotações orçamentárias vinculadas
		"""
		dotacoes = frappe.get_all(
			"DotacaoOrcamentaria",
			filters={"unidade_orcamentaria": self.name}
		)

		if dotacoes:
			frappe.throw(_(
				"Não é possível excluir esta unidade orçamentária pois existem {0} dotações orçamentárias vinculadas a ela."
			).format(len(dotacoes)))
