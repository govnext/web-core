"""
Utilitários para o sistema de integrações do GovNext.
Inclui funções para transformação de dados, validação, criptografia,
retry logic e logging avançado.
"""

import json
import time
import hashlib
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Union
from functools import wraps
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint, cstr, get_datetime

from .base import IntegrationError, IntegrationResult


class DataTransformer:
    """Utilitários para transformação de dados entre sistemas"""
    
    @staticmethod
    def normalize_cpf_cnpj(document: str) -> str:
        """Normaliza CPF/CNPJ removendo caracteres especiais"""
        if not document:
            return ""
        return ''.join(filter(str.isdigit, document))
    
    @staticmethod
    def format_cpf_cnpj(document: str) -> str:
        """Formata CPF/CNPJ com máscaras"""
        clean_doc = DataTransformer.normalize_cpf_cnpj(document)
        
        if len(clean_doc) == 11:  # CPF
            return f"{clean_doc[:3]}.{clean_doc[3:6]}.{clean_doc[6:9]}-{clean_doc[9:]}"
        elif len(clean_doc) == 14:  # CNPJ
            return f"{clean_doc[:2]}.{clean_doc[2:5]}.{clean_doc[5:8]}/{clean_doc[8:12]}-{clean_doc[12:]}"
        
        return document
    
    @staticmethod
    def normalize_monetary_value(value: Union[str, float, Decimal]) -> float:
        """Normaliza valores monetários"""
        if isinstance(value, str):
            # Remove caracteres não numéricos exceto ponto e vírgula
            clean_value = ''.join(c for c in value if c.isdigit() or c in '.,')
            
            # Trata vírgula como separador decimal se for o último
            if ',' in clean_value and clean_value.rfind(',') > clean_value.rfind('.'):
                clean_value = clean_value.replace('.', '').replace(',', '.')
            else:
                clean_value = clean_value.replace(',', '')
            
            try:
                return float(clean_value)
            except ValueError:
                return 0.0
        
        return flt(value)
    
    @staticmethod
    def format_monetary_value(value: float, currency: str = "BRL") -> str:
        """Formata valores monetários"""
        if currency == "BRL":
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{value:.2f}"
    
    @staticmethod
    def normalize_date(date_value: Union[str, datetime]) -> Optional[datetime]:
        """Normaliza datas para formato padrão"""
        if not date_value:
            return None
        
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Tenta vários formatos de data
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def transform_erpnext_to_govnext(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Transforma dados do ERPNext para formato GovNext"""
        result = {}
        
        for govnext_field, erpnext_field in mapping.items():
            if '.' in erpnext_field:
                # Suporte a campos aninhados
                value = data
                for field_part in erpnext_field.split('.'):
                    value = value.get(field_part) if isinstance(value, dict) else None
                    if value is None:
                        break
                result[govnext_field] = value
            else:
                result[govnext_field] = data.get(erpnext_field)
        
        return result
    
    @staticmethod
    def transform_govnext_to_erpnext(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Transforma dados do GovNext para formato ERPNext"""
        result = {}
        
        for erpnext_field, govnext_field in mapping.items():
            if govnext_field in data:
                result[erpnext_field] = data[govnext_field]
        
        return result


class ValidationUtils:
    """Utilitários para validação de dados"""
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Valida CPF"""
        cpf = DataTransformer.normalize_cpf_cnpj(cpf)
        
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Validação do primeiro dígito
        sum1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        if int(cpf[9]) != digit1:
            return False
        
        # Validação do segundo dígito
        sum2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        return int(cpf[10]) == digit2
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """Valida CNPJ"""
        cnpj = DataTransformer.normalize_cpf_cnpj(cnpj)
        
        if len(cnpj) != 14:
            return False
        
        # Validação do primeiro dígito
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(int(cnpj[i]) * weights1[i] for i in range(12))
        digit1 = 11 - (sum1 % 11)
        if digit1 >= 10:
            digit1 = 0
        
        if int(cnpj[12]) != digit1:
            return False
        
        # Validação do segundo dígito
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(int(cnpj[i]) * weights2[i] for i in range(13))
        digit2 = 11 - (sum2 % 11)
        if digit2 >= 10:
            digit2 = 0
        
        return int(cnpj[13]) == digit2
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida e-mail"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Valida campos obrigatórios"""
        missing_fields = []
        
        for field in required_fields:
            if '.' in field:
                # Suporte a campos aninhados
                value = data
                for field_part in field.split('.'):
                    if isinstance(value, dict) and field_part in value:
                        value = value[field_part]
                    else:
                        value = None
                        break
                
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_fields.append(field)
            else:
                if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
                    missing_fields.append(field)
        
        return missing_fields


class CryptoUtils:
    """Utilitários para criptografia e segurança"""
    
    @staticmethod
    def hash_data(data: str, algorithm: str = "sha256") -> str:
        """Cria hash de dados"""
        if algorithm == "md5":
            return hashlib.md5(data.encode()).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(data.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        else:
            raise ValueError(f"Algoritmo não suportado: {algorithm}")
    
    @staticmethod
    def generate_api_key() -> str:
        """Gera chave de API segura"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """Mascara dados sensíveis"""
        if len(data) <= visible_chars * 2:
            return mask_char * len(data)
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars * 2) + data[-visible_chars:]


class RetryUtils:
    """Utilitários para retry logic"""
    
    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """Calcula delay com backoff exponencial"""
        delay = base_delay * (2 ** attempt)
        return min(delay, max_delay)
    
    @staticmethod
    def should_retry(exception: Exception, retryable_exceptions: List[type] = None) -> bool:
        """Determina se deve tentar novamente baseado na exceção"""
        if retryable_exceptions is None:
            retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                IntegrationError
            ]
        
        return any(isinstance(exception, exc_type) for exc_type in retryable_exceptions)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: bool = True):
    """Decorator para retry automático"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries and RetryUtils.should_retry(e):
                        sleep_time = RetryUtils.exponential_backoff(attempt, delay) if backoff else delay
                        time.sleep(sleep_time)
                        continue
                    else:
                        break
            
            raise last_exception
        
        return wrapper
    return decorator


class LoggerUtils:
    """Utilitários avançados para logging"""
    
    @staticmethod
    def setup_integration_logger(name: str, level: str = "INFO") -> logging.Logger:
        """Configura logger específico para integração"""
        logger = logging.getLogger(f"govnext.integrations.{name}")
        
        # Remove handlers existentes para evitar duplicação
        logger.handlers.clear()
        
        # Set level
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (se configurado)
        log_file = frappe.get_conf().get("integration_log_file")
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception:
                pass  # Ignora se não conseguir criar arquivo de log
        
        return logger
    
    @staticmethod
    def log_integration_call(logger: logging.Logger, integration_name: str, operation: str, 
                           data: Dict[str, Any] = None, response: Dict[str, Any] = None,
                           duration: float = None, success: bool = True):
        """Log estruturado para chamadas de integração"""
        log_data = {
            "integration": integration_name,
            "operation": operation,
            "timestamp": now_datetime().isoformat(),
            "duration_ms": round(duration * 1000) if duration else None,
            "success": success,
            "user": frappe.session.user if frappe.session.user else "system",
            "ip": frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else None
        }
        
        if data:
            # Mascara dados sensíveis
            safe_data = LoggerUtils._mask_sensitive_fields(data)
            log_data["request_data"] = safe_data
        
        if response:
            safe_response = LoggerUtils._mask_sensitive_fields(response)
            log_data["response_data"] = safe_response
        
        level = logging.INFO if success else logging.ERROR
        logger.log(level, f"Integration Call: {json.dumps(log_data, default=str)}")
    
    @staticmethod
    def _mask_sensitive_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mascara campos sensíveis nos logs"""
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'authorization',
            'cpf', 'cnpj', 'rg', 'passport', 'credit_card'
        }
        
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            if any(sensitive_field in key.lower() for sensitive_field in sensitive_fields):
                masked_data[key] = CryptoUtils.mask_sensitive_data(str(value)) if value else None
            elif isinstance(value, dict):
                masked_data[key] = LoggerUtils._mask_sensitive_fields(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    LoggerUtils._mask_sensitive_fields(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data


def performance_monitor(func: Callable) -> Callable:
    """Decorator para monitorar performance de funções"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            raise
        finally:
            duration = time.time() - start_time
            
            # Log performance
            logger = logging.getLogger("govnext.performance")
            logger.info(f"Function: {func.__name__}, Duration: {duration:.3f}s, Success: {success}")
            
            # Salva métricas no cache para análise posterior
            metric_key = f"perf_{func.__name__}_{int(time.time())}"
            frappe.cache().set_value(metric_key, {
                "function": func.__name__,
                "duration": duration,
                "success": success,
                "timestamp": now_datetime().isoformat()
            }, expires_in_sec=86400)  # 24 horas
        
        return result
    
    return wrapper