"""
Conector principal para integração com ERPNext.
Responsável pela conexão, autenticação e operações básicas.
"""

import requests
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt

from ..base import BaseIntegration, IntegrationConfig, IntegrationResult, IntegrationError, IntegrationStatus
from ..utils import DataTransformer, ValidationUtils, LoggerUtils, performance_monitor, retry_on_failure


class ERPNextConnector(BaseIntegration):
    """
    Conector principal para ERPNext.
    
    Características:
    - Autenticação via API Key/Secret
    - Suporte a múltiplas instâncias ERPNext
    - Cache de conexões
    - Retry automático
    - Monitoramento de performance
    """
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        
        # Configurações específicas do ERPNext
        self.base_url = config.custom_settings.get("base_url", "").rstrip("/")
        self.api_key = config.custom_settings.get("api_key")
        self.api_secret = config.custom_settings.get("api_secret")
        self.version = config.custom_settings.get("version", "14")
        
        # Headers padrão
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Session para reutilizar conexões
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        if not all([self.base_url, self.api_key, self.api_secret]):
            raise IntegrationError(
                "Configuração incompleta para ERPNext: base_url, api_key e api_secret são obrigatórios",
                "ERPNEXT_CONFIG_INCOMPLETE"
            )
    
    def connect(self) -> bool:
        """Estabelece conexão com ERPNext"""
        try:
            self.logger.info(f"Conectando ao ERPNext: {self.base_url}")
            
            # Testa conectividade básica
            result = self.test_connection()
            
            if result.success:
                self.status = IntegrationStatus.CONNECTED
                self.logger.info("Conexão com ERPNext estabelecida com sucesso")
                return True
            else:
                self.status = IntegrationStatus.ERROR
                self.logger.error(f"Falha na conexão com ERPNext: {result.error_message}")
                return False
                
        except Exception as e:
            self.status = IntegrationStatus.ERROR
            self.logger.error(f"Erro ao conectar com ERPNext: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Encerra conexão com ERPNext"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            
            self.status = IntegrationStatus.DISCONNECTED
            self.logger.info("Conexão com ERPNext encerrada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao desconectar do ERPNext: {str(e)}")
            return False
    
    @performance_monitor
    def test_connection(self) -> IntegrationResult:
        """Testa conectividade com ERPNext"""
        try:
            # Faz uma requisição simples para verificar conectividade
            response = self._make_request("GET", "/api/method/frappe.auth.get_logged_user")
            
            if response.get("message"):
                return IntegrationResult(
                    success=True,
                    data={
                        "connected": True,
                        "user": response.get("message"),
                        "version": self.version,
                        "url": self.base_url
                    }
                )
            else:
                return IntegrationResult(
                    success=False,
                    error_message="Resposta inválida do ERPNext",
                    error_code="ERPNEXT_INVALID_RESPONSE"
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_CONNECTION_FAILED"
            )
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """Faz requisição HTTP para ERPNext com autenticação"""
        url = f"{self.base_url}{endpoint}"
        
        # Adiciona autenticação
        auth_params = {
            "api_key": self.api_key,
            "api_secret": self.api_secret
        }
        
        if params:
            params.update(auth_params)
        else:
            params = auth_params
        
        try:
            self.logger.debug(f"Fazendo requisição {method} para {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                params=params,
                timeout=self.config.timeout
            )
            
            # Log da requisição
            LoggerUtils.log_integration_call(
                self.logger,
                "erpnext",
                f"{method} {endpoint}",
                data=data,
                response=response.json() if response.content else None,
                success=response.status_code < 400
            )
            
            if response.status_code >= 400:
                error_msg = f"ERPNext API retornou erro {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg += f": {error_data['message']}"
                except:
                    pass
                
                raise IntegrationError(error_msg, f"ERPNEXT_HTTP_{response.status_code}")
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise IntegrationError("Timeout na requisição para ERPNext", "ERPNEXT_TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise IntegrationError("Erro de conexão com ERPNext", "ERPNEXT_CONNECTION_ERROR")
        except Exception as e:
            raise IntegrationError(f"Erro na requisição para ERPNext: {str(e)}", "ERPNEXT_REQUEST_ERROR")
    
    def get_document(self, doctype: str, name: str) -> IntegrationResult:
        """Obtém documento do ERPNext"""
        try:
            endpoint = f"/api/resource/{doctype}/{name}"
            response = self._make_request("GET", endpoint)
            
            return IntegrationResult(
                success=True,
                data=response.get("data", {})
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_GET_DOCUMENT_FAILED"
            )
    
    def create_document(self, doctype: str, doc_data: Dict[str, Any]) -> IntegrationResult:
        """Cria documento no ERPNext"""
        try:
            endpoint = f"/api/resource/{doctype}"
            
            # Valida dados obrigatórios
            required_fields = self._get_required_fields(doctype)
            missing_fields = ValidationUtils.validate_required_fields(doc_data, required_fields)
            
            if missing_fields:
                return IntegrationResult(
                    success=False,
                    error_message=f"Campos obrigatórios ausentes: {', '.join(missing_fields)}",
                    error_code="ERPNEXT_MISSING_REQUIRED_FIELDS"
                )
            
            response = self._make_request("POST", endpoint, data=doc_data)
            
            return IntegrationResult(
                success=True,
                data=response.get("data", {})
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_CREATE_DOCUMENT_FAILED"
            )
    
    def update_document(self, doctype: str, name: str, doc_data: Dict[str, Any]) -> IntegrationResult:
        """Atualiza documento no ERPNext"""
        try:
            endpoint = f"/api/resource/{doctype}/{name}"
            response = self._make_request("PUT", endpoint, data=doc_data)
            
            return IntegrationResult(
                success=True,
                data=response.get("data", {})
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_UPDATE_DOCUMENT_FAILED"
            )
    
    def delete_document(self, doctype: str, name: str) -> IntegrationResult:
        """Exclui documento no ERPNext"""
        try:
            endpoint = f"/api/resource/{doctype}/{name}"
            self._make_request("DELETE", endpoint)
            
            return IntegrationResult(
                success=True,
                data={"deleted": True, "doctype": doctype, "name": name}
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_DELETE_DOCUMENT_FAILED"
            )
    
    def get_list(self, doctype: str, fields: List[str] = None, filters: Dict = None, 
                 limit: int = 20, order_by: str = None) -> IntegrationResult:
        """Obtém lista de documentos do ERPNext"""
        try:
            endpoint = f"/api/resource/{doctype}"
            
            params = {}
            if fields:
                params["fields"] = json.dumps(fields)
            if filters:
                params["filters"] = json.dumps(filters)
            if limit:
                params["limit_page_length"] = limit
            if order_by:
                params["order_by"] = order_by
            
            response = self._make_request("GET", endpoint, params=params)
            
            return IntegrationResult(
                success=True,
                data={
                    "data": response.get("data", []),
                    "total": len(response.get("data", []))
                }
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_GET_LIST_FAILED"
            )
    
    def execute_method(self, method_name: str, **kwargs) -> IntegrationResult:
        """Executa método personalizado no ERPNext"""
        try:
            endpoint = f"/api/method/{method_name}"
            response = self._make_request("POST", endpoint, data=kwargs)
            
            return IntegrationResult(
                success=True,
                data=response.get("message", {})
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_EXECUTE_METHOD_FAILED"
            )
    
    def sync_data(self, data_type: str, **kwargs) -> IntegrationResult:
        """Sincroniza dados específicos com ERPNext"""
        try:
            if data_type == "projects":
                from .projects import ERPNextProjectsSync
                sync_handler = ERPNextProjectsSync(self)
                return sync_handler.sync(**kwargs)
            
            elif data_type == "financeiro":
                from .financeiro import ERPNextFinanceiroSync
                sync_handler = ERPNextFinanceiroSync(self)
                return sync_handler.sync(**kwargs)
            
            elif data_type == "contas":
                from .contas import ERPNextContasSync
                sync_handler = ERPNextContasSync(self)
                return sync_handler.sync(**kwargs)
            
            elif data_type == "compras":
                from .compras import ERPNextComprasSync
                sync_handler = ERPNextComprasSync(self)
                return sync_handler.sync(**kwargs)
            
            elif data_type == "documentos":
                from .documentos import ERPNextDocumentosSync
                sync_handler = ERPNextDocumentosSync(self)
                return sync_handler.sync(**kwargs)
            
            else:
                return IntegrationResult(
                    success=False,
                    error_message=f"Tipo de sincronização não suportado: {data_type}",
                    error_code="ERPNEXT_UNSUPPORTED_SYNC_TYPE"
                )
                
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_SYNC_FAILED"
            )
    
    def _get_required_fields(self, doctype: str) -> List[str]:
        """Obtém campos obrigatórios para um doctype"""
        # Mapeamento básico de campos obrigatórios por doctype
        required_fields_map = {
            "Project": ["project_name"],
            "Customer": ["customer_name"],
            "Supplier": ["supplier_name"],
            "Item": ["item_code", "item_name"],
            "Sales Order": ["customer"],
            "Purchase Order": ["supplier"],
            "Sales Invoice": ["customer"],
            "Purchase Invoice": ["supplier"],
        }
        
        return required_fields_map.get(doctype, [])
    
    def get_server_info(self) -> IntegrationResult:
        """Obtém informações do servidor ERPNext"""
        try:
            response = self._make_request("GET", "/api/method/frappe.utils.get_site_info")
            
            return IntegrationResult(
                success=True,
                data=response.get("message", {})
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="ERPNEXT_GET_SERVER_INFO_FAILED"
            )