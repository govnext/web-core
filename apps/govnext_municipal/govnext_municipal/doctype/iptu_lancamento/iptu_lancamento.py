# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, add_months, add_days, getdate, get_last_day

class IPTULancamento(Document):
    def validate(self):
        self.calculate_iptu_value()
        self.generate_payment_schedule()

    def calculate_iptu_value(self):
        """Calculate IPTU value based on property value and tax rates"""
        if not self.valor_venal_total:
            # Get property value from cadastro
            if self.inscricao_cadastral:
                cadastro = frappe.get_doc("IPTU Cadastro", self.inscricao_cadastral)
                self.valor_venal_total = cadastro.valor_venal_total

        # Get IPTU rate from settings or use default
        iptu_rate = self.get_iptu_rate() or 0.02  # Default 2%

        # Calculate IPTU
        self.valor_iptu = flt(self.valor_venal_total) * iptu_rate

        # Apply discounts if paid in a single installment
        if self.parcelas == 1:
            self.desconto = self.valor_iptu * 0.1  # 10% discount for single payment
        else:
            self.desconto = 0

        self.valor_total = self.valor_iptu - self.desconto

    def get_iptu_rate(self):
        """Get IPTU rate from settings based on property type and value"""
        # In a real scenario, this would fetch tax rates from a settings table
        # based on property value ranges and types
        try:
            # Simple simulation of progressive tax based on property value
            if self.valor_venal_total <= 100000:
                return 0.015  # 1.5% for properties up to 100k
            elif self.valor_venal_total <= 500000:
                return 0.02   # 2.0% for properties up to 500k
            elif self.valor_venal_total <= 1000000:
                return 0.025  # 2.5% for properties up to 1M
            else:
                return 0.03   # 3.0% for properties above 1M
        except:
            # Default rate
            return 0.02

    def generate_payment_schedule(self):
        """Generate payment schedule based on number of installments"""
        if not self.parcelas or self.parcelas < 1:
            self.parcelas = 1

        if not self.valor_total:
            self.calculate_iptu_value()

        # Clear existing schedule
        self.pagamentos = []

        installment_value = self.valor_total / self.parcelas
        due_date = getdate(self.data_vencimento) or getdate()

        for i in range(self.parcelas):
            # Add a row to payment schedule
            self.append("pagamentos", {
                "parcela": i + 1,
                "valor": installment_value,
                "data_vencimento": due_date if i == 0 else add_months(due_date, i),
                "status": "Pendente"
            })

    def on_submit(self):
        """Actions when IPTU is finalized"""
        # Send notification to property owner
        self.send_notification()

    def send_notification(self):
        """Send notification to property owner"""
        if self.proprietario:
            try:
                customer = frappe.get_doc("Customer", self.proprietario)
                if customer.email:
                    # Send email notification
                    subject = f"IPTU {self.ano} - Lançamento Realizado"
                    message = f"""
                    <p>Prezado(a) {customer.customer_name},</p>
                    <p>Informamos que o IPTU referente ao ano {self.ano} para o imóvel de inscrição cadastral
                    {self.inscricao_cadastral} foi lançado.</p>
                    <p>Valor total: R$ {self.valor_total:.2f}</p>
                    <p>Número de parcelas: {self.parcelas}</p>
                    <p>Data de vencimento da 1ª parcela: {self.data_vencimento}</p>
                    <p>Acesse o portal do cidadão para mais detalhes e para emissão das guias de pagamento.</p>
                    """

                    frappe.sendmail(
                        recipients=[customer.email],
                        subject=subject,
                        message=message
                    )
            except Exception as e:
                frappe.log_error(f"Erro ao enviar notificação de IPTU: {e}")
