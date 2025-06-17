# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OrgaoPublico(Document):
    def validate(self):
        self.validate_government_unit()
        self.validate_parent_orgao()

    def validate_government_unit(self):
        """Validate that the government unit exists and is active"""
        if self.government_unit:
            unit_exists = frappe.db.exists("Government Unit", self.government_unit)
            if not unit_exists:
                frappe.throw(f"Government Unit {self.government_unit} does not exist")

            unit_active = frappe.db.get_value("Government Unit", self.government_unit, "is_active")
            if not unit_active:
                frappe.throw(f"Government Unit {self.government_unit} is not active")

    def validate_parent_orgao(self):
        """Validate that the parent orgao exists and is active"""
        if self.parent_orgao:
            parent_exists = frappe.db.exists("Orgao Publico", self.parent_orgao)
            if not parent_exists:
                frappe.throw(f"Parent Orgão {self.parent_orgao} does not exist")

            parent_active = frappe.db.get_value("Orgao Publico", self.parent_orgao, "is_active")
            if not parent_active:
                frappe.throw(f"Parent Orgão {self.parent_orgao} is not active")

    def on_update(self):
        """Update child orgaos when status changes"""
        if self.has_value_changed("is_active"):
            # Update all child orgaos with the same status
            child_orgaos = frappe.get_all("Orgao Publico", filters={"parent_orgao": self.name})
            for orgao in child_orgaos:
                doc = frappe.get_doc("Orgao Publico", orgao.name)
                doc.is_active = self.is_active
                doc.save()
