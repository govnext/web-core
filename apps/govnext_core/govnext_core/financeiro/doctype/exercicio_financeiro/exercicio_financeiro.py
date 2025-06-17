# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class ExercicioFinanceiro(Document):
	"""
	Classe para gerenciar exercícios financeiros.

	O exercício financeiro representa o período fiscal do orçamento público,
	geralmente correspondente a um ano civil.
	"""

	def validate(self):
		"""
		Validações do exercício financeiro antes de salvar:
		1. Verifica se as datas são válidas
		2. Verifica se não há sobreposição com outros exercícios
		"""
		self.validar_datas()
		self.validar_sobreposicao()

	def validar_datas(self):
		"""
		Valida as datas do exercício financeiro:
		- Data de início deve ser anterior à data de fim
		- O período deve corresponder a um ano completo
		"""
		if not self.data_inicio or not self.data_fim:
			frappe.throw(_("As datas de início e fim são obrigatórias"))

		if self.data_inicio >= self.data_fim:
			frappe.throw(_("A data de início deve ser anterior à data de fim"))

		# Verifica se o período é de um ano
		data_inicio = datetime.datetime.strptime(str(self.data_inicio), '%Y-%m-%d')
		data_fim = datetime.datetime.strptime(str(self.data_fim), '%Y-%m-%d')

		diferenca = data_fim - data_inicio

		if diferenca.days < 364 or diferenca.days > 366:
			frappe.msgprint(
				_("Atenção: O exercício financeiro deve corresponder a um ano. O período definido é de {0} dias.").format(diferenca.days),
				indicator="orange",
				alert=True
			)

	def validar_sobreposicao(self):
		"""
		Verifica se há sobreposição com outros exercícios financeiros.
		"""
		exercicios = frappe.get_all(
			"ExercicioFinanceiro",
			filters={
				"name": ["!=", self.name] if self.name else "",
				"docstatus": ["<", 2]  # Não cancelados
			},
			fields=["name", "ano", "data_inicio", "data_fim"]
		)

		for exercicio in exercicios:
			if (self.data_inicio <= exercicio.data_fim and self.data_fim >= exercicio.data_inicio):
				frappe.throw(_(
					"Há sobreposição com o exercício financeiro {0} ({1}). "
					"O período de {2} a {3} se sobrepõe ao período definido."
				).format(
					exercicio.name,
					exercicio.ano,
					frappe.format_date(exercicio.data_inicio),
					frappe.format_date(exercicio.data_fim)
				))

	def on_submit(self):
		"""
		Ações ao submeter o exercício financeiro:
		1. Verifica se já existe um exercício ativo para o mesmo ano
		"""
		exercicios_ativos = frappe.get_all(
			"ExercicioFinanceiro",
			filters={
				"name": ["!=", self.name],
				"ano": self.ano,
				"status": "Ativo",
				"docstatus": 1
			}
		)

		if exercicios_ativos:
			frappe.throw(_("Já existe um exercício financeiro ativo para o ano {0}").format(self.ano))

	def before_save(self):
		"""
		Ações antes de salvar:
		1. Define o ano com base na data de início
		"""
		if self.data_inicio:
			self.ano = datetime.datetime.strptime(str(self.data_inicio), '%Y-%m-%d').year
