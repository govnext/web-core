# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CargoPublico(Document):
    def validate(self):
        self.validate_codigo_cargo()
        self.validate_salario_base()

    def validate_codigo_cargo(self):
        """Validate that the cargo code is unique"""
        if self.codigo_cargo and frappe.db.exists("Cargo Publico", {"codigo_cargo": self.codigo_cargo, "name": ["!=", self.name]}):
            frappe.throw(f"Código de cargo {self.codigo_cargo} já está em uso")

    def validate_salario_base(self):
        """Validate salary values"""
        if self.salario_base and self.salario_base < 0:
            frappe.throw("Salário base não pode ser negativo")

        if self.salario_minimo and self.salario_maximo and self.salario_minimo > self.salario_maximo:
            frappe.throw("Salário mínimo não pode ser maior que o salário máximo")

    def on_update(self):
        """Update all servidores with this cargo if the cargo becomes inactive"""
        if self.has_value_changed("is_active") and not self.is_active:
            # Get all servidores with this cargo
            servidores = frappe.get_all("Servidor Publico", filters={"cargo": self.name, "status": "Ativo"})

            if servidores:
                frappe.msgprint(f"Atenção: Existem {len(servidores)} servidores ativos com este cargo. Considere transferi-los para outro cargo antes de desativar este.")
