# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class ISSAtividade(Document):
    def validate(self):
        self.validate_aliquotas()
        self.validate_vigencia()
        self.validate_codigo_servico()

    def validate_aliquotas(self):
        """Valida as alíquotas configuradas"""
        if self.aliquota_padrao:
            if flt(self.aliquota_padrao) < 2.0:
                frappe.throw("Alíquota padrão não pode ser menor que 2%")
            if flt(self.aliquota_padrao) > 5.0:
                frappe.throw("Alíquota padrão não pode ser maior que 5%")
        
        if self.aliquota_minima and self.aliquota_maxima:
            if flt(self.aliquota_minima) > flt(self.aliquota_maxima):
                frappe.throw("Alíquota mínima não pode ser maior que a máxima")
        
        if self.aliquota_minima and flt(self.aliquota_minima) < 2.0:
            frappe.throw("Alíquota mínima não pode ser menor que 2%")
        
        if self.aliquota_maxima and flt(self.aliquota_maxima) > 5.0:
            frappe.throw("Alíquota máxima não pode ser maior que 5%")

    def validate_vigencia(self):
        """Valida período de vigência"""
        if self.data_vigencia_inicio and self.data_vigencia_fim:
            if getdate(self.data_vigencia_inicio) > getdate(self.data_vigencia_fim):
                frappe.throw("Data de início da vigência não pode ser maior que a data fim")

    def validate_codigo_servico(self):
        """Valida formato do código de serviço"""
        if self.codigo_servico:
            # Verifica se o código segue o padrão (XX.XX ou X.XX)
            import re
            if not re.match(r'^\d{1,2}\.\d{2}$', self.codigo_servico):
                frappe.throw("Código de serviço deve seguir o padrão XX.XX (ex: 01.01, 12.05)")

    def before_save(self):
        """Executa antes de salvar"""
        if not self.data_vigencia_inicio:
            self.data_vigencia_inicio = today()

    @frappe.whitelist()
    def get_prestadores_atividade(self):
        """Retorna prestadores que exercem esta atividade"""
        prestadores = frappe.get_all("ISS Atividade Item",
                                   filters={"atividade": self.name},
                                   fields=["parent as prestador"])
        
        return [p.prestador for p in prestadores]

    @frappe.whitelist()
    def calcular_arrecadacao_mensal(self, mes, ano):
        """Calcula arrecadação mensal da atividade"""
        prestadores = self.get_prestadores_atividade()
        
        if not prestadores:
            return {"total_servicos": 0, "total_iss": 0, "prestadores_count": 0}
        
        # Busca lançamentos da atividade no período
        lancamentos = frappe.get_all("ISS Lancamento",
                                   filters={
                                       "prestador": ["in", prestadores],
                                       "atividade": self.name,
                                       "mes_competencia": mes,
                                       "ano_competencia": ano,
                                       "docstatus": 1
                                   },
                                   fields=["valor_servicos", "valor_iss"])
        
        total_servicos = sum(flt(l.valor_servicos) for l in lancamentos)
        total_iss = sum(flt(l.valor_iss) for l in lancamentos)
        
        return {
            "total_servicos": total_servicos,
            "total_iss": total_iss,
            "prestadores_count": len(prestadores),
            "lancamentos_count": len(lancamentos)
        }

    def is_vigente(self, data=None):
        """Verifica se a atividade está vigente na data"""
        if not data:
            data = today()
        
        data_check = getdate(data)
        
        # Verifica início da vigência
        if self.data_vigencia_inicio and getdate(self.data_vigencia_inicio) > data_check:
            return False
        
        # Verifica fim da vigência
        if self.data_vigencia_fim and getdate(self.data_vigencia_fim) < data_check:
            return False
        
        # Verifica situação
        if self.situacao != "Ativo":
            return False
        
        return True

    @staticmethod
    def get_atividades_vigentes(data=None):
        """Retorna lista de atividades vigentes"""
        if not data:
            data = today()
        
        filters = {
            "situacao": "Ativo"
        }
        
        # Filtra por data de vigência
        date_filters = []
        date_filters.append(["data_vigencia_inicio", "<=", data])
        date_filters.append(["data_vigencia_fim", ">=", data])
        date_filters.append(["data_vigencia_fim", "is", "not set"])
        
        # Combina filtros com OR para data_vigencia_fim
        atividades = frappe.get_all("ISS Atividade",
                                  filters=filters,
                                  fields=["name", "codigo_servico", "descricao_servico", 
                                         "aliquota_padrao", "grupo_servico"])
        
        # Filtra manualmente as vigências
        atividades_vigentes = []
        for atividade in atividades:
            doc = frappe.get_doc("ISS Atividade", atividade.name)
            if doc.is_vigente(data):
                atividades_vigentes.append(atividade)
        
        return atividades_vigentes

    @frappe.whitelist()
    def duplicate_for_new_period(self, data_inicio, base_legal=None):
        """Duplica atividade para novo período"""
        # Finaliza atividade atual
        if not self.data_vigencia_fim:
            self.data_vigencia_fim = getdate(data_inicio).replace(day=1) - frappe.utils.datetime.timedelta(days=1)
            self.save()
        
        # Cria nova atividade
        new_atividade = frappe.copy_doc(self)
        new_atividade.data_vigencia_inicio = data_inicio
        new_atividade.data_vigencia_fim = None
        if base_legal:
            new_atividade.base_legal = base_legal
        
        new_atividade.insert()
        
        return new_atividade.name