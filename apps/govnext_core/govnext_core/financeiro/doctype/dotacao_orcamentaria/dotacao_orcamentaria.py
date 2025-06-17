# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class DotacaoOrcamentaria(Document):
	"""
	Classe para gerenciar dotações orçamentárias.

	A dotação orçamentária representa o valor autorizado para determinada
	despesa no orçamento público.
	"""

	def validate(self):
		"""
		Validações da dotação orçamentária antes de salvar:
		1. Verifica se os valores são positivos
		2. Valida os campos obrigatórios
		3. Verifica se a dotação é compatível com o orçamento
		"""
		self.validar_valores()
		self.calcular_saldo_disponivel()
		self.validar_campos_obrigatorios()
		self.validar_compatibilidade_orcamento()

	def on_submit(self):
		"""
		Ações ao submeter a dotação orçamentária:
		1. Registra no histórico de movimentações
		2. Atualiza valores do orçamento relacionado
		"""
		self.criar_historico_movimento("Dotação orçamentária aprovada")
		self.atualizar_orcamento()

	def on_cancel(self):
		"""
		Ações ao cancelar a dotação orçamentária:
		1. Registra o cancelamento no histórico
		2. Reverte valores no orçamento
		"""
		self.criar_historico_movimento("Dotação orçamentária cancelada")
		self.reverter_valores_orcamento()

	def validar_valores(self):
		"""
		Verifica se os valores da dotação são positivos.
		"""
		if self.valor_inicial <= 0:
			frappe.throw(_("O valor inicial da dotação deve ser maior que zero"))

		# Se houver suplementação, verifica se é positiva
		if self.valor_suplementado and self.valor_suplementado < 0:
			frappe.throw(_("O valor de suplementação não pode ser negativo"))

		# Se houver anulação, verifica se é positiva
		if self.valor_anulado and self.valor_anulado < 0:
			frappe.throw(_("O valor de anulação não pode ser negativo"))

	def calcular_saldo_disponivel(self):
		"""
		Calcula o saldo disponível da dotação baseado nos valores de:
		- Valor inicial
		- Valor suplementado
		- Valor anulado
		- Valor empenhado
		"""
		# Calcula o valor total da dotação
		self.valor_total = (self.valor_inicial or 0) + (self.valor_suplementado or 0) - (self.valor_anulado or 0)

		# Calcula o saldo disponível
		self.saldo_disponivel = self.valor_total - (self.valor_empenhado or 0) - (self.valor_bloqueado or 0)

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"exercicio_financeiro", "unidade_orcamentaria", "programa",
			"acao", "natureza_despesa", "valor_inicial"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório").format(
					frappe.bold(self.meta.get_label(campo))
				))

	def validar_compatibilidade_orcamento(self):
		"""
		Verifica se a dotação é compatível com o orçamento do exercício.
		- Verifica se as classificações orçamentárias estão corretas
		- Verifica se há previsão no orçamento
		"""
		orcamento = frappe.get_doc(
			"Orcamento",
			{"exercicio_financeiro": self.exercicio_financeiro, "docstatus": 1}
		)

		if not orcamento:
			frappe.throw(_("Não existe orçamento aprovado para o exercício financeiro {0}").format(
				self.exercicio_financeiro
			))

		# Verifica se a unidade orçamentária está no orçamento
		unidade_encontrada = False
		for unid in orcamento.unidades_orcamentarias:
			if unid.unidade_orcamentaria == self.unidade_orcamentaria:
				unidade_encontrada = True
				break

		if not unidade_encontrada:
			frappe.throw(_("A unidade orçamentária {0} não está prevista no orçamento do exercício {1}").format(
				self.unidade_orcamentaria, self.exercicio_financeiro
			))

	def atualizar_orcamento(self):
		"""
		Atualiza os valores do orçamento após aprovar a dotação.
		"""
		# Implementar lógica de atualização do orçamento
		pass

	def reverter_valores_orcamento(self):
		"""
		Reverte os valores do orçamento após cancelar a dotação.
		"""
		# Implementar lógica de reversão de valores do orçamento
		pass

	def criar_historico_movimento(self, descricao):
		"""
		Cria um registro no histórico de movimentações orçamentárias.

		Args:
			descricao: Descrição da movimentação
		"""
		historico = frappe.new_doc("HistoricoMovimentacaoOrcamentaria")
		historico.update({
			"tipo_documento": "Dotação Orçamentária",
			"documento_referencia": self.name,
			"descricao": descricao,
			"valor": self.valor_total,
			"data_movimento": datetime.date.today(),
			"usuario": frappe.session.user,
			"exercicio_financeiro": self.exercicio_financeiro,
			"unidade_orcamentaria": self.unidade_orcamentaria
		})
		historico.insert(ignore_permissions=True)
