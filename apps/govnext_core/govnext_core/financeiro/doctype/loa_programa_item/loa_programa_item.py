# -*- coding: utf-8 -*-
# Copyright (c) 2025, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class LOAProgramaItem(Document):
	"""
	Child doctype para programas de governo na LOA
	Implementa a estrutura programática conforme metodologia do PPA
	"""
	
	def validate(self):
		"""Validações do programa de governo"""
		self.validar_codigo_programa()
		self.validar_dados_obrigatorios()
		self.validar_tipo_programa()
		self.calcular_valor_total()
		
	def validar_codigo_programa(self):
		"""Valida o código do programa conforme padrão"""
		if not self.codigo_programa:
			frappe.throw("Código do programa é obrigatório")
			
		# Código deve ter 4 dígitos
		if not self.codigo_programa.isdigit() or len(self.codigo_programa) != 4:
			frappe.throw("Código do programa deve ter 4 dígitos numéricos")
			
		# Verificar se não é um código reservado
		codigos_reservados = [
			"0001",  # Operações Especiais
			"0999",  # Reserva de Contingência
		]
		
		if self.codigo_programa in codigos_reservados:
			frappe.msgprint(
				f"Código {self.codigo_programa} é reservado para operações especiais",
				alert=True
			)
			
	def validar_dados_obrigatorios(self):
		"""Valida dados obrigatórios do programa"""
		if not self.nome_programa:
			frappe.throw("Nome do programa é obrigatório")
			
		if not self.objetivo_programa:
			frappe.throw("Objetivo do programa é obrigatório")
			
		if not self.orgao_responsavel:
			frappe.throw("Órgão responsável é obrigatório")
			
		# Validar formato do órgão responsável
		if not self.orgao_responsavel.isdigit() or len(self.orgao_responsavel) != 2:
			frappe.throw("Órgão responsável deve ter 2 dígitos numéricos")
			
	def validar_tipo_programa(self):
		"""Valida o tipo de programa conforme metodologia"""
		tipos_validos = ["Finalístico", "Apoio às Políticas Públicas", "Serviços ao Estado"]
		
		if self.tipo_programa not in tipos_validos:
			frappe.throw(f"Tipo de programa deve ser um dos: {', '.join(tipos_validos)}")
			
		# Orientações sobre tipos de programa
		if self.tipo_programa == "Finalístico":
			if not self.publico_alvo:
				frappe.msgprint(
					"Programas finalísticos devem ter público-alvo bem definido",
					alert=True
				)
		elif self.tipo_programa == "Serviços ao Estado":
			if "gestão" not in self.nome_programa.lower() and "administração" not in self.nome_programa.lower():
				frappe.msgprint(
					"Programas de Serviços ao Estado geralmente são de gestão/administração",
					alert=True
				)
				
	def calcular_valor_total(self):
		"""Calcula o valor total do programa somando suas ações"""
		total = 0
		if self.acoes_programa:
			for acao in self.acoes_programa:
				total += flt(acao.valor_acao)
		
		self.valor_total_programa = total
		
	def get_classificacao_tematica(self):
		"""Retorna a classificação temática baseada no código"""
		# Faixas de códigos por área temática (simplificado)
		codigo_num = int(self.codigo_programa)
		
		if 1000 <= codigo_num <= 1999:
			return "Agricultura, Pecuária e Pesca"
		elif 2000 <= codigo_num <= 2999:
			return "Assistência Social"
		elif 3000 <= codigo_num <= 3999:
			return "Comunicações"
		elif 4000 <= codigo_num <= 4999:
			return "Cultura"
		elif 5000 <= codigo_num <= 5999:
			return "Defesa Nacional"
		elif 6000 <= codigo_num <= 6999:
			return "Educação"
		elif 7000 <= codigo_num <= 7999:
			return "Energia"
		elif 8000 <= codigo_num <= 8999:
			return "Gestão Ambiental"
		elif 9000 <= codigo_num <= 9999:
			return "Saúde"
		else:
			return "Outros"