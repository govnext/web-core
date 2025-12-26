"""
Sincronização de Projects entre ERPNext e GovNext.
Gerencia projetos governamentais, orçamentos e cronogramas.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, flt, cint

from ..base import IntegrationResult, IntegrationError
from ..utils import DataTransformer, ValidationUtils, performance_monitor


class ERPNextProjectsSync:
    """
    Sincronizador de Projects entre ERPNext e GovNext.
    
    Funcionalidades:
    - Importar projetos do ERPNext
    - Sincronizar dados de orçamento
    - Atualizar status de projetos
    - Sincronizar tarefas e cronogramas
    - Integração com módulo de licitações
    """
    
    def __init__(self, connector):
        self.connector = connector
        self.logger = connector.logger
        
        # Mapeamento de campos ERPNext -> GovNext
        self.project_field_mapping = {
            "project_name": "name",
            "customer": "customer",
            "status": "status",
            "project_type": "project_type",
            "is_active": "is_active",
            "percent_complete": "percent_complete",
            "expected_start_date": "expected_start_date",
            "expected_end_date": "expected_end_date",
            "actual_start_date": "actual_start_date", 
            "actual_end_date": "actual_end_date",
            "total_costing_amount": "total_costing_amount",
            "total_billing_amount": "total_billing_amount",
            "cost_center": "cost_center",
            "department": "department",
            "priority": "priority",
            "notes": "notes"
        }
        
        # Mapeamento de status
        self.status_mapping = {
            "Open": "Aberto",
            "Completed": "Concluído", 
            "Cancelled": "Cancelado",
            "Hold": "Suspenso",
            "Template": "Modelo"
        }
    
    @performance_monitor
    def sync(self, **kwargs) -> IntegrationResult:
        """Sincroniza projetos do ERPNext"""
        try:
            sync_type = kwargs.get("sync_type", "full")  # full, incremental, specific
            project_filters = kwargs.get("filters", {})
            limit = kwargs.get("limit", 100)
            
            self.logger.info(f"Iniciando sincronização de projetos - Tipo: {sync_type}")
            
            if sync_type == "specific":
                project_name = kwargs.get("project_name")
                if not project_name:
                    return IntegrationResult(
                        success=False,
                        error_message="project_name é obrigatório para sincronização específica",
                        error_code="MISSING_PROJECT_NAME"
                    )
                return self._sync_specific_project(project_name)
            
            elif sync_type == "incremental":
                return self._sync_incremental_projects(project_filters, limit)
            
            else:  # full sync
                return self._sync_all_projects(project_filters, limit)
                
        except Exception as e:
            self.logger.error(f"Erro na sincronização de projetos: {str(e)}")
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PROJECT_SYNC_FAILED"
            )
    
    def _sync_all_projects(self, filters: Dict = None, limit: int = 100) -> IntegrationResult:
        """Sincroniza todos os projetos"""
        try:
            # Busca projetos no ERPNext
            projects_result = self.connector.get_list(
                "Project",
                fields=list(self.project_field_mapping.values()),
                filters=filters,
                limit=limit,
                order_by="modified desc"
            )
            
            if not projects_result.success:
                return projects_result
            
            projects = projects_result.data.get("data", [])
            
            sync_stats = {
                "total": len(projects),
                "created": 0,
                "updated": 0,
                "errors": 0,
                "skipped": 0
            }
            
            for project_data in projects:
                try:
                    result = self._process_project(project_data)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        self.logger.error(f"Erro ao processar projeto {project_data.get('name')}: {result.error_message}")
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar projeto {project_data.get('name')}: {str(e)}")
            
            self.logger.info(f"Sincronização de projetos concluída: {sync_stats}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats,
                metadata={"sync_type": "full"}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="FULL_PROJECT_SYNC_FAILED"
            )
    
    def _sync_incremental_projects(self, filters: Dict = None, limit: int = 100) -> IntegrationResult:
        """Sincroniza projetos modificados recentemente"""
        try:
            # Obtém última sincronização
            last_sync = self._get_last_sync_timestamp()
            
            # Adiciona filtro de data
            if filters is None:
                filters = {}
            
            filters["modified"] = [">", last_sync.strftime("%Y-%m-%d %H:%M:%S")]
            
            result = self._sync_all_projects(filters, limit)
            
            if result.success:
                # Atualiza timestamp da última sincronização
                self._update_last_sync_timestamp()
                result.metadata["sync_type"] = "incremental"
                result.metadata["last_sync"] = last_sync
            
            return result
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="INCREMENTAL_PROJECT_SYNC_FAILED"
            )
    
    def _sync_specific_project(self, project_name: str) -> IntegrationResult:
        """Sincroniza projeto específico"""
        try:
            # Busca projeto específico no ERPNext
            project_result = self.connector.get_document("Project", project_name)
            
            if not project_result.success:
                return project_result
            
            project_data = project_result.data
            result = self._process_project(project_data)
            
            if result.success:
                # Sincroniza tarefas do projeto
                tasks_result = self._sync_project_tasks(project_name)
                if tasks_result.success:
                    result.data["tasks_synced"] = tasks_result.data
            
            return result
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="SPECIFIC_PROJECT_SYNC_FAILED"
            )
    
    def _process_project(self, project_data: Dict[str, Any]) -> IntegrationResult:
        """Processa um projeto individual"""
        try:
            # Transforma dados do ERPNext para GovNext
            govnext_data = DataTransformer.transform_erpnext_to_govnext(
                project_data, 
                self.project_field_mapping
            )
            
            # Normaliza dados específicos
            govnext_data = self._normalize_project_data(govnext_data)
            
            # Verifica se projeto já existe no GovNext
            existing_project = frappe.db.exists("Projeto Governamental", {
                "codigo_erpnext": project_data.get("name")
            })
            
            if existing_project:
                # Atualiza projeto existente
                doc = frappe.get_doc("Projeto Governamental", existing_project)
                doc.update(govnext_data)
                doc.save()
                
                action = "updated"
                self.logger.info(f"Projeto atualizado: {doc.name}")
                
            else:
                # Cria novo projeto
                doc = frappe.get_doc({
                    "doctype": "Projeto Governamental",
                    "codigo_erpnext": project_data.get("name"),
                    **govnext_data
                })
                doc.insert()
                
                action = "created"
                self.logger.info(f"Projeto criado: {doc.name}")
            
            return IntegrationResult(
                success=True,
                data={
                    "project_name": doc.name,
                    "erpnext_id": project_data.get("name"),
                    "action": action
                },
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PROJECT_PROCESS_FAILED"
            )
    
    def _normalize_project_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza dados do projeto para padrões GovNext"""
        normalized = data.copy()
        
        # Normaliza status
        if "status" in normalized:
            normalized["status"] = self.status_mapping.get(normalized["status"], normalized["status"])
        
        # Normaliza datas
        date_fields = ["expected_start_date", "expected_end_date", "actual_start_date", "actual_end_date"]
        for field in date_fields:
            if field in normalized and normalized[field]:
                normalized[field] = DataTransformer.normalize_date(normalized[field])
        
        # Normaliza valores monetários
        money_fields = ["total_costing_amount", "total_billing_amount"]
        for field in money_fields:
            if field in normalized and normalized[field]:
                normalized[field] = DataTransformer.normalize_monetary_value(normalized[field])
        
        # Normaliza percentual
        if "percent_complete" in normalized:
            normalized["percent_complete"] = flt(normalized["percent_complete"])
        
        return normalized
    
    def _sync_project_tasks(self, project_name: str) -> IntegrationResult:
        """Sincroniza tarefas de um projeto"""
        try:
            # Busca tarefas do projeto no ERPNext
            tasks_result = self.connector.get_list(
                "Task",
                fields=["name", "subject", "status", "priority", "exp_start_date", "exp_end_date", 
                       "act_start_date", "act_end_date", "progress", "description"],
                filters={"project": project_name}
            )
            
            if not tasks_result.success:
                return tasks_result
            
            tasks = tasks_result.data.get("data", [])
            
            sync_stats = {
                "total": len(tasks),
                "created": 0,
                "updated": 0,
                "errors": 0
            }
            
            for task_data in tasks:
                try:
                    result = self._process_project_task(task_data, project_name)
                    if result.success:
                        if result.metadata.get("action") == "created":
                            sync_stats["created"] += 1
                        else:
                            sync_stats["updated"] += 1
                    else:
                        sync_stats["errors"] += 1
                        
                except Exception as e:
                    sync_stats["errors"] += 1
                    self.logger.error(f"Erro ao processar tarefa {task_data.get('name')}: {str(e)}")
            
            return IntegrationResult(
                success=True,
                data=sync_stats
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PROJECT_TASKS_SYNC_FAILED"
            )
    
    def _process_project_task(self, task_data: Dict[str, Any], project_name: str) -> IntegrationResult:
        """Processa uma tarefa individual do projeto"""
        try:
            # Transforma dados da tarefa
            govnext_task_data = {
                "titulo": task_data.get("subject"),
                "status": task_data.get("status"),
                "prioridade": task_data.get("priority"),
                "data_inicio_prevista": DataTransformer.normalize_date(task_data.get("exp_start_date")),
                "data_fim_prevista": DataTransformer.normalize_date(task_data.get("exp_end_date")),
                "data_inicio_real": DataTransformer.normalize_date(task_data.get("act_start_date")),
                "data_fim_real": DataTransformer.normalize_date(task_data.get("act_end_date")),
                "progresso": flt(task_data.get("progress", 0)),
                "descricao": task_data.get("description"),
                "codigo_erpnext": task_data.get("name")
            }
            
            # Busca projeto no GovNext
            project_doc = frappe.db.get_value("Projeto Governamental", 
                                            {"codigo_erpnext": project_name}, "name")
            
            if not project_doc:
                return IntegrationResult(
                    success=False,
                    error_message=f"Projeto {project_name} não encontrado no GovNext",
                    error_code="PROJECT_NOT_FOUND"
                )
            
            govnext_task_data["projeto"] = project_doc
            
            # Verifica se tarefa já existe
            existing_task = frappe.db.exists("Tarefa Projeto", {
                "codigo_erpnext": task_data.get("name")
            })
            
            if existing_task:
                doc = frappe.get_doc("Tarefa Projeto", existing_task)
                doc.update(govnext_task_data)
                doc.save()
                action = "updated"
            else:
                doc = frappe.get_doc({
                    "doctype": "Tarefa Projeto",
                    **govnext_task_data
                })
                doc.insert()
                action = "created"
            
            return IntegrationResult(
                success=True,
                data={"task_name": doc.name, "action": action},
                metadata={"action": action}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="TASK_PROCESS_FAILED"
            )
    
    def _get_last_sync_timestamp(self) -> datetime:
        """Obtém timestamp da última sincronização"""
        last_sync = frappe.db.get_single_value("Configurações Integração", "ultima_sync_projetos")
        
        if last_sync:
            return getdate(last_sync)
        else:
            # Se nunca sincronizou, busca projetos dos últimos 30 dias
            return now_datetime() - timedelta(days=30)
    
    def _update_last_sync_timestamp(self):
        """Atualiza timestamp da última sincronização"""
        frappe.db.set_single_value("Configurações Integração", 
                                 "ultima_sync_projetos", 
                                 now_datetime())
    
    def export_project_to_erpnext(self, govnext_project_name: str) -> IntegrationResult:
        """Exporta projeto do GovNext para ERPNext"""
        try:
            # Busca projeto no GovNext
            project_doc = frappe.get_doc("Projeto Governamental", govnext_project_name)
            
            # Transforma dados para formato ERPNext
            erpnext_data = self._transform_govnext_to_erpnext(project_doc)
            
            # Verifica se já existe no ERPNext
            if project_doc.codigo_erpnext:
                # Atualiza projeto existente
                result = self.connector.update_document("Project", project_doc.codigo_erpnext, erpnext_data)
                action = "updated"
            else:
                # Cria novo projeto
                result = self.connector.create_document("Project", erpnext_data)
                action = "created"
                
                if result.success:
                    # Salva código ERPNext no GovNext
                    project_doc.codigo_erpnext = result.data.get("name")
                    project_doc.save()
            
            if result.success:
                result.metadata = {"action": action}
                self.logger.info(f"Projeto {action} no ERPNext: {govnext_project_name}")
            
            return result
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="PROJECT_EXPORT_FAILED"
            )
    
    def _transform_govnext_to_erpnext(self, project_doc) -> Dict[str, Any]:
        """Transforma projeto do GovNext para formato ERPNext"""
        return {
            "project_name": project_doc.nome,
            "customer": project_doc.cliente if hasattr(project_doc, 'cliente') else None,
            "status": self._reverse_status_mapping(project_doc.status),
            "project_type": project_doc.tipo if hasattr(project_doc, 'tipo') else "External",
            "is_active": 1 if project_doc.ativo else 0,
            "expected_start_date": project_doc.data_inicio_prevista,
            "expected_end_date": project_doc.data_fim_prevista,
            "total_costing_amount": project_doc.orcamento_total if hasattr(project_doc, 'orcamento_total') else 0,
            "notes": project_doc.descricao if hasattr(project_doc, 'descricao') else ""
        }
    
    def _reverse_status_mapping(self, govnext_status: str) -> str:
        """Converte status do GovNext para ERPNext"""
        reverse_mapping = {v: k for k, v in self.status_mapping.items()}
        return reverse_mapping.get(govnext_status, "Open")