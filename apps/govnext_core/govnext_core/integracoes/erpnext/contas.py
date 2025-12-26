"""
Sincronização de Contas entre ERPNext e GovNext.
Gerencia plano de contas, centros de custo e dimensões contábeis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint

from ..base import IntegrationResult, IntegrationError
from ..utils import DataTransformer, ValidationUtils, performance_monitor


class ERPNextContasSync:
    """
    Sincronizador de Contas entre ERPNext e GovNext.
    
    Funcionalidades:
    - Sincronizar Chart of Accounts
    - Integrar Cost Centers
    - Sincronizar Account Dimensions
    - Importar Budget e Budget Variance
    """
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        
        # Mapeamento Account
        self.account_mapping = {
            "nome_conta": "account_name",
            "codigo_conta": "account_number", 
            "tipo_conta": "account_type",
            "conta_pai": "parent_account",
            "eh_grupo": "is_group",
            "tipo_raiz": "root_type",
            "moeda": "account_currency",
            "ativo": "disabled"
        }
        
        # Mapeamento Cost Center
        self.cost_center_mapping = {
            "nome_centro_custo": "cost_center_name",
            "codigo_centro_custo": "cost_center_number",
            "centro_custo_pai": "parent_cost_center", 
            "eh_grupo": "is_group",
            "ativo": "disabled"
        }
        
        # Tipos de conta ERPNext -> GovNext
        self.account_type_mapping = {
            "Asset": "Ativo",
            "Liability": "Passivo", 
            "Equity": "Patrimônio Líquido",
            "Income": "Receita",
            "Expense": "Despesa",
            "Receivable": "Contas a Receber",
            "Payable": "Contas a Pagar",
            "Bank": "Banco",
            "Cash": "Caixa",
            "Stock": "Estoque",
            "Tax": "Imposto",
            "Chargeable": "Tributável"
        }
    
    @performance_monitor
    def sync(self, **kwargs) -> IntegrationResult:
        """Sincroniza dados contábeis do ERPNext"""
        try:
            sync_type = kwargs.get("sync_type", "all")  # all, accounts, cost_centers, budgets
            
            self.logger.info(f"Iniciando sincronização contábil - Tipo: {sync_type}")
            
            results = {}
            
            if sync_type in ["all", "accounts"]:
                results["accounts"] = self._sync_accounts()
            
            if sync_type in ["all", "cost_centers"]:
                results["cost_centers"] = self._sync_cost_centers()
            
            if sync_type in ["all", "budgets"]:
                results["budgets"] = self._sync_budgets()
            
            # Calcula estatísticas
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
            self.logger.error(f"Erro na sincronização contábil: {str(e)}")
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ACCOUNTS_SYNC_FAILED"
            )
    
    def _sync_accounts(self) -> IntegrationResult:
        """Sincroniza plano de contas"""
        try:
            # Busca contas no ERPNext (ordenado por hierarquia)
            accounts_result = self.connector.get_list(
                "Account",
                fields=list(self.account_mapping.values()) + ["company", "report_type", "balance"],
                limit=1000,
                order_by="lft"  # Left-right tree ordering
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
                    self.logger.error(f"Erro ao processar conta {account_data.get('account_name')}: {str(e)}")
            
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
    
    def _sync_cost_centers(self) -> IntegrationResult:
        """Sincroniza centros de custo"""
        try:
            # Busca centros de custo no ERPNext
            cost_centers_result = self.connector.get_list(
                "Cost Center",
                fields=list(self.cost_center_mapping.values()) + ["company"],
                limit=500,
                order_by="lft"
            )
            
            if not cost_centers_result.success:
                return cost_centers_result
            
            cost_centers = cost_centers_result.data.get("data", [])
            
            sync_stats = {
                "total": len(cost_centers),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            for cc_data in cost_centers:
                try:
                    result = self._process_cost_center(cc_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar centro de custo {cc_data.get('cost_center_name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de centros de custo concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="COST_CENTERS_SYNC_FAILED"
            )
    
    def _sync_budgets(self) -> IntegrationResult:
        """Sincroniza orçamentos"""
        try:
            # Busca orçamentos no ERPNext
            budgets_result = self.connector.get_list(
                "Budget",
                fields=["name", "cost_center", "fiscal_year", "budget_against",
                       "applicable_on_material_request", "applicable_on_purchase_order",
                       "applicable_on_booking_actual_expenses", "accounts"],
                limit=200
            )
            
            if not budgets_result.success:
                return budgets_result
            
            budgets = budgets_result.data.get("data", [])
            
            sync_stats = {
                "total": len(budgets),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            for budget_data in budgets:
                try:
                    result = self._process_budget(budget_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar orçamento {budget_data.get('name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de orçamentos concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="BUDGETS_SYNC_FAILED"
            )
    
    def _process_account(self, account_data: Dict[str, Any]) -> IntegrationResult:
        """Processa uma conta individual"""
        try:
            # Transforma dados
            govnext_data = DataTransformer.transform_erpnext_to_govnext(
                account_data,
                self.account_mapping
            )
            
            # Normaliza dados específicos
            govnext_data = self._normalize_account_data(govnext_data, account_data)
            
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
                    "codigo_erpnext": account_data.get("name"),
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
    
    def _process_cost_center(self, cc_data: Dict[str, Any]) -> IntegrationResult:
        """Processa um centro de custo individual"""
        try:
            # Transforma dados
            govnext_data = DataTransformer.transform_erpnext_to_govnext(
                cc_data,
                self.cost_center_mapping
            )
            
            # Normaliza dados
            govnext_data = self._normalize_cost_center_data(govnext_data, cc_data)
            
            # Verifica se já existe
            existing_cc = frappe.db.exists("Centro Custo", {
                "codigo_erpnext": cc_data.get("name")
            })
            
            if existing_cc:
                doc = frappe.get_doc("Centro Custo", existing_cc)
                doc.update(govnext_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Centro Custo",
                    "codigo_erpnext": cc_data.get("name"),
                    **govnext_data
                })
                doc.insert()
                action = "created"
            
            return IntegrationResult(
                success=True,
                data={"cost_center_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="COST_CENTER_PROCESS_FAILED"
            )
    
    def _process_budget(self, budget_data: Dict[str, Any]) -> IntegrationResult:
        """Processa um orçamento individual"""
        try:
            # Prepara dados do orçamento
            govnext_data = {
                "nome_orcamento": budget_data.get("name"),
                "centro_custo": budget_data.get("cost_center"),
                "ano_fiscal": budget_data.get("fiscal_year"),
                "tipo_orcamento": budget_data.get("budget_against"),
                "aplicavel_requisicao_material": cint(budget_data.get("applicable_on_material_request", 0)),
                "aplicavel_ordem_compra": cint(budget_data.get("applicable_on_purchase_order", 0)),
                "aplicavel_despesas_reais": cint(budget_data.get("applicable_on_booking_actual_expenses", 0)),
                "codigo_erpnext": budget_data.get("name")
            }
            
            # Verifica se já existe
            existing_budget = frappe.db.exists("Orcamento", {
                "codigo_erpnext": budget_data.get("name")
            })
            
            if existing_budget:
                doc = frappe.get_doc("Orcamento", existing_budget)
                doc.update(govnext_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Orcamento",
                    **govnext_data
                })
                doc.insert()
                action = "created"
            
            # Processa contas do orçamento
            if budget_data.get("accounts"):
                self._process_budget_accounts(doc.name, budget_data["accounts"])
            
            return IntegrationResult(
                success=True,
                data={"budget_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="BUDGET_PROCESS_FAILED"
            )
    
    def _normalize_account_data(self, data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza dados de conta"""
        normalized = data.copy()
        
        # Converte tipo de conta
        if "tipo_conta" in normalized:
            normalized["tipo_conta"] = self.account_type_mapping.get(
                normalized["tipo_conta"], 
                normalized["tipo_conta"]
            )
        
        # Inverte lógica do campo disabled
        if "ativo" in normalized:
            normalized["ativo"] = not cint(normalized["ativo"])
        
        # Converte is_group para boolean
        if "eh_grupo" in normalized:
            normalized["eh_grupo"] = cint(normalized["eh_grupo"])
        
        # Adiciona dados extras
        normalized["empresa"] = original_data.get("company")
        normalized["tipo_relatorio"] = original_data.get("report_type")
        normalized["saldo"] = flt(original_data.get("balance", 0))
        
        return normalized
    
    def _normalize_cost_center_data(self, data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza dados de centro de custo"""
        normalized = data.copy()
        
        # Inverte lógica do campo disabled
        if "ativo" in normalized:
            normalized["ativo"] = not cint(normalized["ativo"])
        
        # Converte is_group para boolean
        if "eh_grupo" in normalized:
            normalized["eh_grupo"] = cint(normalized["eh_grupo"])
        
        # Adiciona empresa
        normalized["empresa"] = original_data.get("company")
        
        return normalized
    
    def _process_budget_accounts(self, budget_name: str, accounts: List[Dict]):
        """Processa contas de um orçamento"""
        try:
            # Remove contas existentes
            frappe.db.delete("Item Orcamento", {"orcamento": budget_name})
            
            # Adiciona novas contas
            for account_data in accounts:
                item_doc = frappe.get_doc({
                    "doctype": "Item Orcamento",
                    "orcamento": budget_name,
                    "conta": account_data.get("account"),
                    "valor_orcado": DataTransformer.normalize_monetary_value(account_data.get("budget_amount", 0))
                })
                item_doc.insert()
                
        except Exception as e:
            self.logger.error(f"Erro ao processar contas do orçamento {budget_name}: {str(e)}")
    
    def export_chart_of_accounts(self, company: str = None) -> IntegrationResult:
        """Exporta plano de contas do GovNext para ERPNext"""
        try:
            # Busca contas no GovNext
            filters = {}
            if company:
                filters["empresa"] = company
            
            accounts = frappe.get_all(
                "Conta Contabil",
                fields=["name", "nome_conta", "codigo_conta", "tipo_conta", "conta_pai", "eh_grupo"],
                filters=filters,
                order_by="lft"
            )
            
            created_count = 0
            updated_count = 0
            errors = []
            
            for account in accounts:
                try:
                    # Transforma para formato ERPNext
                    erpnext_data = self._transform_account_to_erpnext(account)
                    
                    # Verifica se já existe no ERPNext
                    if account.get("codigo_erpnext"):
                        result = self.connector.update_document("Account", account["codigo_erpnext"], erpnext_data)
                        if result.success:
                            updated_count += 1
                    else:
                        result = self.connector.create_document("Account", erpnext_data)
                        if result.success:
                            created_count += 1
                            # Atualiza código ERPNext no GovNext
                            frappe.db.set_value("Conta Contabil", account["name"], 
                                              "codigo_erpnext", result.data.get("name"))
                    
                    if not result.success:
                        errors.append(f"Conta {account['nome_conta']}: {result.error_message}")
                        
                except Exception as e:
                    errors.append(f"Conta {account.get('nome_conta', 'N/A')}: {str(e)}")
            
            return IntegrationResult(
                success=len(errors) == 0,
                data={
                    "created": created_count,
                    "updated": updated_count,
                    "errors": errors,
                    "total_processed": len(accounts)
                }
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="CHART_EXPORT_FAILED"
            )
    
    def _transform_account_to_erpnext(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma conta do GovNext para formato ERPNext"""
        # Mapeamento reverso de tipos
        reverse_type_mapping = {v: k for k, v in self.account_type_mapping.items()}
        
        return {
            "account_name": account.get("nome_conta"),
            "account_number": account.get("codigo_conta"),
            "account_type": reverse_type_mapping.get(account.get("tipo_conta"), "Asset"),
            "parent_account": account.get("conta_pai"),
            "is_group": cint(account.get("eh_grupo", 0)),
            "account_currency": "BRL"
        }
    
    def get_account_balance(self, account_name: str, date: str = None) -> IntegrationResult:
        """Obtém saldo de conta do ERPNext"""
        try:
            params = {"account": account_name}
            if date:
                params["date"] = date
            
            result = self.connector.execute_method(
                "erpnext.accounts.utils.get_balance_on",
                **params
            )
            
            if result.success:
                return IntegrationResult(
                    success=True,
                    data={
                        "account": account_name,
                        "balance": flt(result.data),
                        "date": date or now_datetime().strftime("%Y-%m-%d")
                    }
                )
            else:
                return result
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ACCOUNT_BALANCE_FAILED"
            )