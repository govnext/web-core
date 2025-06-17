# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CategoriaReceita(Document):
    def validate(self):
        self.validate_codigo()

    def validate_codigo(self):
        """Validate that the category code is unique"""
        if self.codigo and frappe.db.exists("Categoria Receita", {"codigo": self.codigo, "name": ["!=", self.name]}):
            frappe.throw(f"Código de categoria {self.codigo} já está em uso")
