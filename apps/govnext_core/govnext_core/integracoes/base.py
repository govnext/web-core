"""
Classes base para o sistema de integrações do GovNext.
Implementa padrões de arquitetura para garantir consistência,
tolerância a falhas e monitoramento em todas as integrações.
"""

import json
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime


class IntegrationStatus(Enum):
    """Status possíveis para integrações"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTHENTICATING = "authenticating"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class IntegrationPriority(Enum):
    """Prioridades para processamento de integrações"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class IntegrationConfig:
    """Configuração padronizada para integrações"""
    name: str
    type: str
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    priority: IntegrationPriority = IntegrationPriority.MEDIUM
    auth_required: bool = True
    encryption_enabled: bool = True
    audit_level: str = "full"
    rate_limit: Optional[int] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationResult:
    """Resultado padronizado de integrações"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: now_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntegrationError(Exception):
    """Exceção customizada para integrações"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "INTEGRATION_ERROR"
        self.details = details or {}
        self.timestamp = now_datetime()


class BaseIntegration(ABC):
    """
    Classe base abstrata para todas as integrações do GovNext.
    
    Implementa padrões essenciais:
    - Configuração centralizada
    - Logging e auditoria
    - Tratamento de erros
    - Retry logic
    - Monitoramento de performance
    - Validação de dados
    """
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.status = IntegrationStatus.DISCONNECTED
        self.logger = self._setup_logger()
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "avg_response_time": 0,
            "last_call_time": None
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Configura logger específico para a integração"""
        logger = logging.getLogger(f"govnext.integrations.{self.config.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    @abstractmethod
    def connect(self) -> bool:
        """Estabelece conexão com o sistema externo"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Encerra conexão com o sistema externo"""
        pass
    
    @abstractmethod
    def test_connection(self) -> IntegrationResult:
        """Testa conectividade com o sistema externo"""
        pass
    
    @abstractmethod
    def sync_data(self, data_type: str, **kwargs) -> IntegrationResult:
        """Sincroniza dados com o sistema externo"""
        pass
    
    def execute_with_retry(self, operation, *args, **kwargs) -> IntegrationResult:
        """
        Executa operação com retry automático e tratamento de erros
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self.logger.info(f"Executando {operation.__name__} - Tentativa {attempt + 1}")
                
                result = operation(*args, **kwargs)
                
                # Atualiza métricas de sucesso
                execution_time = time.time() - start_time
                self._update_metrics(True, execution_time)
                
                self.logger.info(f"Operação {operation.__name__} executada com sucesso")
                return IntegrationResult(
                    success=True,
                    data=result,
                    execution_time=execution_time
                )
                
            except Exception as e:
                last_error = e
                self.logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                else:
                    break
        
        # Atualiza métricas de falha
        execution_time = time.time() - start_time
        self._update_metrics(False, execution_time)
        
        error_msg = f"Falha após {self.config.max_retries + 1} tentativas: {str(last_error)}"
        self.logger.error(error_msg)
        
        return IntegrationResult(
            success=False,
            error_message=error_msg,
            error_code="RETRY_EXHAUSTED",
            execution_time=execution_time,
            metadata={"attempts": self.config.max_retries + 1}
        )
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Valida dados contra um schema definido"""
        try:
            # Implementação básica de validação
            # Em produção, usar bibliotecas como jsonschema
            for field, field_type in schema.items():
                if field not in data:
                    raise IntegrationError(f"Campo obrigatório ausente: {field}")
                
                if not isinstance(data[field], field_type):
                    raise IntegrationError(f"Tipo inválido para campo {field}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação de dados: {str(e)}")
            raise IntegrationError(f"Validação de dados falhou: {str(e)}")
    
    def _update_metrics(self, success: bool, execution_time: float):
        """Atualiza métricas da integração"""
        self.metrics["total_calls"] += 1
        self.metrics["last_call_time"] = now_datetime()
        
        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1
        
        # Calcula média de tempo de resposta
        total_time = self.metrics["avg_response_time"] * (self.metrics["total_calls"] - 1)
        self.metrics["avg_response_time"] = (total_time + execution_time) / self.metrics["total_calls"]
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual da integração"""
        return {
            "name": self.config.name,
            "type": self.config.type,
            "status": self.status.value,
            "enabled": self.config.enabled,
            "metrics": self.metrics,
            "last_check": now_datetime()
        }
    
    def audit_log(self, action: str, data: Dict[str, Any] = None, user: str = None):
        """Registra ações para auditoria"""
        if self.config.audit_level == "none":
            return
        
        audit_data = {
            "integration": self.config.name,
            "action": action,
            "user": user or frappe.session.user,
            "timestamp": now_datetime(),
            "data": data if self.config.audit_level == "full" else None,
            "ip_address": frappe.local.request_ip if frappe.local.request_ip else None
        }
        
        # Em produção, salvar em tabela específica de auditoria
        self.logger.info(f"AUDIT: {json.dumps(audit_data, default=str)}")


class IntegrationManager:
    """
    Gerenciador central de integrações.
    Responsável por registrar, configurar e monitorar todas as integrações.
    """
    
    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.logger = logging.getLogger("govnext.integration_manager")
    
    def register_integration(self, integration: BaseIntegration):
        """Registra uma nova integração"""
        self.integrations[integration.config.name] = integration
        self.logger.info(f"Integração registrada: {integration.config.name}")
    
    def get_integration(self, name: str) -> Optional[BaseIntegration]:
        """Obtém integração por nome"""
        return self.integrations.get(name)
    
    def get_all_integrations(self) -> Dict[str, BaseIntegration]:
        """Retorna todas as integrações registradas"""
        return self.integrations
    
    def test_all_connections(self) -> Dict[str, IntegrationResult]:
        """Testa conexão de todas as integrações"""
        results = {}
        
        for name, integration in self.integrations.items():
            if integration.config.enabled:
                try:
                    results[name] = integration.test_connection()
                except Exception as e:
                    results[name] = IntegrationResult(
                        success=False,
                        error_message=str(e),
                        error_code="CONNECTION_TEST_FAILED"
                    )
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status geral do sistema de integrações"""
        total_integrations = len(self.integrations)
        enabled_integrations = sum(1 for i in self.integrations.values() if i.config.enabled)
        connected_integrations = sum(1 for i in self.integrations.values() 
                                   if i.status == IntegrationStatus.CONNECTED)
        
        return {
            "total_integrations": total_integrations,
            "enabled_integrations": enabled_integrations,
            "connected_integrations": connected_integrations,
            "status": "healthy" if connected_integrations == enabled_integrations else "degraded",
            "timestamp": now_datetime()
        }


# Instância global do gerenciador
integration_manager = IntegrationManager()