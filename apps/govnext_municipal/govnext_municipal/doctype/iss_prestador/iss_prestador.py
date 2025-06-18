# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import validate_email_address, cint, flt
import re


class ISSPrestador(Document):
    def validate(self):
        self.validate_cnpj_cpf()
        self.validate_inscricao_municipal()
        self.validate_email()
        self.validate_responsavel_data()
        self.calculate_aliquota_iss()
        self.validate_beneficio_fiscal()

    def validate_cnpj_cpf(self):
        """Valida CNPJ/CPF do prestador"""
        if not self.cnpj_cpf:
            return
        
        # Remove formatação
        doc_num = re.sub(r'[^\d]', '', self.cnpj_cpf)
        
        if self.tipo_pessoa == "Pessoa Jurídica":
            if len(doc_num) != 14:
                frappe.throw("CNPJ deve ter 14 dígitos")
            if not self.validate_cnpj(doc_num):
                frappe.throw("CNPJ inválido")
        else:
            if len(doc_num) != 11:
                frappe.throw("CPF deve ter 11 dígitos")
            if not self.validate_cpf(doc_num):
                frappe.throw("CPF inválido")

    def validate_cnpj(self, cnpj):
        """Validação de CNPJ"""
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Primeiro dígito verificador
        soma = 0
        peso = 5
        for i in range(12):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != digito1:
            return False
        
        # Segundo dígito verificador
        soma = 0
        peso = 6
        for i in range(13):
            soma += int(cnpj[i]) * peso
            peso -= 1
            if peso < 2:
                peso = 9
        
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return int(cnpj[13]) == digito2

    def validate_cpf(self, cpf):
        """Validação de CPF"""
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[9]) != digito1:
            return False
        
        # Segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        return int(cpf[10]) == digito2

    def validate_inscricao_municipal(self):
        """Valida se inscrição municipal é única"""
        if self.inscricao_municipal:
            existing = frappe.db.get_value("ISS Prestador", 
                                         {"inscricao_municipal": self.inscricao_municipal, 
                                          "name": ["!=", self.name]})
            if existing:
                frappe.throw(f"Inscrição Municipal {self.inscricao_municipal} já existe")

    def validate_email(self):
        """Valida formato do email"""
        if self.email:
            try:
                validate_email_address(self.email)
            except:
                frappe.throw("Email inválido")
        
        if self.responsavel_email:
            try:
                validate_email_address(self.responsavel_email)
            except:
                frappe.throw("Email do responsável inválido")

    def validate_responsavel_data(self):
        """Valida dados do responsável legal"""
        if self.tipo_pessoa == "Pessoa Jurídica":
            if not self.responsavel_nome:
                frappe.throw("Nome do responsável é obrigatório para Pessoa Jurídica")
            if not self.responsavel_cpf:
                frappe.throw("CPF do responsável é obrigatório para Pessoa Jurídica")

    def calculate_aliquota_iss(self):
        """Calcula alíquota ISS baseada na atividade principal"""
        if self.atividade_principal and not self.aliquota_iss:
            atividade = frappe.get_doc("ISS Atividade", self.atividade_principal)
            if atividade.aliquota_padrao:
                self.aliquota_iss = atividade.aliquota_padrao

    def validate_beneficio_fiscal(self):
        """Valida período do benefício fiscal"""
        if self.beneficio_fiscal:
            if not self.data_inicio_beneficio:
                frappe.throw("Data de início do benefício fiscal é obrigatória")
            if self.data_fim_beneficio and self.data_inicio_beneficio > self.data_fim_beneficio:
                frappe.throw("Data de início não pode ser maior que data de fim do benefício")

    def on_update(self):
        """Executa após salvar"""
        self.update_customer_data()

    def update_customer_data(self):
        """Atualiza dados do Customer relacionado"""
        # Cria ou atualiza Customer
        customer_name = self.razao_social or self.nome_fantasia
        
        if not frappe.db.exists("Customer", customer_name):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": "Company" if self.tipo_pessoa == "Pessoa Jurídica" else "Individual",
                "tax_id": self.cnpj_cpf,
                "website": "",
                "mobile_no": self.telefone,
                "email_id": self.email,
                "customer_group": "Prestador ISS",
                "territory": "Brazil",
                "custom_inscricao_municipal": self.inscricao_municipal
            })
            customer.insert(ignore_permissions=True)

    @frappe.whitelist()
    def get_atividades_por_prestador(self):
        """Retorna atividades do prestador"""
        return frappe.get_all("ISS Atividade Item", 
                            filters={"parent": self.name}, 
                            fields=["atividade", "aliquota", "descricao"])

    @frappe.whitelist()
    def calcular_iss_mensal(self, mes, ano):
        """Calcula ISS mensal do prestador"""
        lancamentos = frappe.get_all("ISS Lancamento",
                                   filters={
                                       "prestador": self.name,
                                       "mes_competencia": mes,
                                       "ano_competencia": ano,
                                       "docstatus": 1
                                   },
                                   fields=["valor_servicos", "valor_iss", "valor_retencoes"])
        
        total_servicos = sum(flt(l.valor_servicos) for l in lancamentos)
        total_iss = sum(flt(l.valor_iss) for l in lancamentos)
        total_retencoes = sum(flt(l.valor_retencoes) for l in lancamentos)
        
        return {
            "total_servicos": total_servicos,
            "total_iss": total_iss,
            "total_retencoes": total_retencoes,
            "iss_a_recolher": total_iss - total_retencoes
        }

    def before_insert(self):
        """Executa antes de inserir"""
        if not self.inscricao_municipal:
            self.inscricao_municipal = self.generate_inscricao_municipal()

    def generate_inscricao_municipal(self):
        """Gera número de inscrição municipal"""
        # Busca último número
        last_inscricao = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(inscricao_municipal, -8) AS UNSIGNED)) as last_num
            FROM `tabISS Prestador`
            WHERE inscricao_municipal REGEXP '^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}-[0-9]$'
        """)[0][0]
        
        next_num = (last_inscricao or 0) + 1
        
        # Formato: 01.001.001-2 (município.sequencial-dv)
        base_num = f"{next_num:06d}"
        inscricao = f"01.{base_num[:3]}.{base_num[3:]}"
        
        # Calcula dígito verificador
        digits = re.sub(r'[^\d]', '', inscricao)
        dv = sum(int(d) * (i + 1) for i, d in enumerate(digits)) % 11
        dv = dv if dv < 10 else 0
        
        return f"{inscricao}-{dv}"