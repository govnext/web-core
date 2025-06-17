# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IPTUCadastro(Document):
    def validate(self):
        self.calculate_total_value()
        self.validate_area()

    def calculate_total_value(self):
        """Calculate total property value"""
        self.valor_venal_terreno = self.valor_venal_terreno or 0
        self.valor_venal_construcao = self.valor_venal_construcao or 0
        self.valor_venal_total = self.valor_venal_terreno + self.valor_venal_construcao

    def validate_area(self):
        """Validate that construction area doesn't exceed land area"""
        if self.area_construida and self.area_terreno and self.area_construida > self.area_terreno:
            frappe.throw("A área construída não pode ser maior que a área do terreno.")

    def after_insert(self):
        """Create default IPTU record for the current year"""
        self.create_current_year_iptu()

    def create_current_year_iptu(self):
        """Create IPTU record for the current year"""
        # Only create if not already exists
        current_year = frappe.utils.today()[:4]  # Get current year

        if not frappe.db.exists("IPTU Lancamento", {"inscricao_cadastral": self.inscricao_cadastral, "ano": current_year}):
            # Create new IPTU record
            iptu = frappe.new_doc("IPTU Lancamento")
            iptu.inscricao_cadastral = self.inscricao_cadastral
            iptu.proprietario = self.proprietario
            iptu.ano = current_year
            iptu.valor_venal_total = self.valor_venal_total

            # Calculate IPTU based on property value
            iptu.calculate_iptu_value()
            iptu.insert()
