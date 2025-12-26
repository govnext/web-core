# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
import redis
import pickle
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import time

class GovNextCacheSystem:
    """
    Sistema de Cache Avançado para GovNext
    Implementa cache inteligente com Redis e invalidação automática
    """
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.default_ttl = 3600  # 1 hora
        self.cache_prefix = f"govnext:{frappe.local.site}:"
        
    def _get_redis_client(self):
        """Configurar cliente Redis"""
        try:
            redis_config = frappe.conf.get('redis_cache', {})
            
            client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 1),
                password=redis_config.get('password'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Testar conexão
            client.ping()
            return client
            
        except Exception as e:
            frappe.log_error(f"Redis connection failed: {str(e)}", "Cache System")
            # Fallback para cache do Frappe
            return None
    
    def _generate_cache_key(self, key, user=None, government_level=None):
        """Gerar chave de cache única"""
        components = [self.cache_prefix, key]
        
        if user:
            components.append(f"user:{user}")
        
        if government_level:
            components.append(f"gov:{government_level}")
        
        return ":".join(components)
    
    def set(self, key, value, ttl=None, user_specific=False, government_level=None):
        """
        Armazenar valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Tempo de vida em segundos
            user_specific: Se o cache é específico por usuário
            government_level: Nível governamental (federal, estadual, municipal)
        """
        try:
            cache_key = self._generate_cache_key(
                key, 
                frappe.session.user if user_specific else None,
                government_level
            )
            
            ttl = ttl or self.default_ttl
            
            # Serializar dados
            cached_data = {
                "value": value,
                "cached_at": datetime.utcnow().isoformat(),
                "ttl": ttl,
                "user": frappe.session.user if user_specific else None,
                "government_level": government_level
            }
            
            if self.redis_client:
                # Cache no Redis
                self.redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(cached_data, default=str)
                )
            else:
                # Fallback para cache do Frappe
                frappe.cache().set(cache_key, cached_data, expires_in_sec=ttl)
            
            # Registrar para invalidação
            self._register_for_invalidation(key, cache_key, government_level)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Cache set error: {str(e)}", "Cache System")
            return False
    
    def get(self, key, user_specific=False, government_level=None):
        """
        Recuperar valor do cache
        
        Args:
            key: Chave do cache
            user_specific: Se o cache é específico por usuário
            government_level: Nível governamental
        """
        try:
            cache_key = self._generate_cache_key(
                key,
                frappe.session.user if user_specific else None,
                government_level
            )
            
            if self.redis_client:
                # Buscar no Redis
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    return data["value"]
            else:
                # Fallback para cache do Frappe
                cached_data = frappe.cache().get(cache_key)
                if cached_data:
                    return cached_data["value"]
            
            return None
            
        except Exception as e:
            frappe.log_error(f"Cache get error: {str(e)}", "Cache System")
            return None
    
    def delete(self, key, user_specific=False, government_level=None):
        """Remover item do cache"""
        try:
            cache_key = self._generate_cache_key(
                key,
                frappe.session.user if user_specific else None,
                government_level
            )
            
            if self.redis_client:
                self.redis_client.delete(cache_key)
            else:
                frappe.cache().delete(cache_key)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Cache delete error: {str(e)}", "Cache System")
            return False
    
    def invalidate_pattern(self, pattern):
        """Invalidar cache por padrão"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(f"{self.cache_prefix}{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Para cache do Frappe, limpar tudo relacionado
                frappe.cache().delete_keys(pattern)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Cache invalidate error: {str(e)}", "Cache System")
            return False
    
    def _register_for_invalidation(self, key, cache_key, government_level):
        """Registrar chave para invalidação automática"""
        try:
            # Mapear tipos de dados para invalidação
            invalidation_map = {
                "budget": ["public_budget", "financial_report"],
                "tender": ["public_tender", "procurement"],
                "user": ["user_permissions", "user_profile"],
                "government_unit": ["org_structure", "hierarchy"]
            }
            
            for data_type, related_keys in invalidation_map.items():
                if data_type in key.lower():
                    for related_key in related_keys:
                        self._add_to_invalidation_group(related_key, cache_key, government_level)
            
        except Exception as e:
            frappe.log_error(f"Cache registration error: {str(e)}", "Cache System")
    
    def _add_to_invalidation_group(self, group, cache_key, government_level):
        """Adicionar chave ao grupo de invalidação"""
        try:
            group_key = f"{self.cache_prefix}invalidation:{group}"
            if government_level:
                group_key += f":{government_level}"
            
            if self.redis_client:
                self.redis_client.sadd(group_key, cache_key)
                self.redis_client.expire(group_key, 86400)  # 24 horas
            
        except Exception as e:
            frappe.log_error(f"Cache group error: {str(e)}", "Cache System")
    
    def invalidate_group(self, group, government_level=None):
        """Invalidar grupo de cache"""
        try:
            group_key = f"{self.cache_prefix}invalidation:{group}"
            if government_level:
                group_key += f":{government_level}"
            
            if self.redis_client:
                cache_keys = self.redis_client.smembers(group_key)
                if cache_keys:
                    self.redis_client.delete(*cache_keys)
                self.redis_client.delete(group_key)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Cache group invalidation error: {str(e)}", "Cache System")
            return False
    
    def get_cache_stats(self):
        """Obter estatísticas do cache"""
        try:
            stats = {
                "redis_available": self.redis_client is not None,
                "total_keys": 0,
                "memory_usage": 0,
                "hit_rate": 0
            }
            
            if self.redis_client:
                info = self.redis_client.info()
                pattern_keys = self.redis_client.keys(f"{self.cache_prefix}*")
                
                stats.update({
                    "total_keys": len(pattern_keys),
                    "memory_usage": info.get("used_memory_human", "0B"),
                    "hit_rate": self._calculate_hit_rate(),
                    "redis_version": info.get("redis_version", "unknown"),
                    "connected_clients": info.get("connected_clients", 0)
                })
            
            return stats
            
        except Exception as e:
            frappe.log_error(f"Cache stats error: {str(e)}", "Cache System")
            return {"error": str(e)}
    
    def _calculate_hit_rate(self):
        """Calcular taxa de acerto do cache"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                
                if hits + misses > 0:
                    return round((hits / (hits + misses)) * 100, 2)
            
            return 0
            
        except Exception:
            return 0
    
    def warm_up_cache(self, government_level=None):
        """Pré-carregar cache com dados frequentemente acessados"""
        try:
            # Dados de unidades governamentais
            self._cache_government_units(government_level)
            
            # Configurações do sistema
            self._cache_system_settings()
            
            # Dados de transparência
            self._cache_transparency_data(government_level)
            
            return True
            
        except Exception as e:
            frappe.log_error(f"Cache warm-up error: {str(e)}", "Cache System")
            return False
    
    def _cache_government_units(self, government_level):
        """Cache de unidades governamentais"""
        filters = {"is_active": 1}
        if government_level:
            filters["unit_type"] = government_level
        
        units = frappe.get_all(
            "Government Unit",
            filters=filters,
            fields=["name", "unit_name", "unit_type", "parent_unit"]
        )
        
        self.set(
            "government_units",
            units,
            ttl=7200,  # 2 horas
            government_level=government_level
        )
    
    def _cache_system_settings(self):
        """Cache de configurações do sistema"""
        settings = frappe.get_single("System Settings")
        self.set("system_settings", settings.as_dict(), ttl=3600)
    
    def _cache_transparency_data(self, government_level):
        """Cache de dados de transparência"""
        # Últimos orçamentos
        budgets = frappe.get_all(
            "Public Budget",
            filters={"status": "Active"},
            fields=["name", "government_unit", "fiscal_year", "total_revenue", "total_expenses"],
            limit=50
        )
        
        self.set(
            "recent_budgets",
            budgets,
            ttl=1800,  # 30 minutos
            government_level=government_level
        )
        
        # Licitações ativas
        tenders = frappe.get_all(
            "Public Tender",
            filters={"status": "Open"},
            fields=["name", "tender_title", "government_unit", "end_date", "total_value"],
            limit=50
        )
        
        self.set(
            "active_tenders",
            tenders,
            ttl=900,  # 15 minutos
            government_level=government_level
        )

# Instância global do sistema de cache
cache_system = GovNextCacheSystem()

# Decorador para cache automático
def cached(ttl=None, user_specific=False, government_level=None, key_func=None):
    """
    Decorator para cache automático de funções
    
    Args:
        ttl: Tempo de vida do cache
        user_specific: Cache específico por usuário
        government_level: Nível governamental
        key_func: Função para gerar chave customizada
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave do cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Tentar buscar no cache
            cached_result = cache_system.get(
                cache_key,
                user_specific=user_specific,
                government_level=government_level
            )
            
            if cached_result is not None:
                return cached_result
            
            # Executar função e armazenar resultado
            result = func(*args, **kwargs)
            
            cache_system.set(
                cache_key,
                result,
                ttl=ttl,
                user_specific=user_specific,
                government_level=government_level
            )
            
            return result
            
        return wrapper
    return decorator

# Decorador para invalidação automática
def invalidates_cache(*groups):
    """Decorator para invalidar cache após execução"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidar grupos especificados
            for group in groups:
                cache_system.invalidate_group(group)
            
            return result
            
        return wrapper
    return decorator

# Funções de cache específicas para o sistema
@frappe.whitelist()
@cached(ttl=3600, government_level="municipal")
def get_cached_government_units(unit_type=None):
    """Buscar unidades governamentais com cache"""
    filters = {"is_active": 1}
    if unit_type:
        filters["unit_type"] = unit_type
    
    return frappe.get_all(
        "Government Unit",
        filters=filters,
        fields=["name", "unit_name", "unit_type", "parent_unit", "is_active"]
    )

@frappe.whitelist()
@cached(ttl=1800, user_specific=True)
def get_user_dashboard_data():
    """Dados do dashboard do usuário com cache"""
    user = frappe.session.user
    
    # Dados específicos do usuário
    user_data = {
        "notifications": frappe.get_all(
            "Notification Log",
            filters={"for_user": user, "read": 0},
            limit=10
        ),
        "recent_documents": frappe.get_all(
            "Version",
            filters={"owner": user},
            fields=["ref_doctype", "docname", "creation"],
            order_by="creation desc",
            limit=20
        ),
        "permissions": frappe.get_roles(user)
    }
    
    return user_data

@frappe.whitelist()
@cached(ttl=900, government_level="all")
def get_transparency_summary():
    """Resumo de transparência com cache"""
    return {
        "total_budgets": frappe.db.count("Public Budget", {"status": "Active"}),
        "active_tenders": frappe.db.count("Public Tender", {"status": "Open"}),
        "total_contracts": frappe.db.count("Public Contract", {"status": "Active"}),
        "transparency_requests": frappe.db.count("Transparency Request", {"status": "Open"})
    }

# Funções de invalidação específicas
def invalidate_government_cache():
    """Invalidar cache relacionado a governo"""
    cache_system.invalidate_group("government_unit")
    cache_system.invalidate_group("org_structure")

def invalidate_budget_cache():
    """Invalidar cache relacionado a orçamento"""
    cache_system.invalidate_group("public_budget")
    cache_system.invalidate_group("financial_report")

def invalidate_tender_cache():
    """Invalidar cache relacionado a licitações"""
    cache_system.invalidate_group("public_tender")
    cache_system.invalidate_group("procurement")

def invalidate_user_cache(user=None):
    """Invalidar cache específico do usuário"""
    if user:
        cache_system.invalidate_pattern(f"user:{user}")
    else:
        cache_system.invalidate_group("user_permissions")

# APIs para gestão de cache
@frappe.whitelist()
def get_cache_statistics():
    """API para obter estatísticas do cache"""
    if not frappe.has_permission("System Settings", "read"):
        frappe.throw(_("Permissão insuficiente"))
    
    return cache_system.get_cache_stats()

@frappe.whitelist()
def warm_up_system_cache():
    """API para pré-carregar cache"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Permissão insuficiente"))
    
    government_level = frappe.local.form_dict.get("government_level")
    result = cache_system.warm_up_cache(government_level)
    
    return {"success": result, "message": _("Cache pré-carregado com sucesso") if result else _("Erro ao pré-carregar cache")}

@frappe.whitelist()
def clear_system_cache():
    """API para limpar cache"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Permissão insuficiente"))
    
    pattern = frappe.local.form_dict.get("pattern", "*")
    result = cache_system.invalidate_pattern(pattern)
    
    return {"success": result, "message": _("Cache limpo com sucesso") if result else _("Erro ao limpar cache")}