# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt, add_days

class IPTUPagamento(Document):
    def validate(self):
        """Validate payment information"""
        self.check_payment_status()

    def check_payment_status(self):
        """Update payment status based on payment date and due date"""
        today = getdate()

        # If paid, ensure payment date is provided
        if self.status == "Pago" and not self.data_pagamento:
            self.data_pagamento = today

        # If not paid, check if it's overdue
        if self.status not in ["Pago", "Cancelado"] and today > getdate(self.data_vencimento):
            self.status = "Atrasado"

            # If overdue for more than 90 days, move to "Dívida Ativa"
            if add_days(getdate(self.data_vencimento), 90) < today:
                self.status = "Dívida Ativa"

    def on_update(self):
        """When payment status changes, update parent document"""
        if self.status == "Pago" and hasattr(self, "parent") and self.parent:
            # Try to refresh parent document status
            try:
                parent_doc = frappe.get_doc("IPTU Lancamento", self.parent)
                parent_doc.update_status()
                parent_doc.save()
            except Exception as e:
                frappe.log_error(f"Erro ao atualizar status do IPTU: {e}")
