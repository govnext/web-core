# -*- coding: utf-8 -*-
"""
Sistema de Cache Governamental
Gerenciamento inteligente de cache para otimização de performance
"""

import frappe
from frappe import _
import json
import hashlib
from datetime import datetime, timedelta
import redis
from functools import wraps

class GovCacheManager:
    """Gerenciador de Cache para aplicações governamentais"""
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 hora
        self.init_redis()
    
    def init_redis(self):
        """Inicializar conexão Redis"""
        try:
            redis_config = frappe.conf.get('redis_cache', {})
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 1),
                decode_responses=True
            )
            # Testar conexão
            self.redis_client.ping()
        except:
            # Fallback para cache nativo do Frappe
            self.redis_client = None
    
    def get_cache_key(self, category, identifier, params=None):
        """Gerar chave de cache padronizada"""
        key_parts = [f"govnext_{category}", str(identifier)]
        
        if params:
            # Ordenar parâmetros para consistência
            param_str = json.dumps(params, sort_keys=True, default=str)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        
        return ":".join(key_parts)
    
    def get(self, category, identifier, params=None):
        """Obter valor do cache"""
        key = self.get_cache_key(category, identifier, params)
        
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            else:
                return frappe.cache().get(key)
        except:
            return None
    
    def set(self, category, identifier, value, ttl=None, params=None):
        """Definir valor no cache"""
        key = self.get_cache_key(category, identifier, params)
        ttl = ttl or self.default_ttl
        
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            else:
                frappe.cache().set(key, value, expires_in_sec=ttl)
            
            # Log de cache para debugging
            self._log_cache_operation("SET", key, ttl)
            
        except Exception as e:
            frappe.log_error(f"Erro ao definir cache: {str(e)}", "Cache Error")
    
    def delete(self, category, identifier=None, params=None):
        """Deletar valor específico ou categoria inteira"""
        if identifier:
            key = self.get_cache_key(category, identifier, params)
            try:
                if self.redis_client:
                    self.redis_client.delete(key)
                else:
                    frappe.cache().delete(key)
                
                self._log_cache_operation("DELETE", key)
            except:
                pass
        else:
            # Deletar toda a categoria
            self.invalidate_category(category)
    
    def invalidate_category(self, category):
        """Invalidar toda uma categoria de cache"""
        pattern = f"govnext_{category}*"
        
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            else:
                # Para cache nativo, não há pattern matching eficiente
                # Usar flag de invalidação
                frappe.cache().set(f"invalid_{category}", True, expires_in_sec=3600)
            
            self._log_cache_operation("INVALIDATE", pattern)
            
        except Exception as e:
            frappe.log_error(f"Erro ao invalidar categoria: {str(e)}", "Cache Error")
    
    def is_category_invalid(self, category):
        """Verificar se categoria foi invalidada"""
        if self.redis_client:
            return False  # Redis gerencia automaticamente
        
        return frappe.cache().get(f"invalid_{category}") is True
    
    def get_stats(self):
        """Obter estatísticas do cache"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                keys_count = self.redis_client.dbsize()
                
                return {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_keys": keys_count,
                    "hit_rate": self._calculate_hit_rate(info)
                }
            else:
                return {
                    "backend": "frappe_cache",
                    "status": "active"
                }
        except:
            return {"status": "error"}
    
    def _calculate_hit_rate(self, info):
        """Calcular taxa de acerto do cache"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0
        
        return round((hits / total) * 100, 2)
    
    def _log_cache_operation(self, operation, key, ttl=None):
        """Log de operações de cache para debugging"""
        if frappe.conf.get('cache_debug'):
            frappe.log_error(
                f"Cache {operation}: {key}" + (f" (TTL: {ttl}s)" if ttl else ""),
                "Cache Debug"
            )
    
    def warm_up(self, categories=None):
        """Pré-carregar cache com dados frequentemente acessados"""
        categories = categories or [
            'transparency_data', 'budget_data', 'tender_data', 
            'municipal_data', 'financial_data'
        ]
        
        for category in categories:
            try:
                if category == 'transparency_data':
                    self._warm_up_transparency_data()
                elif category == 'budget_data':
                    self._warm_up_budget_data()
                elif category == 'tender_data':
                    self._warm_up_tender_data()
                elif category == 'municipal_data':
                    self._warm_up_municipal_data()
                elif category == 'financial_data':
                    self._warm_up_financial_data()
            except Exception as e:
                frappe.log_error(f"Erro ao pré-carregar {category}: {str(e)}", "Cache Warmup Error")
    
    def _warm_up_transparency_data(self):
        """Pré-carregar dados de transparência"""
        # Dados gerais do portal
        self.set('transparency_data', 'portal_stats', self._get_portal_stats(), ttl=1800)
        
        # Resumos mensais
        for i in range(12):
            month_data = self._get_monthly_summary(i)
            self.set('transparency_data', f'monthly_summary_{i}', month_data, ttl=3600)
    
    def _warm_up_budget_data(self):
        """Pré-carregar dados orçamentários"""
        current_year = datetime.now().year
        budget_summary = self._get_budget_summary(current_year)
        self.set('budget_data', f'summary_{current_year}', budget_summary, ttl=3600)
    
    def _warm_up_tender_data(self):
        """Pré-carregar dados de licitações"""
        active_tenders = self._get_active_tenders()
        self.set('tender_data', 'active_list', active_tenders, ttl=1800)
    
    def _warm_up_municipal_data(self):
        """Pré-carregar dados municipais"""
        municipal_stats = self._get_municipal_stats()
        self.set('municipal_data', 'stats', municipal_stats, ttl=3600)
    
    def _warm_up_financial_data(self):
        """Pré-carregar dados financeiros"""
        financial_summary = self._get_financial_summary()
        self.set('financial_data', 'summary', financial_summary, ttl=1800)
    
    # Métodos auxiliares para warm-up
    def _get_portal_stats(self):
        """Obter estatísticas do portal"""
        return {
            "total_visitors": frappe.db.count("Web Page View"),
            "transparency_requests": frappe.db.count("Request Log"),
            "last_updated": frappe.utils.now()
        }
    
    def _get_monthly_summary(self, months_ago):
        """Obter resumo mensal"""
        target_date = frappe.utils.add_months(frappe.utils.nowdate(), -months_ago)
        return {
            "month": target_date,
            "budget_execution": 85.5,  # Placeholder
            "tender_count": 15,  # Placeholder
        }
    
    def _get_budget_summary(self, year):
        """Obter resumo orçamentário"""
        return {
            "year": year,
            "total_budget": 10000000,  # Placeholder
            "executed": 8500000,  # Placeholder
            "percentage": 85.0
        }
    
    def _get_active_tenders(self):
        """Obter licitações ativas"""
        return frappe.get_all(
            "Public Tender",
            filters={"status": "Active"},
            fields=["name", "tender_title", "opening_date"],
            limit=20
        )
    
    def _get_municipal_stats(self):
        """Obter estatísticas municipais"""
        return {
            "iptu_collected": 5000000,  # Placeholder
            "iss_collected": 3000000,   # Placeholder
            "licenses_issued": 450      # Placeholder
        }
    
    def _get_financial_summary(self):
        """Obter resumo financeiro"""
        return {
            "total_revenue": 50000000,  # Placeholder
            "total_expenses": 45000000, # Placeholder
            "balance": 5000000         # Placeholder
        }

# Instância global do gerenciador de cache
cache_manager = GovCacheManager()

def cached_function(category, ttl=None, key_func=None):
    """Decorator para cache automático de funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave baseada na função e parâmetros
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Verificar se categoria foi invalidada
            if cache_manager.is_category_invalid(category):
                cache_manager.delete(category, cache_key)
            
            # Tentar obter do cache
            cached_result = cache_manager.get(category, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(category, cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_cache_on_update(doc, method):
    """Hook para invalidar cache quando documentos são atualizados"""
    cache_invalidation_map = {
        "Public Budget": ["budget_data", "financial_data", "transparency_data"],
        "Public Tender": ["tender_data", "transparency_data"],
        "Municipal Tax": ["municipal_data", "financial_data"],
        "Government Unit": ["transparency_data"],
        "Payment Entry": ["financial_data", "transparency_data"]
    }
    
    categories = cache_invalidation_map.get(doc.doctype, [])
    for category in categories:
        cache_manager.invalidate_category(category)

# APIs para gerenciamento de cache
@frappe.whitelist()
def get_cache_stats():
    """Obter estatísticas do cache"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Sem permissão para acessar estatísticas de cache"))
    
    return cache_manager.get_stats()

@frappe.whitelist() 
def invalidate_cache(category=None):
    """Invalidar cache por categoria"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Sem permissão para invalidar cache"))
    
    if category:
        cache_manager.invalidate_category(category)
        return {"message": f"Cache da categoria '{category}' invalidado"}
    else:
        # Invalidar todas as categorias principais
        categories = [
            'transparency_data', 'budget_data', 'tender_data',
            'municipal_data', 'financial_data'
        ]
        for cat in categories:
            cache_manager.invalidate_category(cat)
        return {"message": "Todo o cache foi invalidado"}

@frappe.whitelist()
def warm_up_cache(categories=None):
    """Pré-carregar cache"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Sem permissão para pré-carregar cache"))
    
    if categories:
        categories = json.loads(categories) if isinstance(categories, str) else categories
    
    cache_manager.warm_up(categories)
    return {"message": "Cache pré-carregado com sucesso"}

# Cache específico para consultas governamentais
@cached_function('transparency_data', ttl=1800)
def get_transparency_summary():
    """Cache para resumo de transparência"""
    return {
        "total_revenue": frappe.db.sql("SELECT SUM(amount) FROM `tabRevenue Entry`")[0][0] or 0,
        "total_expenses": frappe.db.sql("SELECT SUM(amount) FROM `tabExpense Entry`")[0][0] or 0,
        "active_tenders": frappe.db.count("Public Tender", {"status": "Active"}),
        "last_updated": frappe.utils.now()
    }

@cached_function('budget_data', ttl=3600)
def get_budget_execution(year=None):
    """Cache para execução orçamentária"""
    year = year or datetime.now().year
    
    budget_data = frappe.db.sql("""
        SELECT 
            SUM(allocated_amount) as allocated,
            SUM(executed_amount) as executed
        FROM `tabBudget Line`
        WHERE YEAR(creation) = %s
    """, [year], as_dict=True)
    
    if budget_data:
        allocated = budget_data[0].get('allocated', 0)
        executed = budget_data[0].get('executed', 0)
        
        return {
            "year": year,
            "allocated": allocated,
            "executed": executed,
            "execution_percentage": round((executed / allocated * 100), 2) if allocated > 0 else 0
        }
    
    return {"year": year, "allocated": 0, "executed": 0, "execution_percentage": 0}

@cached_function('municipal_data', ttl=7200)
def get_municipal_revenue_summary():
    """Cache para resumo de receitas municipais"""
    return {
        "iptu_current_year": frappe.db.sql("""
            SELECT SUM(amount) FROM `tabIPTU Payment`
            WHERE YEAR(payment_date) = YEAR(CURDATE())
        """)[0][0] or 0,
        "iss_current_year": frappe.db.sql("""
            SELECT SUM(amount) FROM `tabISS Payment`
            WHERE YEAR(payment_date) = YEAR(CURDATE())
        """)[0][0] or 0,
        "licenses_issued": frappe.db.count("Municipal License", {
            "issue_date": [">=", frappe.utils.get_first_day()]
        })
    }