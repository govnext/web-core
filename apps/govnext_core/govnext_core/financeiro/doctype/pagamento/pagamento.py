# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class Pagamento(Document):
	"""
	Classe para gerenciar pagamentos no sistema de gestão financeira.

	O pagamento é o terceiro estágio da despesa orçamentária, onde ocorre
	a transferência de valores ao credor após a regular liquidação.
	"""

	def validate(self):
		"""
		Validações do pagamento antes de salvar:
		1. Verifica se a liquidação existe e tem saldo
		2. Valida os campos obrigatórios
		3. Valida o formato e consistência dos dados
		"""
		self.validar_liquidacao()
		self.validar_campos_obrigatorios()
		self.validar_datas()
		self.validar_valores()

	def on_submit(self):
		"""
		Ações ao submeter o pagamento:
		1. Atualiza o saldo da liquidação
		2. Cria registro no histórico de movimentações
		3. Gera número do pagamento
		4. Atualiza o status do empenho relacionado
		"""
		self.atualizar_saldo_liquidacao()
		self.criar_historico_movimento("Pagamento realizado")
		self.gerar_numero_pagamento()
		self.atualizar_status_empenho()

	def on_cancel(self):
		"""
		Ações ao cancelar o pagamento:
		1. Restaura o saldo da liquidação
		2. Registra o cancelamento no histórico
		3. Atualiza o status do empenho relacionado
		"""
		self.restaurar_saldo_liquidacao()
		self.criar_historico_movimento("Pagamento cancelado")
		self.atualizar_status_empenho(cancelado=True)

	def validar_liquidacao(self):
		"""
		Verifica se a liquidação existe e tem saldo suficiente para pagamento.
		"""
		if not self.liquidacao:
			frappe.throw(_("A liquidação é obrigatória para pagamento."))

		liquidacao = frappe.get_doc("Liquidacao", self.liquidacao)
		if not liquidacao:
			frappe.throw(_("Liquidação não encontrada."))

		# Verifica se a liquidação está aprovada
		if liquidacao.docstatus != 1:
			frappe.throw(_("A liquidação {0} não está aprovada.").format(self.liquidacao))

		# Verifica se há saldo suficiente na liquidação
		saldo_liquidacao = liquidacao.valor_total - liquidacao.valor_pago
		if saldo_liquidacao < self.valor_pagamento:
			frappe.throw(_(
				"Saldo insuficiente na liquidação para pagamento. "
				"Saldo disponível: {0}, Valor do pagamento: {1}"
			).format(
				frappe.format_value(saldo_liquidacao, {"fieldtype": "Currency"}),
				frappe.format_value(self.valor_pagamento, {"fieldtype": "Currency"})
			))

		# Preenche informações da liquidação
		self.empenho = liquidacao.empenho
		self.numero_empenho = liquidacao.numero_empenho
		self.dotacao_orcamentaria = liquidacao.dotacao_orcamentaria
		self.credor = liquidacao.credor
		self.nome_credor = liquidacao.nome_credor
		self.documento_credor = liquidacao.documento_credor

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"liquidacao", "data_pagamento", "valor_pagamento",
			"forma_pagamento", "conta_bancaria"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório").format(
					frappe.bold(self.meta.get_label(campo))
				))

	def validar_datas(self):
		"""
		Valida as datas do pagamento:
		1. Data do pagamento não pode ser maior que a data atual
		2. Data do pagamento deve ser posterior à data da liquidação
		"""
		hoje = datetime.date.today()

		# Data do pagamento não pode ser maior que hoje
		if self.data_pagamento and self.data_pagamento > hoje:
			frappe.throw(_("A data do pagamento não pode ser maior que a data atual"))

		# Verifica se a data do pagamento é posterior à data da liquidação
		if self.liquidacao:
			liquidacao = frappe.get_doc("Liquidacao", self.liquidacao)
			if self.data_pagamento < liquidacao.data_liquidacao:
				frappe.throw(_("A data do pagamento deve ser posterior à data da liquidação"))

	def validar_valores(self):
		"""
		Valida os valores do pagamento:
		1. Valor do pagamento deve ser maior que zero
		"""
		if not self.valor_pagamento > 0:
			frappe.throw(_("O valor do pagamento deve ser maior que zero"))

	def atualizar_saldo_liquidacao(self):
		"""
		Atualiza o saldo da liquidação após a criação do pagamento.
		"""
		liquidacao = frappe.get_doc("Liquidacao", self.liquidacao)
		liquidacao.valor_pago = (liquidacao.valor_pago or 0) + self.valor_pagamento

		# Atualiza o status da liquidação
		if liquidacao.valor_pago >= liquidacao.valor_total:
			liquidacao.status_liquidacao = "Pago"
		else:
			liquidacao.status_liquidacao = "Pago Parcialmente"

		liquidacao.save()

	def restaurar_saldo_liquidacao(self):
		"""
		Restaura o saldo da liquidação após o cancelamento do pagamento.
		"""
		liquidacao = frappe.get_doc("Liquidacao", self.liquidacao)
		liquidacao.valor_pago = (liquidacao.valor_pago or 0) - self.valor_pagamento

		# Atualiza o status da liquidação
		if liquidacao.valor_pago <= 0:
			liquidacao.valor_pago = 0
			liquidacao.status_liquidacao = "Liquidado"
		else:
			liquidacao.status_liquidacao = "Pago Parcialmente"

		liquidacao.save()

	def criar_historico_movimento(self, descricao):
		"""
		Cria um registro no histórico de movimentações financeiras.

		Args:
			descricao: Descrição da movimentação
		"""
		historico = frappe.new_doc("HistoricoMovimentacaoFinanceira")
		historico.update({
			"tipo_documento": "Pagamento",
			"documento_referencia": self.name,
			"descricao": descricao,
			"valor": self.valor_pagamento,
			"data_movimento": self.data_pagamento or datetime.date.today(),
			"usuario": frappe.session.user
		})
		historico.insert(ignore_permissions=True)

	def gerar_numero_pagamento(self):
		"""
		Gera o número sequencial do pagamento no formato NNNNNN/AAAA,
		onde NNNNNN é um número sequencial e AAAA é o ano do pagamento.
		"""
		if not self.numero_pagamento:
			ano = self.data_pagamento.year if self.data_pagamento else datetime.date.today().year

			# Busca o último número de pagamento do ano
			ultimo_pagamento = frappe.db.sql("""
				SELECT MAX(SUBSTRING_INDEX(numero_pagamento, '/', 1)) as numero
				FROM `tabPagamento`
				WHERE YEAR(data_pagamento) = %s
			""", (ano,), as_dict=True)

			ultimo_numero = int(ultimo_pagamento[0].numero or 0) if ultimo_pagamento else 0
			proximo_numero = ultimo_numero + 1

			self.numero_pagamento = f"{proximo_numero:06d}/{ano}"
			self.db_update()

	def atualizar_status_empenho(self, cancelado=False):
		"""
		Atualiza o status do empenho relacionado ao pagamento.

		Args:
			cancelado: Se True, o pagamento foi cancelado
		"""
		if not self.empenho:
			return

		empenho = frappe.get_doc("Empenho", self.empenho)
		liquidacao = frappe.get_doc("Liquidacao", self.liquidacao)

		# Busca todos os pagamentos relacionados à liquidação
		pagamentos = frappe.get_all(
			"Pagamento",
			filters={
				"empenho": self.empenho,
				"docstatus": 1
			},
			fields=["sum(valor_pagamento) as total_pago"]
		)

		total_pago = pagamentos[0].total_pago if pagamentos and pagamentos[0].total_pago else 0

		# Atualiza o valor pago no empenho
		empenho.valor_pago = total_pago

		# Atualiza o status do empenho
		if total_pago >= empenho.valor_total:
			empenho.status_empenho = "Pago"
		elif total_pago > 0:
			empenho.status_empenho = "Pago Parcialmente"
		elif empenho.valor_liquidado > 0:
			empenho.status_empenho = "Liquidado Parcialmente"
		else:
			empenho.status_empenho = "Emitido"

		empenho.save()
