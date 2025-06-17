# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate, add_to_date, date_diff

class AlvaraMunicipal(Document):
    def validate(self):
        self.validate_dates()
        self.check_status()
        self.validate_requirements()

    def validate_dates(self):
        """Validate that dates make sense"""
        if self.data_emissao and self.data_validade:
            if getdate(self.data_validade) < getdate(self.data_emissao):
                frappe.throw("A data de validade não pode ser anterior à data de emissão.")

    def check_status(self):
        """Update status based on dates"""
        today = getdate()

        if self.docstatus == 1:  # If submitted
            if getdate(self.data_validade) < today:
                if self.status != "Vencido":
                    # Record in history that alvará has expired
                    self.add_history("Vencido", "Alvará vencido automaticamente pelo sistema.")
                self.status = "Vencido"
            else:
                # If all requirements are met and document is submitted, status should be "Emitido"
                if all([self.licenca_bombeiros, self.licenca_sanitaria,
                        self.documentacao_completa, self.taxa_paga]):
                    if self.status != "Emitido":
                        self.add_history("Emitido", "Alvará emitido após cumprimento de requisitos.")
                    self.status = "Emitido"

    def validate_requirements(self):
        """Validate if all requirements are met for alvará issuance"""
        # Requirements depend on risk classification
        if self.classificacao_risco == "Alto Risco":
            required_fields = ["licenca_bombeiros", "licenca_sanitaria",
                              "licenca_ambiental", "vistoria_engenharia",
                              "documentacao_completa", "parecer_tecnico", "taxa_paga"]

            for field in required_fields:
                if not self.get(field) and self.status == "Emitido":
                    frappe.throw(f"Para alvarás de alto risco, o requisito '{field}' deve ser atendido.")

        # For medium risk, require fewer items
        elif self.classificacao_risco == "Médio Risco":
            if not all([self.licenca_bombeiros, self.documentacao_completa, self.taxa_paga]) and self.status == "Emitido":
                frappe.throw("Para alvarás de médio risco, é necessário licença do corpo de bombeiros, documentação completa e taxa paga.")

    def on_submit(self):
        """Actions when alvará is submitted"""
        if not self.documento_alvara:
            self.generate_alvara_document()

        # Record submission in history
        self.add_history("Emitido", "Alvará submetido e emitido.")

        # Schedule notification for renewal
        if not self.renovacao_automatica:
            self.schedule_renewal_notification()

    def on_cancel(self):
        """Actions when alvará is cancelled"""
        self.status = "Cancelado"
        self.add_history("Cancelado", "Alvará foi cancelado.")

    def on_update(self):
        """Actions on update"""
        if self.has_value_changed("status"):
            self.add_history(self.status, f"Status do alvará alterado para {self.status}.")

    def add_history(self, status, description):
        """Add entry to history table"""
        self.append("historico", {
            "data": nowdate(),
            "status": status,
            "descricao": description,
        })

    def schedule_renewal_notification(self):
        """Schedule notification for alvará renewal"""
        if self.data_validade:
            # Schedule notification 30 days before expiration
            notification_date = add_days(getdate(self.data_validade), -30)

            if notification_date > getdate():
                # Create notification entry
                frappe.get_doc({
                    "doctype": "Notification",
                    "subject": f"Renovação de Alvará {self.numero_alvara}",
                    "document_type": "Alvara Municipal",
                    "document_name": self.name,
                    "event": "Date",
                    "date": notification_date,
                    "message": f"""
                    <p>O Alvará Municipal {self.numero_alvara} vencerá em 30 dias.</p>
                    <p>Requerente: {self.requerente}</p>
                    <p>Data de Vencimento: {self.data_validade}</p>
                    """
                }).insert(ignore_permissions=True)

    def generate_alvara_document(self):
        """Generate PDF document for alvará"""
        # This would be implemented to generate an actual PDF document
        # For now, we'll just log it
        frappe.log_error(f"Geração de documento de alvará para {self.numero_alvara} não implementada ainda.")
