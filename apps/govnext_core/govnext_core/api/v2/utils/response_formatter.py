# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from typing import Any, Dict, Optional, List
import json
from frappe.utils import now_datetime
from .json_encoder import JSONEncoder


class ResponseFormatter:
    """
    Formatador padronizado de respostas para API v2.0
    
    Garante consistência nas respostas com:
    - Estrutura padronizada
    - Metadados de resposta
    - Códigos de status HTTP apropriados
    - Paginação
    - Logs de auditoria
    """
    
    def __init__(self):
        self.json_encoder = JSONEncoder()
    
    def success(self, data: Any = None, message: str = None, status_code: int = 200, 
                metadata: Dict = None, pagination: Dict = None) -> Dict:
        """
        Formata resposta de sucesso
        
        Args:
            data: Dados da resposta
            message: Mensagem de sucesso
            status_code: Código de status HTTP
            metadata: Metadados adicionais
            pagination: Informações de paginação
            
        Returns:
            Dict com resposta formatada
        """
        response = {
            "success": True,
            "status_code": status_code,
            "timestamp": now_datetime().isoformat(),
            "api_version": "2.0"
        }
        
        if message:
            response["message"] = message
        
        if data is not None:
            response["data"] = self._serialize_data(data)
        
        if metadata:
            response["metadata"] = metadata
        
        if pagination:
            response["pagination"] = pagination
        
        # Adicionar informações de performance
        if hasattr(frappe.local, 'request_start_time'):
            response["performance"] = {
                "response_time_ms": int((datetime.now() - frappe.local.request_start_time).total_seconds() * 1000)
            }
        
        frappe.response.update({
            "status_code": status_code,
            "data": response
        })
        
        return response
    
    def error(self, message: str, status_code: int = 400, error_code: str = None, 
              details: Any = None, validation_errors: List = None) -> Dict:
        """
        Formata resposta de erro
        
        Args:
            message: Mensagem de erro
            status_code: Código de status HTTP
            error_code: Código específico do erro
            details: Detalhes adicionais do erro
            validation_errors: Lista de erros de validação
            
        Returns:
            Dict com resposta de erro formatada
        """
        response = {
            "success": False,
            "status_code": status_code,
            "timestamp": now_datetime().isoformat(),
            "api_version": "2.0",
            "error": {
                "message": message
            }
        }
        
        if error_code:
            response["error"]["code"] = error_code
        
        if details:
            response["error"]["details"] = self._serialize_data(details)
        
        if validation_errors:
            response["error"]["validation_errors"] = validation_errors
        
        # Adicionar informações de debug em desenvolvimento
        if frappe.conf.get("developer_mode"):
            response["error"]["debug"] = {
                "traceback": frappe.get_traceback(),
                "request_id": frappe.local.request_id if hasattr(frappe.local, 'request_id') else None
            }
        
        frappe.response.update({
            "status_code": status_code,
            "data": response
        })
        
        # Log do erro
        self._log_error(response)
        
        return response
    
    def paginated_response(self, data: List, page: int, per_page: int, 
                          total: int, message: str = None) -> Dict:
        """
        Formata resposta paginada
        
        Args:
            data: Lista de dados
            page: Página atual
            per_page: Itens por página
            total: Total de itens
            message: Mensagem opcional
            
        Returns:
            Dict com resposta paginada
        """
        total_pages = (total + per_page - 1) // per_page
        
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "prev_page": page - 1 if page > 1 else None
        }
        
        return self.success(
            data=data,
            message=message,
            pagination=pagination,
            metadata={
                "result_count": len(data),
                "query_time": self._get_query_time()
            }
        )
    
    def validation_error(self, validation_errors: List[Dict]) -> Dict:
        """
        Formata resposta de erro de validação
        
        Args:
            validation_errors: Lista de erros de validação
            
        Returns:
            Dict com resposta de erro de validação
        """
        return self.error(
            message="Dados inválidos fornecidos",
            status_code=422,
            error_code="VALIDATION_ERROR",
            validation_errors=validation_errors
        )
    
    def not_found(self, resource: str = "Recurso") -> Dict:
        """Formata resposta de recurso não encontrado"""
        return self.error(
            message=f"{resource} não encontrado",
            status_code=404,
            error_code="NOT_FOUND"
        )
    
    def unauthorized(self, message: str = "Acesso não autorizado") -> Dict:
        """Formata resposta de acesso não autorizado"""
        return self.error(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED"
        )
    
    def forbidden(self, message: str = "Acesso proibido") -> Dict:
        """Formata resposta de acesso proibido"""
        return self.error(
            message=message,
            status_code=403,
            error_code="FORBIDDEN"
        )
    
    def rate_limit_exceeded(self, retry_after: int = 60) -> Dict:
        """Formata resposta de limite de taxa excedido"""
        response = self.error(
            message="Limite de requisições excedido",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "retry_after": retry_after
            }
        )
        
        # Adicionar header Retry-After
        frappe.response["headers"] = frappe.response.get("headers", {})
        frappe.response["headers"]["Retry-After"] = str(retry_after)
        
        return response
    
    def _serialize_data(self, data: Any) -> Any:
        """Serializa dados usando o encoder personalizado"""
        try:
            # Usar o encoder personalizado para lidar com tipos específicos do Frappe
            return json.loads(json.dumps(data, cls=self.json_encoder))
        except Exception as e:
            frappe.log_error(f"Erro na serialização de dados: {str(e)}")
            return str(data)
    
    def _log_error(self, response: Dict):
        """Registra erro no log de auditoria"""
        try:
            error_data = {
                "doctype": "API Error Log",
                "api_version": "2.0",
                "status_code": response["status_code"],
                "error_message": response["error"]["message"],
                "error_code": response["error"].get("code"),
                "timestamp": response["timestamp"],
                "user": frappe.session.user if frappe.session else "Guest",
                "ip_address": frappe.local.request_ip if frappe.local else None,
                "endpoint": frappe.request.path if frappe.request else None,
                "method": frappe.request.method if frappe.request else None,
                "user_agent": frappe.request.headers.get("User-Agent") if frappe.request else None
            }
            
            frappe.get_doc(error_data).insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            # Não fazer log do erro de logging para evitar loops
            pass
    
    def _get_query_time(self) -> Optional[float]:
        """Obtém tempo de consulta se disponível"""
        try:
            if hasattr(frappe.local, 'query_start_time'):
                return round((datetime.now() - frappe.local.query_start_time).total_seconds() * 1000, 2)
        except Exception:
            pass
        return None
    
    def add_headers(self, headers: Dict):
        """Adiciona headers personalizados à resposta"""
        if not frappe.response.get("headers"):
            frappe.response["headers"] = {}
        
        frappe.response["headers"].update(headers)
    
    def add_rate_limit_headers(self, limits: Dict, remaining: Dict):
        """Adiciona headers de rate limiting"""
        headers = {}
        
        for period, limit in limits.items():
            if period == "burst_limit":
                continue
            
            period_name = period.replace("requests_per_", "")
            headers[f"X-RateLimit-Limit-{period_name.title()}"] = str(limit)
            headers[f"X-RateLimit-Remaining-{period_name.title()}"] = str(remaining.get(period, 0))
        
        self.add_headers(headers)


# Instância global do formatador
response_formatter = ResponseFormatter()