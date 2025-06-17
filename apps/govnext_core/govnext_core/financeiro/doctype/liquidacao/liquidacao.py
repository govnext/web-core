# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class Liquidacao(Document):
	"""
	Classe para gerenciar liquidações no sistema de gestão financeira.

	A liquidação é o segundo estágio da despesa orçamentária, onde se verifica
	o direito adquirido pelo credor com base em documentos comprobatórios.
	"""

	def validate(self):
		"""
		Validações da liquidação antes de salvar:
		1. Verifica se o empenho existe e tem saldo
		2. Valida os campos obrigatórios
		3. Valida o formato e consistência dos dados
		"""
		self.validar_empenho()
		self.validar_campos_obrigatorios()
		self.validar_datas()
		self.calcular_valores_totais()

	def on_submit(self):
		"""
		Ações ao submeter a liquidação:
		1. Atualiza o saldo do empenho
		2. Cria registro no histórico de movimentações
		3. Gera número da liquidação
		"""
		self.atualizar_saldo_empenho()
		self.criar_historico_movimento("Liquidação criada")
		self.gerar_numero_liquidacao()

	def on_cancel(self):
		"""
		Ações ao cancelar a liquidação:
		1. Restaura o saldo do empenho
		2. Registra o cancelamento no histórico
		"""
		self.restaurar_saldo_empenho()
		self.criar_historico_movimento("Liquidação cancelada")

	def validar_empenho(self):
		"""
		Verifica se o empenho existe e tem saldo suficiente para liquidação.
		"""
		if not self.empenho:
			frappe.throw(_("O empenho é obrigatório para liquidação."))

		empenho = frappe.get_doc("Empenho", self.empenho)
		if not empenho:
			frappe.throw(_("Empenho não encontrado."))

		# Verifica se o empenho está aprovado
		if empenho.docstatus != 1:
			frappe.throw(_("O empenho {0} não está aprovado.").format(self.empenho))

		# Verifica se há saldo suficiente no empenho
		saldo_empenho = empenho.valor_total - empenho.valor_liquidado
		if saldo_empenho < self.valor_total:
			frappe.throw(_(
				"Saldo insuficiente no empenho para liquidação. "
				"Saldo disponível: {0}, Valor da liquidação: {1}"
			).format(
				frappe.format_value(saldo_empenho, {"fieldtype": "Currency"}),
				frappe.format_value(self.valor_total, {"fieldtype": "Currency"})
			))

		# Preenche informações do empenho
		self.dotacao_orcamentaria = empenho.dotacao_orcamentaria
		self.credor = empenho.credor
		self.nome_credor = empenho.nome_credor
		self.documento_credor = empenho.documento_credor

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"empenho", "data_liquidacao", "valor_total", "documentos_fiscais"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório").format(
					frappe.bold(self.meta.get_label(campo))
				))

		# Valida se há pelo menos um documento fiscal
		if not self.documentos_fiscais or len(self.documentos_fiscais) == 0:
			frappe.throw(_("É necessário informar pelo menos um documento fiscal para liquidação"))

	def validar_datas(self):
		"""
		Valida as datas da liquidação:
		1. Data da liquidação não pode ser maior que a data atual
		2. Data da liquidação deve ser posterior à data do empenho
		"""
		hoje = datetime.date.today()

		# Data da liquidação não pode ser maior que hoje
		if self.data_liquidacao and self.data_liquidacao > hoje:
			frappe.throw(_("A data da liquidação não pode ser maior que a data atual"))

		# Verifica se a data da liquidação é posterior à data do empenho
		if self.empenho:
			empenho = frappe.get_doc("Empenho", self.empenho)
			if self.data_liquidacao < empenho.data_empenho:
				frappe.throw(_("A data da liquidação deve ser posterior à data do empenho"))

	def calcular_valores_totais(self):
		"""
		Calcula valores totais da liquidação com base nos documentos fiscais.
		"""
		self.valor_total = sum(doc.valor for doc in self.documentos_fiscais)

		if not self.valor_total > 0:
			frappe.throw(_("O valor total da liquidação deve ser maior que zero"))

	def atualizar_saldo_empenho(self):
		"""
		Atualiza o saldo do empenho após a criação da liquidação.
		"""
		empenho = frappe.get_doc("Empenho", self.empenho)
		empenho.valor_liquidado = (empenho.valor_liquidado or 0) + self.valor_total

		# Atualiza o status do empenho
		if empenho.valor_liquidado >= empenho.valor_total:
			empenho.status_empenho = "Liquidado"
		else:
			empenho.status_empenho = "Liquidado Parcialmente"

		empenho.save()

	def restaurar_saldo_empenho(self):
		"""
		Restaura o saldo do empenho após o cancelamento da liquidação.
		"""
		empenho = frappe.get_doc("Empenho", self.empenho)
		empenho.valor_liquidado = (empenho.valor_liquidado or 0) - self.valor_total

		# Atualiza o status do empenho
		if empenho.valor_liquidado <= 0:
			empenho.valor_liquidado = 0
			empenho.status_empenho = "Emitido"
		else:
			empenho.status_empenho = "Liquidado Parcialmente"

		empenho.save()

	def criar_historico_movimento(self, descricao):
		"""
		Cria um registro no histórico de movimentações financeiras.

		Args:
			descricao: Descrição da movimentação
		"""
		historico = frappe.new_doc("HistoricoMovimentacaoFinanceira")
		historico.update({
			"tipo_documento": "Liquidacao",
			"documento_referencia": self.name,
			"descricao": descricao,
			"valor": self.valor_total,
			"data_movimento": self.data_liquidacao or datetime.date.today(),
			"usuario": frappe.session.user
		})
		historico.insert(ignore_permissions=True)

	def gerar_numero_liquidacao(self):
		"""
		Gera o número sequencial da liquidação no formato NNNNNN/AAAA,
		onde NNNNNN é um número sequencial e AAAA é o ano da liquidação.
		"""
		if not self.numero_liquidacao:
			ano = self.data_liquidacao.year if self.data_liquidacao else datetime.date.today().year

			# Busca o último número de liquidação do ano
			ultimo_liquidacao = frappe.db.sql("""
				SELECT MAX(SUBSTRING_INDEX(numero_liquidacao, '/', 1)) as numero
				FROM `tabLiquidacao`
				WHERE YEAR(data_liquidacao) = %s
			""", (ano,), as_dict=True)

			ultimo_numero = int(ultimo_liquidacao[0].numero or 0) if ultimo_liquidacao else 0
			proximo_numero = ultimo_numero + 1

			self.numero_liquidacao = f"{proximo_numero:06d}/{ano}"
			self.db_update()
