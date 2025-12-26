"""
Sincronização Financeira entre ERPNext e GovNext.
Gerencia contas a pagar, contas a receber, fluxo de caixa e relatórios financeiros.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, flt, cint, fmt_money

from ..base import IntegrationResult, IntegrationError
from ..utils import DataTransformer, ValidationUtils, performance_monitor


class ERPNextFinanceiroSync:
    """
    Sincronizador Financeiro entre ERPNext e GovNext.
    
    Funcionalidades:
    - Sincronizar Sales Invoice / Purchase Invoice
    - Integrar Payment Entry
    - Sincronizar Journal Entry
    - Importar dados de Account
    - Gerar relatórios financeiros consolidados
    """
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        
        # Mapeamento Sales Invoice
        self.sales_invoice_mapping = {
            "nome": "name",
            "customer": "customer", 
            "posting_date": "posting_date",
            "due_date": "due_date",
            "total": "grand_total",
            "outstanding_amount": "outstanding_amount",
            "status": "status",
            "remarks": "remarks",
            "cost_center": "cost_center",
            "project": "project"
        }
        
        # Mapeamento Purchase Invoice
        self.purchase_invoice_mapping = {
            "nome": "name",
            "supplier": "supplier",
            "posting_date": "posting_date", 
            "due_date": "due_date",
            "total": "grand_total",
            "outstanding_amount": "outstanding_amount",
            "status": "status",
            "remarks": "remarks",
            "cost_center": "cost_center",
            "project": "project"
        }
        
        # Mapeamento Payment Entry
        self.payment_entry_mapping = {
            "nome": "name",
            "payment_type": "payment_type",
            "party_type": "party_type",
            "party": "party",
            "posting_date": "posting_date",
            "paid_amount": "paid_amount",
            "received_amount": "received_amount",
            "mode_of_payment": "mode_of_payment",
            "reference_no": "reference_no",
            "reference_date": "reference_date"
        }
        
        # Status mapping
        self.invoice_status_mapping = {
            "Draft": "Rascunho",
            "Submitted": "Enviado",
            "Paid": "Pago",
            "Partly Paid": "Parcialmente Pago",
            "Overdue": "Vencido",
            "Cancelled": "Cancelado",
            "Credit Note Issued": "Nota Crédito Emitida",
            "Return": "Devolução"
        }
        
        self.payment_status_mapping = {
            "Draft": "Rascunho",
            "Submitted": "Confirmado",
            "Cancelled": "Cancelado"
        }
    
    @performance_monitor
    def sync(self, **kwargs) -> IntegrationResult:
        """Sincroniza dados financeiros do ERPNext"""
        try:
            sync_type = kwargs.get("sync_type", "all")  # all, invoices, payments, accounts
            date_from = kwargs.get("date_from")
            date_to = kwargs.get("date_to")
            limit = kwargs.get("limit", 100)
            
            self.logger.info(f"Iniciando sincronização financeira - Tipo: {sync_type}")
            
            results = {}
            
            if sync_type in ["all", "invoices"]:
                # Sincroniza faturas de venda e compra
                results["sales_invoices"] = self._sync_sales_invoices(date_from, date_to, limit)
                results["purchase_invoices"] = self._sync_purchase_invoices(date_from, date_to, limit)
            
            if sync_type in ["all", "payments"]:
                # Sincroniza pagamentos
                results["payment_entries"] = self._sync_payment_entries(date_from, date_to, limit)
            
            if sync_type in ["all", "accounts"]:
                # Sincroniza plano de contas
                results["accounts"] = self._sync_accounts()
            
            # Calcula estatísticas consolidadas
            total_success = sum(1 for r in results.values() if r.success)
            total_operations = len(results)
            
            return IntegrationResult(
                success=total_success == total_operations,
                data=results,
                metadata={
                    "sync_type": sync_type,
                    "successful_operations": total_success,
                    "total_operations": total_operations
                }
            )
            
        except Exception as e:
            self.logger.error(f"Erro na sincronização financeira: {str(e)}")
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="FINANCIAL_SYNC_FAILED"
            )
    
    def _sync_sales_invoices(self, date_from: str = None, date_to: str = None, limit: int = 100) -> IntegrationResult:
        """Sincroniza faturas de venda"""
        try:
            filters = {}
            if date_from:
                filters["posting_date"] = [">=", date_from]
            if date_to:
                if "posting_date" in filters:
                    filters["posting_date"] = ["between", [date_from, date_to]]
                else:
                    filters["posting_date"] = ["<=", date_to]
            
            # Busca faturas no ERPNext
            invoices_result = self.connector.get_list(
                "Sales Invoice",
                fields=list(self.sales_invoice_mapping.values()) + ["items"],
                filters=filters,
                limit=limit,
                order_by="posting_date desc"
            )
            
            if not invoices_result.success:
                return invoices_result
            
            invoices = invoices_result.data.get("data", [])
            
            sync_stats = {
                "total": len(invoices),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            for invoice_data in invoices:
                try:
                    result = self._process_sales_invoice(invoice_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar fatura de venda {invoice_data.get('name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de faturas de venda concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="SALES_INVOICE_SYNC_FAILED"
            )
    
    def _sync_purchase_invoices(self, date_from: str = None, date_to: str = None, limit: int = 100) -> IntegrationResult:
        """Sincroniza faturas de compra"""
        try:
            filters = {}
            if date_from:
                filters["posting_date"] = [">=", date_from]
            if date_to:
                if "posting_date" in filters:
                    filters["posting_date"] = ["between", [date_from, date_to]]
                else:
                    filters["posting_date"] = ["<=", date_to]
            
            # Busca faturas no ERPNext
            invoices_result = self.connector.get_list(
                "Purchase Invoice",
                fields=list(self.purchase_invoice_mapping.values()) + ["items"],
                filters=filters,
                limit=limit,
                order_by="posting_date desc"
            )
            
            if not invoices_result.success:
                return invoices_result
            
            invoices = invoices_result.data.get("data", [])
            
            sync_stats = {
                "total": len(invoices),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            for invoice_data in invoices:
                try:
                    result = self._process_purchase_invoice(invoice_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar fatura de compra {invoice_data.get('name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de faturas de compra concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PURCHASE_INVOICE_SYNC_FAILED"
            )
    
    def _sync_payment_entries(self, date_from: str = None, date_to: str = None, limit: int = 100) -> IntegrationResult:
        """Sincroniza lançamentos de pagamento"""
        try:
            filters = {}
            if date_from:
                filters["posting_date"] = [">=", date_from]
            if date_to:
                if "posting_date" in filters:
                    filters["posting_date"] = ["between", [date_from, date_to]]
                else:
                    filters["posting_date"] = ["<=", date_to]
            
            # Busca pagamentos no ERPNext
            payments_result = self.connector.get_list(
                "Payment Entry",
                fields=list(self.payment_entry_mapping.values()),
                filters=filters,
                limit=limit,
                order_by="posting_date desc"
            )
            
            if not payments_result.success:
                return payments_result
            
            payments = payments_result.data.get("data", [])
            
            sync_stats = {
                "total": len(payments),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            for payment_data in payments:
                try:
                    result = self._process_payment_entry(payment_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar pagamento {payment_data.get('name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de pagamentos concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PAYMENT_ENTRY_SYNC_FAILED"
            )
    
    def _sync_accounts(self) -> IntegrationResult:
        """Sincroniza plano de contas"""
        try:
            # Busca contas no ERPNext
            accounts_result = self.connector.get_list(
                "Account",
                fields=["name", "account_name", "account_type", "parent_account", "is_group", 
                       "account_number", "root_type", "report_type", "account_currency"],
                limit=500,
                order_by="lft"
            )
            
            if not accounts_result.success:
                return accounts_result
            
            accounts = accounts_result.data.get("data", [])
            
            sync_stats = {
                "total": len(accounts),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            # Processa contas em ordem hierárquica
            for account_data in accounts:
                try:
                    result = self._process_account(account_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar conta {account_data.get('name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de contas concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ACCOUNTS_SYNC_FAILED"
            )
    
    def _process_sales_invoice(self, invoice_data: Dict[str, Any]) -> IntegrationResult:
        """Processa uma fatura de venda individual"""
        try:
            # Transforma dados
            govnext_data = DataTransformer.transform_erpnext_to_govnext(
                invoice_data, 
                self.sales_invoice_mapping
            )
            
            # Normaliza dados
            govnext_data = self._normalize_invoice_data(govnext_data, "sales")
            
            # Verifica se já existe
            existing_invoice = frappe.db.exists("Fatura Venda", {
                "codigo_erpnext": invoice_data.get("name")
            })
            
            if existing_invoice:
                doc = frappe.get_doc("Fatura Venda", existing_invoice)
                doc.update(govnext_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Fatura Venda",
                    "codigo_erpnext": invoice_data.get("name"),
                    **govnext_data
                })
                doc.insert()
                action = "created"
            
            # Processa itens da fatura
            if invoice_data.get("items"):
                self._process_invoice_items(doc.name, invoice_data["items"], "sales")
            
            return IntegrationResult(
                success=True,
                data={"invoice_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="SALES_INVOICE_PROCESS_FAILED"
            )
    
    def _process_purchase_invoice(self, invoice_data: Dict[str, Any]) -> IntegrationResult:
        """Processa uma fatura de compra individual"""
        try:
            # Transforma dados
            govnext_data = DataTransformer.transform_erpnext_to_govnext(
                invoice_data, 
                self.purchase_invoice_mapping
            )
            
            # Normaliza dados
            govnext_data = self._normalize_invoice_data(govnext_data, "purchase")
            
            # Verifica se já existe
            existing_invoice = frappe.db.exists("Fatura Compra", {
                "codigo_erpnext": invoice_data.get("name")
            })
            
            if existing_invoice:
                doc = frappe.get_doc("Fatura Compra", existing_invoice)
                doc.update(govnext_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Fatura Compra",
                    "codigo_erpnext": invoice_data.get("name"),
                    **govnext_data
                })
                doc.insert()
                action = "created"
            
            # Processa itens da fatura
            if invoice_data.get("items"):
                self._process_invoice_items(doc.name, invoice_data["items"], "purchase")
            
            return IntegrationResult(
                success=True,
                data={"invoice_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PURCHASE_INVOICE_PROCESS_FAILED"
            )
    
    def _process_payment_entry(self, payment_data: Dict[str, Any]) -> IntegrationResult:
        """Processa um lançamento de pagamento"""
        try:
            # Transforma dados
            govnext_data = DataTransformer.transform_erpnext_to_govnext(
                payment_data, 
                self.payment_entry_mapping
            )
            
            # Normaliza dados
            govnext_data = self._normalize_payment_data(govnext_data)
            
            # Verifica se já existe
            existing_payment = frappe.db.exists("Lancamento Pagamento", {
                "codigo_erpnext": payment_data.get("name")
            })
            
            if existing_payment:
                doc = frappe.get_doc("Lancamento Pagamento", existing_payment)
                doc.update(govnext_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Lancamento Pagamento",
                    "codigo_erpnext": payment_data.get("name"),
                    **govnext_data
                })
                doc.insert()
                action = "created"
            
            return IntegrationResult(
                success=True,
                data={"payment_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PAYMENT_ENTRY_PROCESS_FAILED"
            )
    
    def _process_account(self, account_data: Dict[str, Any]) -> IntegrationResult:
        """Processa uma conta do plano de contas"""
        try:
            # Prepara dados da conta
            govnext_data = {
                "nome_conta": account_data.get("account_name"),
                "numero_conta": account_data.get("account_number"),
                "tipo_conta": account_data.get("account_type"),
                "conta_pai": account_data.get("parent_account"),
                "eh_grupo": cint(account_data.get("is_group", 0)),
                "tipo_raiz": account_data.get("root_type"),
                "tipo_relatorio": account_data.get("report_type"),
                "moeda": account_data.get("account_currency", "BRL"),
                "codigo_erpnext": account_data.get("name")
            }
            
            # Verifica se já existe
            existing_account = frappe.db.exists("Conta Contabil", {
                "codigo_erpnext": account_data.get("name")
            })
            
            if existing_account:
                doc = frappe.get_doc("Conta Contabil", existing_account)
                doc.update(govnext_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Conta Contabil",
                    **govnext_data
                })
                doc.insert()
                action = "created"
            
            return IntegrationResult(
                success=True,
                data={"account_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ACCOUNT_PROCESS_FAILED"
            )
    
    def _normalize_invoice_data(self, data: Dict[str, Any], invoice_type: str) -> Dict[str, Any]:
        """Normaliza dados de fatura"""
        normalized = data.copy()
        
        # Normaliza status
        if "status" in normalized:
            normalized["status"] = self.invoice_status_mapping.get(normalized["status"], normalized["status"])
        
        # Normaliza datas
        date_fields = ["posting_date", "due_date"]
        for field in date_fields:
            if field in normalized and normalized[field]:
                normalized[field] = DataTransformer.normalize_date(normalized[field])
        
        # Normaliza valores monetários
        money_fields = ["total", "outstanding_amount"]
        for field in money_fields:
            if field in normalized and normalized[field]:
                normalized[field] = DataTransformer.normalize_monetary_value(normalized[field])
        
        return normalized
    
    def _normalize_payment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza dados de pagamento"""
        normalized = data.copy()
        
        # Normaliza datas
        date_fields = ["posting_date", "reference_date"]
        for field in date_fields:
            if field in normalized and normalized[field]:
                normalized[field] = DataTransformer.normalize_date(normalized[field])
        
        # Normaliza valores monetários
        money_fields = ["paid_amount", "received_amount"]
        for field in money_fields:
            if field in normalized and normalized[field]:
                normalized[field] = DataTransformer.normalize_monetary_value(normalized[field])
        
        return normalized
    
    def _process_invoice_items(self, invoice_name: str, items: List[Dict], invoice_type: str):
        """Processa itens de uma fatura"""
        try:
            doctype_map = {
                "sales": "Item Fatura Venda",
                "purchase": "Item Fatura Compra"
            }
            
            doctype = doctype_map.get(invoice_type)
            if not doctype:
                return
            
            # Remove itens existentes
            frappe.db.delete(doctype, {"fatura": invoice_name})
            
            # Adiciona novos itens
            for item_data in items:
                item_doc = frappe.get_doc({
                    "doctype": doctype,
                    "fatura": invoice_name,
                    "item_code": item_data.get("item_code"),
                    "item_name": item_data.get("item_name"),
                    "descricao": item_data.get("description"),
                    "quantidade": flt(item_data.get("qty", 0)),
                    "preco_unitario": DataTransformer.normalize_monetary_value(item_data.get("rate", 0)),
                    "valor_total": DataTransformer.normalize_monetary_value(item_data.get("amount", 0)),
                    "unidade": item_data.get("uom")
                })
                item_doc.insert()
                
        except Exception as e:
            self.logger.error(f"Erro ao processar itens da fatura {invoice_name}: {str(e)}")
    
    def generate_financial_report(self, report_type: str, date_from: str, date_to: str) -> IntegrationResult:
        """Gera relatórios financeiros consolidados"""
        try:
            if report_type == "cash_flow":
                return self._generate_cash_flow_report(date_from, date_to)
            elif report_type == "profit_loss":
                return self._generate_profit_loss_report(date_from, date_to)
            elif report_type == "balance_sheet":
                return self._generate_balance_sheet_report(date_to)
            else:
                return IntegrationResult(
                    success=False,
                    error_message=f"Tipo de relatório não suportado: {report_type}",
                    error_code="UNSUPPORTED_REPORT_TYPE"
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="FINANCIAL_REPORT_FAILED"
            )
    
    def _generate_cash_flow_report(self, date_from: str, date_to: str) -> IntegrationResult:
        """Gera relatório de fluxo de caixa"""
        try:
            # Busca dados de fluxo de caixa no ERPNext
            result = self.connector.execute_method(
                "erpnext.accounts.report.cash_flow.cash_flow.execute",
                from_date=date_from,
                to_date=date_to,
                company="GovNext"  # Ajustar conforme necessário
            )
            
            if result.success:
                return IntegrationResult(
                    success=True,
                    data={
                        "report_type": "cash_flow",
                        "date_from": date_from,
                        "date_to": date_to,
                        "data": result.data
                    }
                )
            else:
                return result
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="CASH_FLOW_REPORT_FAILED"
            )