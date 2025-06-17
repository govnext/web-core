# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AlvaraAtividade(Document):
    def validate(self):
        """Validate that there's only one main activity"""
        if self.principal:
            # Check if there's another main activity in the parent document
            if hasattr(self, 'parent') and self.parent:
                try:
                    parent_doc = frappe.get_doc("Alvara Municipal", self.parent)
                    for activity in parent_doc.atividades_autorizadas:
                        if activity.name != self.name and activity.principal:
                            activity.principal = 0
                except Exception as e:
                    frappe.log_error(f"Erro ao validar atividade principal: {e}")
