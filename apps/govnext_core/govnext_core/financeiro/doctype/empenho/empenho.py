# -*- coding: utf-8 -*-
# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import datetime

class Empenho(Document):
	"""
	Classe para gerenciar empenhos no sistema de gestão financeira.

	O empenho é o primeiro estágio da despesa orçamentária, que cria
	para o Estado a obrigação de pagamento pendente.
	"""

	def validate(self):
		"""
		Validações do empenho antes de salvar:
		1. Verifica se a dotação orçamentária existe e tem saldo
		2. Valida os campos obrigatórios
		3. Valida o formato e consistência dos dados
		"""
		self.validar_dotacao_orcamentaria()
		self.validar_campos_obrigatorios()
		self.validar_datas()
		self.validar_valores()
		self.validar_itens_empenho()

	def on_submit(self):
		"""
		Ações ao submeter o empenho:
		1. Atualiza o saldo da dotação orçamentária
		2. Cria registro no histórico de movimentações
		3. Gera número do empenho
		"""
		self.atualizar_saldo_dotacao()
		self.criar_historico_movimento("Empenho criado")
		self.gerar_numero_empenho()
		self.db_set('status_empenho', 'Emitido')

	def on_cancel(self):
		"""
		Ações ao cancelar o empenho:
		1. Restaura o saldo da dotação orçamentária
		2. Registra o cancelamento no histórico
		"""
		self.restaurar_saldo_dotacao()
		self.criar_historico_movimento("Empenho cancelado")
		self.db_set('status_empenho', 'Cancelado')

	def validar_dotacao_orcamentaria(self):
		"""
		Verifica se a dotação orçamentária existe e tem saldo suficiente para empenho.
		"""
		if not self.dotacao_orcamentaria:
			frappe.throw(_("A dotação orçamentária é obrigatória para empenho."))

		dotacao = frappe.get_doc("DotacaoOrcamentaria", self.dotacao_orcamentaria)
		if not dotacao:
			frappe.throw(_("Dotação orçamentária não encontrada."))

		# Verifica se a dotação está ativa
		if dotacao.status != "Ativo":
			frappe.throw(_("A dotação orçamentária {0} não está ativa.").format(self.dotacao_orcamentaria))

		# Verifica se há saldo suficiente na dotação
		saldo_dotacao = dotacao.valor_disponivel - dotacao.valor_empenhado
		if saldo_dotacao < self.valor_total:
			frappe.throw(_(
				"Saldo insuficiente na dotação orçamentária para empenho. "
				"Saldo disponível: {0}, Valor do empenho: {1}"
			).format(
				frappe.format_value(saldo_dotacao, {"fieldtype": "Currency"}),
				frappe.format_value(self.valor_total, {"fieldtype": "Currency"})
			))

		# Preenche informações da dotação
		self.unidade_orcamentaria = dotacao.unidade_orcamentaria
		self.exercicio_financeiro = dotacao.exercicio_financeiro
		self.natureza_despesa = dotacao.natureza_despesa
		self.fonte_recurso = dotacao.fonte_recurso

	def validar_campos_obrigatorios(self):
		"""
		Valida se todos os campos obrigatórios foram preenchidos corretamente.
		"""
		campos_obrigatorios = [
			"dotacao_orcamentaria", "data_empenho", "tipo_empenho",
			"credor", "valor_total", "objeto"
		]

		for campo in campos_obrigatorios:
			if not self.get(campo):
				frappe.throw(_("O campo {0} é obrigatório").format(
					frappe.bold(self.meta.get_label(campo))
				))

		# Valida se há pelo menos um item para empenho ordinário ou global
		if self.tipo_empenho in ["Ordinário", "Global"] and (not self.itens_empenho or len(self.itens_empenho) == 0):
			frappe.throw(_("É necessário informar pelo menos um item para empenho do tipo {0}").format(self.tipo_empenho))

	def validar_datas(self):
		"""
		Valida as datas do empenho:
		1. Data do empenho não pode ser maior que a data atual
		2. Data do empenho deve estar dentro do exercício financeiro
		"""
		hoje = datetime.date.today()

		# Data do empenho não pode ser maior que hoje
		if self.data_empenho and self.data_empenho > hoje:
			frappe.throw(_("A data do empenho não pode ser maior que a data atual"))

		# Verifica se a data está dentro do exercício financeiro
		if self.exercicio_financeiro:
			exercicio = frappe.get_doc("ExercicioFinanceiro", self.exercicio_financeiro)
			if self.data_empenho < exercicio.data_inicio or self.data_empenho > exercicio.data_fim:
				frappe.throw(_("A data do empenho deve estar dentro do período do exercício financeiro"))

	def validar_valores(self):
		"""
		Valida os valores do empenho:
		1. Valor total deve ser maior que zero
		2. Valor total deve ser igual à soma dos itens
		"""
		if not self.valor_total > 0:
			frappe.throw(_("O valor total do empenho deve ser maior que zero"))

		# Se houver itens, verifica se o valor total é igual à soma dos itens
		if self.itens_empenho and len(self.itens_empenho) > 0:
			soma_itens = sum(item.valor_total for item in self.itens_empenho)
			if abs(soma_itens - self.valor_total) > 0.01:  # Pequena tolerância para arredondamentos
				frappe.throw(_(
					"O valor total do empenho ({0}) deve ser igual à soma dos itens ({1})"
				).format(
					frappe.format_value(self.valor_total, {"fieldtype": "Currency"}),
					frappe.format_value(soma_itens, {"fieldtype": "Currency"})
				))

	def validar_itens_empenho(self):
		"""
		Valida os itens do empenho:
		1. Para empenho estimativo, não deve haver itens
		2. Para empenho ordinário, deve haver itens com quantidade e valor unitário
		3. Para empenho global, deve haver itens com quantidade e valor unitário
		"""
		if self.tipo_empenho == "Estimativo" and self.itens_empenho and len(self.itens_empenho) > 0:
			frappe.throw(_("Empenho do tipo Estimativo não deve conter itens detalhados"))

		if self.tipo_empenho == "Ordinário":
			for item in self.itens_empenho:
				if not item.quantidade or not item.valor_unitario:
					frappe.throw(_("Para empenho Ordinário, todos os itens devem ter quantidade e valor unitário"))

		if self.tipo_empenho == "Global":
			for item in self.itens_empenho:
				if not item.quantidade or not item.valor_unitario:
					frappe.throw(_("Para empenho Global, todos os itens devem ter quantidade e valor unitário"))

	def atualizar_saldo_dotacao(self):
		"""
		Atualiza o saldo da dotação orçamentária após a criação do empenho.
		"""
		dotacao = frappe.get_doc("DotacaoOrcamentaria", self.dotacao_orcamentaria)
		dotacao.valor_empenhado = (dotacao.valor_empenhado or 0) + self.valor_total
		dotacao.save()

	def restaurar_saldo_dotacao(self):
		"""
		Restaura o saldo da dotação orçamentária após o cancelamento do empenho.
		"""
		dotacao = frappe.get_doc("DotacaoOrcamentaria", self.dotacao_orcamentaria)
		dotacao.valor_empenhado = (dotacao.valor_empenhado or 0) - self.valor_total

		# Garante que o valor empenhado não fique negativo
		if dotacao.valor_empenhado < 0:
			dotacao.valor_empenhado = 0

		dotacao.save()

	def criar_historico_movimento(self, descricao):
		"""
		Cria um registro no histórico de movimentações financeiras.

		Args:
			descricao: Descrição da movimentação
		"""
		historico = frappe.new_doc("HistoricoMovimentacaoFinanceira")
		historico.update({
			"tipo_documento": "Empenho",
			"documento_referencia": self.name,
			"descricao": descricao,
			"valor": self.valor_total,
			"data_movimento": self.data_empenho or datetime.date.today(),
			"usuario": frappe.session.user
		})
		historico.insert(ignore_permissions=True)

	def gerar_numero_empenho(self):
		"""
		Gera o número sequencial do empenho no formato NNNNNN/AAAA,
		onde NNNNNN é um número sequencial e AAAA é o ano do empenho.
		"""
		if not self.numero_empenho:
			ano = self.data_empenho.year if self.data_empenho else datetime.date.today().year

			# Busca o último número de empenho do ano
			ultimo_empenho = frappe.db.sql("""
				SELECT MAX(SUBSTRING_INDEX(numero_empenho, '/', 1)) as numero
				FROM `tabEmpenho`
				WHERE YEAR(data_empenho) = %s
			""", (ano,), as_dict=True)

			ultimo_numero = int(ultimo_empenho[0].numero or 0) if ultimo_empenho else 0
			proximo_numero = ultimo_numero + 1

			self.numero_empenho = f"{proximo_numero:06d}/{ano}"
			self.db_update()
