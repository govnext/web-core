# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

import frappe
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from frappe import _
from frappe.utils import get_datetime, now_datetime
import hashlib


class RateLimiter:
    """
    Sistema de Rate Limiting para API v2.0
    
    Implementa diferentes estratégias de limitação:
    - Por usuário autenticado
    - Por IP para usuários anônimos
    - Por endpoint específico
    - Sliding window counter
    - Burst protection
    """
    
    def __init__(self):
        self.default_limits = {
            "authenticated": {
                "requests_per_minute": 100,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "burst_limit": 20  # Máximo de requisições em rajada
            },
            "anonymous": {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "requests_per_day": 1000,
                "burst_limit": 5
            },
            "admin": {
                "requests_per_minute": 500,
                "requests_per_hour": 5000,
                "requests_per_day": 50000,
                "burst_limit": 100
            }
        }
        
        # Limites específicos por endpoint
        self.endpoint_limits = {
            "/api/v2/auth/login": {
                "requests_per_minute": 5,
                "requests_per_hour": 20,
                "burst_limit": 3
            },
            "/api/v2/financial/pix": {
                "requests_per_minute": 50,
                "requests_per_hour": 500,
                "burst_limit": 10
            },
            "/api/v2/opendata/export": {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "burst_limit": 5
            }
        }
    
    def check_rate_limit(self, user: Optional[str] = None, ip_address: str = None, 
                        endpoint: str = None) -> Tuple[bool, Dict]:
        """
        Verifica se a requisição está dentro dos limites
        
        Args:
            user: Usuário autenticado (opcional)
            ip_address: Endereço IP da requisição
            endpoint: Endpoint sendo acessado
            
        Returns:
            Tuple (permitido: bool, info: dict)
        """
        try:
            # Determinar identificador e tipo de usuário
            if user:
                identifier = f"user:{user}"
                user_type = self._get_user_type(user)
            else:
                identifier = f"ip:{ip_address}"
                user_type = "anonymous"
            
            # Obter limites aplicáveis
            limits = self._get_applicable_limits(user_type, endpoint)
            
            # Verificar cada tipo de limite
            for period, limit in limits.items():
                if period == "burst_limit":
                    continue
                    
                allowed, remaining, reset_time = self._check_period_limit(
                    identifier, period, limit, endpoint
                )
                
                if not allowed:
                    return False, {
                        "error": "rate_limit_exceeded",
                        "message": _("Limite de requisições excedido para {}").format(period.replace("_", " ")),
                        "period": period,
                        "limit": limit,
                        "remaining": remaining,
                        "reset_time": reset_time.isoformat() if reset_time else None,
                        "retry_after": self._calculate_retry_after(reset_time)
                    }
            
            # Verificar burst protection
            if not self._check_burst_limit(identifier, limits.get("burst_limit", 10)):
                return False, {
                    "error": "burst_limit_exceeded",
                    "message": _("Muitas requisições em sequência. Aguarde alguns segundos."),
                    "retry_after": 60
                }
            
            # Incrementar contadores
            self._increment_counters(identifier, endpoint)
            
            # Retornar informações de limite para headers
            remaining_info = self._get_remaining_limits(identifier, limits)
            
            return True, {
                "limits": limits,
                "remaining": remaining_info,
                "identifier": identifier
            }
            
        except Exception as e:
            frappe.log_error(f"Erro no rate limiting: {str(e)}", "Rate Limiter Error")
            # Em caso de erro, permitir requisição (fail open)
            return True, {"error": "rate_limiter_error"}
    
    def _get_user_type(self, user: str) -> str:
        """Determina o tipo de usuário para aplicar limites apropriados"""
        try:
            if user == "Administrator":
                return "admin"
            
            roles = frappe.get_roles(user)
            if "System Manager" in roles or "Administrator" in roles:
                return "admin"
            
            return "authenticated"
            
        except Exception:
            return "authenticated"
    
    def _get_applicable_limits(self, user_type: str, endpoint: str = None) -> Dict:
        """Obtém os limites aplicáveis baseado no tipo de usuário e endpoint"""
        base_limits = self.default_limits.get(user_type, self.default_limits["anonymous"])
        
        # Aplicar limites específicos do endpoint se existirem
        if endpoint and endpoint in self.endpoint_limits:
            endpoint_limits = self.endpoint_limits[endpoint]
            # Usar o menor entre os limites base e específicos do endpoint
            return {
                key: min(base_limits.get(key, float('inf')), endpoint_limits.get(key, float('inf')))
                for key in set(base_limits.keys()) | set(endpoint_limits.keys())
            }
        
        return base_limits
    
    def _check_period_limit(self, identifier: str, period: str, limit: int, 
                           endpoint: str = None) -> Tuple[bool, int, Optional[datetime]]:
        """
        Verifica limite para um período específico usando sliding window
        
        Returns:
            Tuple (permitido, restante, próximo_reset)
        """
        try:
            window_size = self._get_window_size(period)
            now = now_datetime()
            window_start = now - window_size
            
            # Chave para o cache/banco
            cache_key = f"rate_limit:{identifier}:{period}"
            if endpoint:
                cache_key += f":{hashlib.md5(endpoint.encode()).hexdigest()[:8]}"
            
            # Obter histórico de requisições do período
            requests = self._get_request_history(cache_key, window_start, now)
            
            current_count = len(requests)
            remaining = max(0, limit - current_count)
            
            # Calcular próximo reset (início da próxima janela)
            if requests:
                oldest_request = min(requests)
                next_reset = oldest_request + window_size
            else:
                next_reset = now + window_size
            
            return current_count < limit, remaining, next_reset
            
        except Exception as e:
            frappe.log_error(f"Erro ao verificar limite do período {period}: {str(e)}")
            return True, limit, None
    
    def _check_burst_limit(self, identifier: str, burst_limit: int) -> bool:
        """Verifica proteção contra rajadas de requisições"""
        try:
            now = now_datetime()
            burst_window = now - timedelta(seconds=60)  # Janela de 1 minuto
            
            cache_key = f"rate_limit:{identifier}:burst"
            requests = self._get_request_history(cache_key, burst_window, now)
            
            return len(requests) < burst_limit
            
        except Exception:
            return True
    
    def _increment_counters(self, identifier: str, endpoint: str = None):
        """Incrementa contadores de requisições"""
        try:
            now = now_datetime()
            
            # Registrar requisição para diferentes períodos
            for period in ["requests_per_minute", "requests_per_hour", "requests_per_day"]:
                cache_key = f"rate_limit:{identifier}:{period}"
                if endpoint:
                    cache_key += f":{hashlib.md5(endpoint.encode()).hexdigest()[:8]}"
                
                self._add_request_to_history(cache_key, now)
            
            # Registrar para burst protection
            burst_key = f"rate_limit:{identifier}:burst"
            self._add_request_to_history(burst_key, now)
            
        except Exception as e:
            frappe.log_error(f"Erro ao incrementar contadores: {str(e)}")
    
    def _get_request_history(self, cache_key: str, start_time: datetime, 
                           end_time: datetime) -> list:
        """Obtém histórico de requisições para uma janela de tempo"""
        try:
            # Tentar obter do cache Redis primeiro
            if frappe.cache and hasattr(frappe.cache, 'hget'):
                cached_data = frappe.cache.hget("rate_limit_history", cache_key)
                if cached_data:
                    history = json.loads(cached_data)
                    # Filtrar apenas requisições na janela atual
                    return [
                        datetime.fromisoformat(req_time) 
                        for req_time in history 
                        if start_time <= datetime.fromisoformat(req_time) <= end_time
                    ]
            
            # Fallback para banco de dados
            return self._get_request_history_from_db(cache_key, start_time, end_time)
            
        except Exception as e:
            frappe.log_error(f"Erro ao obter histórico: {str(e)}")
            return []
    
    def _add_request_to_history(self, cache_key: str, request_time: datetime):
        """Adiciona requisição ao histórico"""
        try:
            # Tentar adicionar ao cache Redis
            if frappe.cache and hasattr(frappe.cache, 'hget'):
                cached_data = frappe.cache.hget("rate_limit_history", cache_key)
                history = json.loads(cached_data) if cached_data else []
                
                # Adicionar nova requisição
                history.append(request_time.isoformat())
                
                # Manter apenas últimas 1000 requisições
                if len(history) > 1000:
                    history = history[-1000:]
                
                # Salvar de volta no cache (expirar em 1 dia)
                frappe.cache.hset("rate_limit_history", cache_key, json.dumps(history))
                frappe.cache.expire("rate_limit_history", 86400)
            
            # Também salvar no banco como backup
            self._save_request_to_db(cache_key, request_time)
            
        except Exception as e:
            frappe.log_error(f"Erro ao adicionar ao histórico: {str(e)}")
    
    def _get_request_history_from_db(self, cache_key: str, start_time: datetime, 
                                   end_time: datetime) -> list:
        """Obtém histórico do banco de dados"""
        try:
            records = frappe.get_all(
                "API Rate Limit Log",
                filters={
                    "cache_key": cache_key,
                    "request_time": ["between", [start_time, end_time]]
                },
                fields=["request_time"],
                order_by="request_time desc",
                limit=1000
            )
            
            return [get_datetime(record.request_time) for record in records]
            
        except Exception:
            return []
    
    def _save_request_to_db(self, cache_key: str, request_time: datetime):
        """Salva requisição no banco de dados"""
        try:
            frappe.get_doc({
                "doctype": "API Rate Limit Log",
                "cache_key": cache_key,
                "request_time": request_time,
                "created_at": now_datetime()
            }).insert(ignore_permissions=True, ignore_if_duplicate=True)
            
        except Exception as e:
            # Não fazer log de erro aqui para evitar loops
            pass
    
    def _get_window_size(self, period: str) -> timedelta:
        """Retorna o tamanho da janela para um período"""
        if period == "requests_per_minute":
            return timedelta(minutes=1)
        elif period == "requests_per_hour":
            return timedelta(hours=1)
        elif period == "requests_per_day":
            return timedelta(days=1)
        else:
            return timedelta(minutes=1)
    
    def _get_remaining_limits(self, identifier: str, limits: Dict) -> Dict:
        """Obtém informações sobre limites restantes"""
        try:
            remaining = {}
            now = now_datetime()
            
            for period, limit in limits.items():
                if period == "burst_limit":
                    continue
                    
                window_size = self._get_window_size(period)
                window_start = now - window_size
                
                cache_key = f"rate_limit:{identifier}:{period}"
                requests = self._get_request_history(cache_key, window_start, now)
                
                remaining[period] = max(0, limit - len(requests))
            
            return remaining
            
        except Exception:
            return {}
    
    def _calculate_retry_after(self, reset_time: Optional[datetime]) -> int:
        """Calcula tempo em segundos até o próximo reset"""
        if not reset_time:
            return 60
        
        now = now_datetime()
        if reset_time > now:
            return int((reset_time - now).total_seconds())
        
        return 60
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Remove logs antigos do banco de dados"""
        try:
            cutoff_date = now_datetime() - timedelta(days=days_to_keep)
            
            frappe.db.delete("API Rate Limit Log", {
                "created_at": ["<", cutoff_date]
            })
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Erro na limpeza de logs de rate limit: {str(e)}")


# Instância global do rate limiter
rate_limiter = RateLimiter()