# -*- coding: utf-8 -*-
"""
Módulo de Integração com ERPNext
Conector para sincronização de dados entre GovNext e ERPNext
"""

import frappe
from frappe import _
import requests
import json
from datetime import datetime, timedelta
from ..utils.cache_manager import cached_function
from ..utils.audit import audit_operation

class ERPNextConnector:
    """Conector para integração com ERPNext"""
    
    def __init__(self):
        self.settings = self.get_integration_settings()
        self.session = requests.Session()
        self.base_url = self.settings.get("erpnext_url", "")
        self.api_key = self.settings.get("api_key", "")
        self.api_secret = self.settings.get("api_secret", "")
    
    def get_integration_settings(self):
        """Obter configurações de integração"""
        try:
            settings = frappe.get_single("ERPNext Integration Settings")
            return settings.as_dict()
        except:
            return {
                "erpnext_url": "http://localhost:8000",
                "api_key": "",
                "api_secret": "",
                "sync_enabled": False,
                "sync_interval_minutes": 30
            }
    
    def authenticate(self):
        """Autenticar com ERPNext"""
        try:
            headers = {
                "Authorization": f"token {self.api_key}:{self.api_secret}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(
                f"{self.base_url}/api/method/frappe.auth.get_logged_user",
                headers=headers
            )
            
            if response.status_code == 200:
                self.session.headers.update(headers)
                return True
            else:
                frappe.log_error(f"ERPNext Auth Error: {response.text}", "ERPNext Integration")
                return False
                
        except Exception as e:
            frappe.log_error(f"ERPNext Auth Exception: {str(e)}", "ERPNext Integration")
            return False
    
    @audit_operation("ERPNEXT_SYNC")
    def sync_projects(self):
        """Sincronizar projetos do ERPNext"""
        if not self.authenticate():
            return {"success": False, "error": "Falha na autenticação"}
        
        try:
            # Buscar projetos no ERPNext
            response = self.session.get(
                f"{self.base_url}/api/resource/Project",
                params={
                    "fields": ["name", "project_name", "status", "expected_start_date", "expected_end_date", "project_type", "cost_center", "total_expense_claim", "total_purchase_cost"],
                    "filters": [["status", "in", ["Open", "Completed"]]],
                    "limit_page_length": 1000
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Erro ao buscar projetos: {response.text}"}
            
            projects_data = response.json().get("data", [])
            synced_count = 0
            
            for project in projects_data:
                # Verificar se projeto já existe
                existing = frappe.db.exists("Government Project", {"erpnext_project_id": project["name"]})
                
                if existing:
                    # Atualizar projeto existente
                    gov_project = frappe.get_doc("Government Project", existing)
                else:
                    # Criar novo projeto
                    gov_project = frappe.new_doc("Government Project")
                    gov_project.erpnext_project_id = project["name"]
                
                # Atualizar dados
                gov_project.update({
                    "project_name": project["project_name"],
                    "status": self.map_project_status(project["status"]),
                    "start_date": project.get("expected_start_date"),
                    "end_date": project.get("expected_end_date"),
                    "project_type": project.get("project_type", "Public Works"),
                    "cost_center": project.get("cost_center"),
                    "total_budget": project.get("total_expense_claim", 0) + project.get("total_purchase_cost", 0),
                    "last_sync": frappe.utils.now()
                })
                
                if existing:
                    gov_project.save()
                else:
                    gov_project.insert()
                
                synced_count += 1
            
            return {
                "success": True,
                "synced_projects": synced_count,
                "message": f"{synced_count} projetos sincronizados com sucesso"
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "ERPNext Project Sync Error")
            return {"success": False, "error": str(e)}
    
    def sync_purchase_orders(self):
        """Sincronizar ordens de compra do ERPNext"""
        if not self.authenticate():
            return {"success": False, "error": "Falha na autenticação"}
        
        try:
            # Buscar POs dos últimos 30 dias
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            response = self.session.get(
                f"{self.base_url}/api/resource/Purchase Order",
                params={
                    "fields": ["name", "supplier", "transaction_date", "total", "status", "project", "cost_center"],
                    "filters": [["transaction_date", ">=", from_date], ["docstatus", "=", 1]],
                    "limit_page_length": 1000
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Erro ao buscar ordens de compra: {response.text}"}
            
            pos_data = response.json().get("data", [])
            synced_count = 0
            
            for po in pos_data:
                # Verificar se PO já existe
                existing = frappe.db.exists("Government Purchase Order", {"erpnext_po_id": po["name"]})
                
                if existing:
                    gov_po = frappe.get_doc("Government Purchase Order", existing)
                else:
                    gov_po = frappe.new_doc("Government Purchase Order")
                    gov_po.erpnext_po_id = po["name"]
                
                # Atualizar dados
                gov_po.update({
                    "supplier": po["supplier"],
                    "transaction_date": po["transaction_date"],
                    "total_amount": po["total"],
                    "status": po["status"],
                    "project": po.get("project"),
                    "cost_center": po.get("cost_center"),
                    "last_sync": frappe.utils.now()
                })
                
                if existing:
                    gov_po.save()
                else:
                    gov_po.insert()
                
                synced_count += 1
            
            return {
                "success": True,
                "synced_orders": synced_count,
                "message": f"{synced_count} ordens de compra sincronizadas"
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "ERPNext PO Sync Error")
            return {"success": False, "error": str(e)}
    
    def sync_gl_entries(self):
        """Sincronizar lançamentos contábeis do ERPNext"""
        if not self.authenticate():
            return {"success": False, "error": "Falha na autenticação"}
        
        try:
            # Buscar GL Entries dos últimos 7 dias
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            
            response = self.session.get(
                f"{self.base_url}/api/resource/GL Entry",
                params={
                    "fields": ["name", "account", "posting_date", "debit", "credit", "voucher_type", "voucher_no", "remarks"],
                    "filters": [["posting_date", ">=", from_date], ["is_cancelled", "=", 0]],
                    "limit_page_length": 5000
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"Erro ao buscar lançamentos: {response.text}"}
            
            gl_data = response.json().get("data", [])
            synced_count = 0
            
            for gl in gl_data:
                # Verificar se lançamento já existe
                existing = frappe.db.exists("GL Entry", {"erpnext_gl_id": gl["name"]})
                
                if not existing:
                    # Mapear conta ERPNext para conta PCASP
                    pcasp_account = self.map_account_to_pcasp(gl["account"])
                    
                    if pcasp_account:
                        gov_gl = frappe.new_doc("GL Entry")
                        gov_gl.update({
                            "erpnext_gl_id": gl["name"],
                            "account": pcasp_account,
                            "posting_date": gl["posting_date"],
                            "debit": gl["debit"],
                            "credit": gl["credit"],
                            "voucher_type": gl["voucher_type"],
                            "voucher_no": gl["voucher_no"],
                            "remarks": gl.get("remarks", ""),
                            "is_from_erpnext": True
                        })
                        
                        gov_gl.insert(ignore_permissions=True)
                        synced_count += 1
            
            return {
                "success": True,
                "synced_entries": synced_count,
                "message": f"{synced_count} lançamentos sincronizados"
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "ERPNext GL Sync Error")
            return {"success": False, "error": str(e)}
    
    def push_transparency_data(self):
        """Enviar dados de transparência para ERPNext"""
        if not self.authenticate():
            return {"success": False, "error": "Falha na autenticação"}
        
        try:
            # Preparar dados de transparência
            current_year = datetime.now().year
            
            # Resumo de receitas
            receitas = frappe.db.sql("""
                SELECT 
                    SUBSTRING(account, 1, 5) as categoria,
                    SUM(debit) as valor
                FROM `tabGL Entry`
                WHERE account LIKE '3.%'
                AND YEAR(posting_date) = %s
                AND is_cancelled = 0
                GROUP BY categoria
            """, [current_year], as_dict=True)
            
            # Resumo de despesas
            despesas = frappe.db.sql("""
                SELECT 
                    SUBSTRING(account, 1, 5) as categoria,
                    SUM(credit) as valor
                FROM `tabGL Entry`
                WHERE account LIKE '4.%'
                AND YEAR(posting_date) = %s
                AND is_cancelled = 0
                GROUP BY categoria
            """, [current_year], as_dict=True)
            
            transparency_data = {
                "year": current_year,
                "receitas": receitas,
                "despesas": despesas,
                "timestamp": frappe.utils.now()
            }
            
            # Enviar para ERPNext
            response = self.session.post(
                f"{self.base_url}/api/method/govnext.receive_transparency_data",
                json=transparency_data
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Dados de transparência enviados com sucesso"
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro ao enviar dados: {response.text}"
                }
                
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "ERPNext Push Data Error")
            return {"success": False, "error": str(e)}
    
    def map_project_status(self, erpnext_status):
        """Mapear status de projeto do ERPNext para GovNext"""
        mapping = {
            "Open": "Em Andamento",
            "Completed": "Concluído",
            "Cancelled": "Cancelado"
        }
        return mapping.get(erpnext_status, "Em Andamento")
    
    def map_account_to_pcasp(self, erpnext_account):
        """Mapear conta do ERPNext para conta PCASP"""
        # Buscar mapeamento configurado
        mapping = frappe.db.get_value(
            "ERPNext Account Mapping",
            {"erpnext_account": erpnext_account},
            "pcasp_account"
        )
        
        if mapping:
            return mapping
        
        # Mapeamento automático baseado em padrões
        if "Cash" in erpnext_account or "Bank" in erpnext_account:
            return "1.1.1.1.1.01.00"  # Caixa
        elif "Income" in erpnext_account:
            return "3.1.9.9.9.99.00"  # Outras receitas
        elif "Expense" in erpnext_account:
            return "4.1.3.9.9.99.00"  # Outras despesas
        
        return None  # Não mapear se não encontrar correspondência
    
    def test_connection(self):
        """Testar conexão com ERPNext"""
        try:
            if self.authenticate():
                response = self.session.get(f"{self.base_url}/api/method/ping")
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Conexão estabelecida com sucesso",
                        "server_info": response.json()
                    }
            
            return {
                "success": False,
                "error": "Falha na conexão ou autenticação"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro de conexão: {str(e)}"
            }
    
    def full_sync(self):
        """Sincronização completa"""
        results = {
            "projects": self.sync_projects(),
            "purchase_orders": self.sync_purchase_orders(),
            "gl_entries": self.sync_gl_entries()
        }
        
        # Enviar dados de volta se configurado
        if self.settings.get("push_transparency_data"):
            results["transparency_push"] = self.push_transparency_data()
        
        return {
            "success": True,
            "sync_results": results,
            "timestamp": frappe.utils.now()
        }

# Instância global
erpnext_connector = ERPNextConnector()

# APIs públicas
@frappe.whitelist()
def test_erpnext_connection():
    """API para testar conexão com ERPNext"""
    return erpnext_connector.test_connection()

@frappe.whitelist()
def sync_erpnext_projects():
    """API para sincronizar projetos"""
    return erpnext_connector.sync_projects()

@frappe.whitelist()
def sync_erpnext_purchase_orders():
    """API para sincronizar ordens de compra"""
    return erpnext_connector.sync_purchase_orders()

@frappe.whitelist()
def sync_erpnext_gl_entries():
    """API para sincronizar lançamentos contábeis"""
    return erpnext_connector.sync_gl_entries()

@frappe.whitelist()
def full_erpnext_sync():
    """API para sincronização completa"""
    return erpnext_connector.full_sync()

@frappe.whitelist()
def push_transparency_to_erpnext():
    """API para enviar dados de transparência"""
    return erpnext_connector.push_transparency_data()

# Scheduler para sincronização automática
def scheduled_erpnext_sync():
    """Sincronização agendada com ERPNext"""
    settings = frappe.get_single("ERPNext Integration Settings")
    
    if settings.sync_enabled:
        try:
            result = erpnext_connector.full_sync()
            frappe.log_error(
                json.dumps(result, indent=2),
                "ERPNext Scheduled Sync"
            )
        except Exception as e:
            frappe.log_error(
                f"Erro na sincronização agendada: {str(e)}",
                "ERPNext Sync Error"
            )