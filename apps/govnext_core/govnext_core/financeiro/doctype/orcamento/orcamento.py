# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt

class Orcamento(Document):
    def validate(self):
        self.validate_dates()
        self.validate_government_unit()
        self.calculate_totals()

    def validate_dates(self):
        """Validate that the dates make sense"""
        if self.data_inicio and self.data_fim:
            if getdate(self.data_fim) < getdate(self.data_inicio):
                frappe.throw("A data de fim não pode ser anterior à data de início")

    def validate_government_unit(self):
        """Validate that the government unit exists and is active"""
        if self.government_unit:
            unit_exists = frappe.db.exists("Government Unit", self.government_unit)
            if not unit_exists:
                frappe.throw(f"Government Unit {self.government_unit} does not exist")

            unit_active = frappe.db.get_value("Government Unit", self.government_unit, "is_active")
            if not unit_active:
                frappe.throw(f"Government Unit {self.government_unit} is not active")

    def calculate_totals(self):
        """Calculate total values from revenue and expense items"""
        # Calculate total revenue
        self.total_receita = sum(flt(item.valor) for item in self.receitas)

        # Calculate total expenses
        self.total_despesa = sum(flt(item.valor) for item in self.despesas)

        # Calculate balance
        self.saldo = self.total_receita - self.total_despesa

        # Calculate execution percentages
        if self.total_receita_prevista and self.total_receita:
            self.percentual_execucao_receita = (self.total_receita / self.total_receita_prevista) * 100
        else:
            self.percentual_execucao_receita = 0

        if self.total_despesa_prevista and self.total_despesa:
            self.percentual_execucao_despesa = (self.total_despesa / self.total_despesa_prevista) * 100
        else:
            self.percentual_execucao_despesa = 0

    def on_submit(self):
        """Actions when budget is submitted"""
        # Create budget accounts if they don't exist
        self.create_budget_accounts()

        # Update status
        self.status = "Aprovado"

    def on_cancel(self):
        """Actions when budget is cancelled"""
        self.status = "Cancelado"

    def create_budget_accounts(self):
        """Create budget accounts if they don't exist"""
        # This would create the necessary accounting entries
        # For now, we'll just log it
        frappe.log_error(f"Criação de contas orçamentárias para {self.name} não implementada ainda.")