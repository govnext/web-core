# -*- coding: utf-8 -*-
# Copyright (c) 2025, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_months
from datetime import datetime

class LeiDiretrizesOrcamentarias(Document):
	"""
	Doctype para Lei de Diretrizes Orçamentárias (LDO)
	Implementa as regras da Lei de Responsabilidade Fiscal
	"""
	
	def validate(self):
		"""Validações específicas da LDO"""
		self.validar_exercicio_financeiro()
		self.validar_metas_fiscais()
		self.validar_anexos_obrigatorios()
		self.validar_limites_lrf()
		
	def before_save(self):
		"""Processamento antes de salvar"""
		self.atualizar_status()
		self.validar_prazos_lrf()
		
	def on_submit(self):
		"""Ao submeter a LDO"""
		self.criar_parametros_orcamentarios()
		self.notificar_usuarios()
		
	def validar_exercicio_financeiro(self):
		"""Valida se o exercício financeiro está correto"""
		if not self.ano_exercicio:
			frappe.throw("Ano do exercício é obrigatório")
			
		# A LDO deve ser aprovada até 15 de julho do ano anterior
		ano_atual = datetime.now().year
		if self.ano_exercicio <= ano_atual:
			frappe.throw(f"LDO deve ser para exercício futuro (ano {ano_atual + 1} ou posterior)")
			
		# Verificar se já existe LDO para o mesmo exercício
		if self.is_new():
			existing_ldo = frappe.db.exists("Lei Diretrizes Orcamentarias", {
				"ano_exercicio": self.ano_exercicio,
				"status": ["in", ["Aprovada", "Sancionada", "Promulgada", "Vigente"]],
				"name": ["!=", self.name]
			})
			if existing_ldo:
				frappe.throw(f"Já existe LDO aprovada para o exercício {self.ano_exercicio}")
	
	def validar_metas_fiscais(self):
		"""Valida as metas fiscais obrigatórias"""
		if not self.metas_fiscais:
			frappe.throw("Metas fiscais são obrigatórias conforme art. 4º da LRF")
			
		# Verificar se as metas mínimas estão presentes
		metas_obrigatorias = [
			"Resultado Primário",
			"Resultado Nominal", 
			"Dívida Pública Líquida",
			"Receitas Primárias",
			"Despesas Primárias"
		]
		
		metas_informadas = [meta.tipo_meta for meta in self.metas_fiscais]
		
		for meta_obrigatoria in metas_obrigatorias:
			if meta_obrigatoria not in metas_informadas:
				frappe.throw(f"Meta fiscal '{meta_obrigatoria}' é obrigatória")
				
		# Validar consistência das metas
		for meta in self.metas_fiscais:
			if meta.tipo_meta == "Dívida Pública Líquida":
				# Verificar limite de 200% da RCL para municípios
				if flt(meta.valor_meta) > 200:  # Assumindo valor em % da RCL
					frappe.msgprint(
						"Meta da dívida pública líquida excede 200% da RCL (limite municipal)",
						alert=True
					)
	
	def validar_anexos_obrigatorios(self):
		"""Valida se os anexos obrigatórios estão presentes"""
		if not self.anexo_metas_fiscais:
			frappe.throw("Anexo de Metas Fiscais é obrigatório (art. 4º LRF)")
			
		if not self.anexo_riscos_fiscais:
			frappe.throw("Anexo de Riscos Fiscais é obrigatório (art. 4º LRF)")
	
	def validar_limites_lrf(self):
		"""Valida os limites da Lei de Responsabilidade Fiscal"""
		if self.limite_despesa_pessoal:
			# Limite máximo: 60% da RCL (com alerta em 54% - limite prudencial)
			if flt(self.limite_despesa_pessoal) > 60:
				frappe.throw("Limite de despesa com pessoal não pode exceder 60% da RCL")
			elif flt(self.limite_despesa_pessoal) > 54:
				frappe.msgprint(
					"Limite de despesa com pessoal excede 54% da RCL (limite prudencial)",
					alert=True
				)
				
		if self.limite_endividamento:
			# Alertar sobre limites de endividamento
			frappe.msgprint(
				"Verificar compatibilidade do limite de endividamento com Resolução SF 40/2001",
				alert=True
			)
	
	def validar_prazos_lrf(self):
		"""Valida os prazos estabelecidos na LRF"""
		if self.data_promulgacao:
			# LDO deve ser promulgada até 15 de julho
			data_limite = datetime(self.ano_exercicio - 1, 7, 15).date()
			if getdate(self.data_promulgacao) > data_limite:
				frappe.msgprint(
					f"LDO deveria ter sido promulgada até 15/7/{self.ano_exercicio - 1} (art. 35 ADCT)",
					alert=True
				)
	
	def atualizar_status(self):
		"""Atualiza o status conforme o ciclo de aprovação"""
		if self.data_promulgacao and self.status not in ["Promulgada", "Vigente", "Encerrada"]:
			self.status = "Promulgada"
			
		# Se está no período de vigência
		if (self.data_vigencia_inicio and self.data_vigencia_fim and 
			getdate() >= getdate(self.data_vigencia_inicio) and 
			getdate() <= getdate(self.data_vigencia_fim)):
			self.status = "Vigente"
			
		# Se passou do período de vigência
		if (self.data_vigencia_fim and 
			getdate() > getdate(self.data_vigencia_fim)):
			self.status = "Encerrada"
	
	def criar_parametros_orcamentarios(self):
		"""Cria parâmetros orçamentários baseados na LDO"""
		# Criar configurações para o exercício
		parametros = frappe.new_doc("Parametros Orcamentarios")
		parametros.update({
			"ano_exercicio": self.ano_exercicio,
			"ldo_referencia": self.name,
			"limite_despesa_pessoal": self.limite_despesa_pessoal,
			"limite_endividamento": self.limite_endividamento
		})
		
		try:
			parametros.insert()
			frappe.msgprint(f"Parâmetros orçamentários criados para {self.ano_exercicio}")
		except:
			pass  # Parâmetros já podem existir
	
	def notificar_usuarios(self):
		"""Notifica usuários sobre aprovação da LDO"""
		usuarios_financeiro = frappe.get_all("Has Role", 
			filters={"role": "Gestor Financeiro"}, 
			fields=["parent"]
		)
		
		for usuario in usuarios_financeiro:
			frappe.share.add("Lei Diretrizes Orcamentarias", self.name, usuario.parent, read=1)
			
		frappe.msgprint(f"LDO compartilhada com {len(usuarios_financeiro)} usuários do financeiro")
	
	def get_metas_resumo(self):
		"""Retorna resumo das metas fiscais"""
		if not self.metas_fiscais:
			return {}
			
		resumo = {}
		for meta in self.metas_fiscais:
			resumo[meta.tipo_meta] = {
				"valor": meta.valor_meta,
				"unidade": meta.unidade_medida,
				"justificativa": meta.justificativa
			}
		
		return resumo
	
	def get_prioridades_por_area(self):
		"""Retorna prioridades agrupadas por área"""
		if not self.prioridades_governo:
			return {}
			
		areas = {}
		for prioridade in self.prioridades_governo:
			area = prioridade.area_governo
			if area not in areas:
				areas[area] = []
			areas[area].append({
				"descricao": prioridade.descricao_prioridade,
				"valor": prioridade.valor_previsto,
				"prazo": prioridade.prazo_execucao
			})
		
		return areas

@frappe.whitelist()
def get_ldo_vigente(ano_exercicio=None):
	"""Retorna a LDO vigente para o exercício"""
	if not ano_exercicio:
		ano_exercicio = datetime.now().year + 1
		
	ldo = frappe.get_value("Lei Diretrizes Orcamentarias", 
		{"ano_exercicio": ano_exercicio, "status": "Vigente"}, 
		["name", "numero_lei"])
	
	return ldo

@frappe.whitelist()
def verificar_compatibilidade_ppa(ano_exercicio):
	"""Verifica se LDO está compatível com PPA"""
	ldo = frappe.get_doc("Lei Diretrizes Orcamentarias", {"ano_exercicio": ano_exercicio})
	ppa = frappe.get_value("Plano Plurianual", 
		{"ano_inicio": ["<=", ano_exercicio], "ano_fim": [">=", ano_exercicio]}, 
		["name", "programas_estrategicos"])
	
	if not ppa:
		return {"compativel": False, "motivo": "PPA não encontrado para o período"}
	
	# Implementar lógica de verificação de compatibilidade
	return {"compativel": True, "ppa_referencia": ppa}