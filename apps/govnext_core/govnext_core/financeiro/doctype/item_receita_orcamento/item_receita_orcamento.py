# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class ItemReceitaOrcamento(Document):
    def validate(self):
        self.validate_values()

    def validate_values(self):
        """Validate that the values make sense"""
        if self.valor_previsto and flt(self.valor_previsto) < 0:
            frappe.throw("O valor previsto não pode ser negativo")

        if self.valor and flt(self.valor) < 0:
            frappe.throw("O valor realizado não pode ser negativo")

        # Calculate percentage of execution
        if self.valor_previsto and self.valor:
            self.percentual_execucao = (flt(self.valor) / flt(self.valor_previsto)) * 100
        else:
            self.percentual_execucao = 0
