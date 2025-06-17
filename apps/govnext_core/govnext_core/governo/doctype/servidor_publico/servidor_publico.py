# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, date_diff

class ServidorPublico(Document):
    def validate(self):
        self.validate_cpf()
        self.validate_dates()
        self.validate_orgao()
        self.update_status()

    def validate_cpf(self):
        """Validate CPF format and uniqueness"""
        from apps.govnext_core.govnext_core.utils.validation import validate_cpf

        if self.cpf:
            if not validate_cpf(self.cpf):
                frappe.throw("CPF inválido")

            # Check if CPF is already used by another servidor
            if frappe.db.exists("Servidor Publico", {"cpf": self.cpf, "name": ["!=", self.name]}):
                frappe.throw(f"CPF {self.cpf} já está cadastrado para outro servidor")

    def validate_dates(self):
        """Validate date fields"""
        if self.data_nascimento and getdate(self.data_nascimento) > getdate(today()):
            frappe.throw("Data de nascimento não pode ser futura")

        if self.data_admissao and self.data_exoneracao and getdate(self.data_exoneracao) < getdate(self.data_admissao):
            frappe.throw("Data de exoneração não pode ser anterior à data de admissão")

    def validate_orgao(self):
        """Validate that the orgao exists and is active"""
        if self.orgao:
            orgao_exists = frappe.db.exists("Orgao Publico", self.orgao)
            if not orgao_exists:
                frappe.throw(f"Órgão {self.orgao} não existe")

            orgao_active = frappe.db.get_value("Orgao Publico", self.orgao, "is_active")
            if not orgao_active:
                frappe.throw(f"Órgão {self.orgao} não está ativo")

    def update_status(self):
        """Update status based on dates and other fields"""
        today_date = getdate(today())

        # If exoneration date is set and is in the past, set status to "Exonerado"
        if self.data_exoneracao and getdate(self.data_exoneracao) <= today_date:
            self.status = "Exonerado"
        # If admission date is set and is in the future, set status to "Aguardando Admissão"
        elif self.data_admissao and getdate(self.data_admissao) > today_date:
            self.status = "Aguardando Admissão"
        # If admission date is set and is in the past, and no exoneration date or is in the future
        elif self.data_admissao and getdate(self.data_admissao) <= today_date:
            if self.afastado:
                self.status = "Afastado"
            else:
                self.status = "Ativo"
        # Default status
        else:
            self.status = "Ativo"
