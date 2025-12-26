# -*- coding: utf-8 -*-
# Copyright (c) 2025, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_years
from datetime import datetime

class PlanoPlurianual(Document):
	"""
	Doctype para Plano Plurianual (PPA)
	Implementa as regras constitucionais e da Lei de Responsabilidade Fiscal
	"""
	
	def validate(self):
		"""Validações específicas do PPA"""
		self.validar_periodo_quadrienio()
		self.validar_compatibilidade_constitucional()
		self.validar_programas_obrigatorios()
		self.calcular_totais()
		
	def before_save(self):
		"""Processamento antes de salvar"""
		self.atualizar_status()
		self.validar_prazos_constitucionais()
		
	def on_submit(self):
		"""Ao submeter o PPA"""
		self.validar_consistencia_temporal()
		self.criar_base_programatica()
		
	def validar_periodo_quadrienio(self):
		"""Valida se o período é um quadriênio válido"""
		if not self.ano_inicio or not self.ano_fim:
			frappe.throw("Anos de início e fim são obrigatórios")
			
		# Deve ser exatamente 4 anos
		if (self.ano_fim - self.ano_inicio + 1) != 4:
			frappe.throw("PPA deve compreender exatamente 4 anos")
			
		# Validar se é o período correto do mandato
		# PPA vai do 2º ao 5º ano do mandato (anos ímpares)
		if self.ano_inicio % 4 != 2:  # 2022, 2026, 2030, etc.
			frappe.msgprint(
				f"PPA normalmente inicia no 2º ano do mandato. Verificar se {self.ano_inicio} está correto.",
				alert=True
			)
			
		# Verificar se já existe PPA para o período
		if self.is_new():
			existing_ppa = frappe.db.exists("Plano Plurianual", {
				"ano_inicio": self.ano_inicio,
				"ano_fim": self.ano_fim,
				"status": ["in", ["Aprovado", "Sancionado", "Promulgado", "Vigente"]],
				"name": ["!=", self.name]
			})
			if existing_ppa:
				frappe.throw(f"Já existe PPA aprovado para o período {self.ano_inicio}-{self.ano_fim}")
	
	def validar_compatibilidade_constitucional(self):
		"""Valida compatibilidade com dispositivos constitucionais"""
		if not self.diretrizes_estrategicas:
			frappe.throw("Diretrizes estratégicas são obrigatórias (art. 165, §1º CF)")
			
		if not self.objetivos_estrategicos:
			frappe.throw("Objetivos estratégicos são obrigatórios")
			
		# Validar áreas mínimas de atuação
		areas_obrigatorias = [
			"Saúde", "Educação", "Assistência Social", "Segurança Pública",
			"Infraestrutura", "Meio Ambiente"
		]
		
		areas_contempladas = []
		if self.programas_estrategicos:
			for programa in self.programas_estrategicos:
				if programa.area_tematica:
					areas_contempladas.append(programa.area_tematica)
		
		areas_faltantes = set(areas_obrigatorias) - set(areas_contempladas)
		if areas_faltantes:
			frappe.msgprint(
				f"Considerar incluir programas nas áreas: {', '.join(areas_faltantes)}",
				alert=True
			)
	
	def validar_programas_obrigatorios(self):
		"""Valida se programas obrigatórios estão incluídos"""
		if not self.programas_estrategicos:
			frappe.throw("Pelo menos um programa estratégico deve ser incluído")
			
		# Verificar se existem programas com recursos significativos
		total_com_recursos = 0
		for programa in self.programas_estrategicos:
			if flt(programa.valor_total) > 0:
				total_com_recursos += 1
				
		if total_com_recursos == 0:
			frappe.throw("Pelo menos um programa deve ter recursos financeiros definidos")
	
	def calcular_totais(self):
		"""Calcula os totais do PPA"""
		total_recursos = 0
		
		if self.programas_estrategicos:
			for programa in self.programas_estrategicos:
				total_recursos += flt(programa.valor_total)
		
		self.total_recursos_programas = total_recursos
	
	def validar_prazos_constitucionais(self):
		"""Valida os prazos constitucionais"""
		if self.data_promulgacao:
			# PPA deve ser aprovado até final do primeiro ano do mandato
			ano_limite = self.ano_inicio - 1  # Ano anterior ao início
			data_limite = datetime(ano_limite, 12, 31).date()
			
			if getdate(self.data_promulgacao) > data_limite:
				frappe.msgprint(
					f"PPA deveria ter sido promulgado até 31/12/{ano_limite} (art. 35 ADCT)",
					alert=True
				)
	
	def atualizar_status(self):
		"""Atualiza o status conforme o ciclo de aprovação"""
		if self.data_promulgacao and self.status not in ["Promulgado", "Vigente", "Encerrado"]:
			self.status = "Promulgado"
			
		# Se está no período de vigência
		ano_atual = datetime.now().year
		if self.ano_inicio <= ano_atual <= self.ano_fim:
			self.status = "Vigente"
		elif ano_atual > self.ano_fim:
			self.status = "Encerrado"
	
	def validar_consistencia_temporal(self):
		"""Valida consistência temporal com LDO e LOA"""
		# Verificar se há LDO compatível
		ldo_compativel = frappe.db.exists("Lei Diretrizes Orcamentarias", {
			"ano_exercicio": ["between", [self.ano_inicio, self.ano_fim]],
			"status": ["in", ["Aprovada", "Vigente"]]
		})
		
		if not ldo_compativel:
			frappe.msgprint(
				"Não há LDO vigente compatível com o período do PPA",
				alert=True
			)
	
	def criar_base_programatica(self):
		"""Cria base programática para LOAs futuras"""
		if not self.programas_estrategicos:
			return
			
		programas_criados = 0
		for programa in self.programas_estrategicos:
			# Verificar se programa já existe
			programa_existente = frappe.db.exists("Programa Governo", {
				"codigo_programa": programa.codigo_programa
			})
			
			if not programa_existente:
				novo_programa = frappe.new_doc("Programa Governo")
				novo_programa.update({
					"codigo_programa": programa.codigo_programa,
					"nome_programa": programa.nome_programa,
					"tipo_programa": programa.tipo_programa,
					"area_tematica": programa.area_tematica,
					"objetivo_programa": programa.objetivo_programa,
					"periodo_vigencia_inicio": self.ano_inicio,
					"periodo_vigencia_fim": self.ano_fim,
					"ppa_origem": self.name
				})
				novo_programa.insert()
				programas_criados += 1
		
		if programas_criados > 0:
			frappe.msgprint(f"Criados {programas_criados} programas na base programática")
	
	def get_programas_por_area(self):
		"""Retorna programas agrupados por área temática"""
		if not self.programas_estrategicos:
			return {}
			
		areas = {}
		for programa in self.programas_estrategicos:
			area = programa.area_tematica or "Outras"
			if area not in areas:
				areas[area] = []
			areas[area].append({
				"codigo": programa.codigo_programa,
				"nome": programa.nome_programa,
				"valor": programa.valor_total,
				"tipo": programa.tipo_programa
			})
		
		return areas
	
	def get_evolucao_recursos(self):
		"""Retorna evolução dos recursos por ano"""
		if not self.projecoes_fiscais:
			return {}
			
		evolucao = {}
		for projecao in self.projecoes_fiscais:
			evolucao[projecao.ano] = {
				"receita": projecao.receita_total,
				"despesa": projecao.despesa_total,
				"resultado": projecao.resultado_primario
			}
		
		return evolucao
	
	def get_indicadores_principais(self):
		"""Retorna indicadores principais do PPA"""
		if not self.indicadores_estrategicos:
			return []
			
		indicadores = []
		for indicador in self.indicadores_estrategicos:
			indicadores.append({
				"nome": indicador.nome_indicador,
				"valor_atual": indicador.valor_atual,
				"meta_final": indicador.meta_final,
				"unidade": indicador.unidade_medida,
				"periodicidade": indicador.periodicidade_apuracao
			})
		
		return indicadores

@frappe.whitelist()
def get_ppa_vigente(ano_referencia=None):
	"""Retorna o PPA vigente para determinado ano"""
	if not ano_referencia:
		ano_referencia = datetime.now().year
		
	ppa = frappe.get_value("Plano Plurianual", {
		"ano_inicio": ["<=", ano_referencia],
		"ano_fim": [">=", ano_referencia],
		"status": "Vigente"
	}, ["name", "numero_lei", "ano_inicio", "ano_fim"])
	
	return ppa

@frappe.whitelist()
def get_programas_ppa(ppa_name):
	"""Retorna programas de um PPA específico"""
	ppa = frappe.get_doc("Plano Plurianual", ppa_name)
	
	if not ppa.programas_estrategicos:
		return []
		
	programas = []
	for programa in ppa.programas_estrategicos:
		programas.append({
			"codigo": programa.codigo_programa,
			"nome": programa.nome_programa,
			"area": programa.area_tematica,
			"valor": programa.valor_total,
			"tipo": programa.tipo_programa
		})
	
	return programas