# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from .utils.cache import cache_system, invalidate_government_cache, invalidate_budget_cache, invalidate_tender_cache, invalidate_user_cache
from .utils.audit import audit_system
from .utils.validation import GovNextValidator, validate_document_data

def before_request():
    """
    Hook executado antes de cada request
    """
    try:
        # Configurar contexto de segurança
        frappe.local.security_context = {
            "request_id": frappe.generate_hash(length=16),
            "start_time": frappe.utils.now(),
            "ip_address": frappe.local.request_ip,
            "user_agent": frappe.local.request.headers.get('User-Agent', '')
        }
        
        # Verificar rate limiting para usuários anônimos
        if frappe.session.user == "Guest":
            check_anonymous_rate_limit()
        
        # Log de request para APIs críticas
        if frappe.local.request.path.startswith('/api/'):
            log_api_request()
            
    except Exception as e:
        frappe.log_error(f"Before request error: {str(e)}", "Hooks Error")

def after_request():
    """
    Hook executado após cada request
    """
    try:
        # Log de performance
        if hasattr(frappe.local, 'security_context'):
            start_time = frappe.local.security_context.get('start_time')
            if start_time:
                duration = frappe.utils.time_diff_in_seconds(frappe.utils.now(), start_time)
                
                # Log requests lentos
                if duration > 5:  # 5 segundos
                    frappe.log_error(
                        f"Slow request: {frappe.local.request.path} took {duration}s",
                        "Performance Warning"
                    )
        
        # Cleanup de cache temporário
        cleanup_temp_cache()
        
    except Exception as e:
        frappe.log_error(f"After request error: {str(e)}", "Hooks Error")

def check_anonymous_rate_limit():
    """Verificar rate limiting para usuários anônimos"""
    try:
        ip = frappe.local.request_ip
        key = f"anon_rate_limit:{ip}"
        
        current_requests = cache_system.get(key) or 0
        
        if current_requests >= 100:  # 100 requests por hora
            frappe.throw(_("Muitas requisições. Tente novamente em uma hora."))
        
        cache_system.set(key, current_requests + 1, ttl=3600)
        
    except Exception as e:
        frappe.log_error(f"Rate limit check error: {str(e)}", "Security Error")

def log_api_request():
    """Log de requisições da API"""
    try:
        if frappe.local.request.path.startswith('/api/method/govnext_core'):
            audit_system.log_event(
                event_type="API_REQUEST",
                user=frappe.session.user,
                details={
                    "path": frappe.local.request.path,
                    "method": frappe.local.request.method,
                    "user_agent": frappe.local.request.headers.get('User-Agent', ''),
                    "request_id": frappe.local.security_context.get('request_id')
                }
            )
    except Exception as e:
        frappe.log_error(f"API request log error: {str(e)}", "Audit Error")

def cleanup_temp_cache():
    """Limpar cache temporário"""
    try:
        # Limpar cache de sessão expirado
        cache_system.invalidate_pattern("temp_*")
        
    except Exception as e:
        frappe.log_error(f"Cache cleanup error: {str(e)}", "Cache Error")

def before_job(job):
    """Hook executado antes de jobs em background"""
    try:
        audit_system.log_event(
            event_type="JOB_START",
            user="Administrator",
            details={
                "job_name": job.get('job_name'),
                "queue": job.get('queue'),
                "timeout": job.get('timeout')
            }
        )
    except Exception as e:
        frappe.log_error(f"Before job error: {str(e)}", "Job Error")

def after_job(job):
    """Hook executado após jobs em background"""
    try:
        audit_system.log_event(
            event_type="JOB_COMPLETE",
            user="Administrator",
            details={
                "job_name": job.get('job_name'),
                "status": job.get('status'),
                "duration": job.get('duration')
            }
        )
    except Exception as e:
        frappe.log_error(f"After job error: {str(e)}", "Job Error")

# ==================== DOCUMENT EVENTS ====================

def invalidate_cache_on_update(doc, method):
    """Invalidar cache quando documentos são atualizados"""
    try:
        doctype = doc.doctype
        
        # Mapeamento de doctypes para grupos de cache
        cache_mapping = {
            "User": ["user_permissions", "user_profile"],
            "Government Unit": ["government_unit", "org_structure"],
            "Public Budget": ["public_budget", "financial_report"],
            "Public Tender": ["public_tender", "procurement"],
            "Company": ["company_info", "system_settings"],
            "System Settings": ["system_settings"]
        }
        
        if doctype in cache_mapping:
            for cache_group in cache_mapping[doctype]:
                cache_system.invalidate_group(cache_group)
        
        # Cache específico do documento
        cache_system.delete(f"{doctype}:{doc.name}")
        
    except Exception as e:
        frappe.log_error(f"Cache invalidation error: {str(e)}", "Cache Error")

def setup_user_permissions(doc, method):
    """Configurar permissões para novo usuário"""
    try:
        # Configurar permissões baseadas no tipo de usuário governamental
        if hasattr(doc, 'government_level'):
            setup_government_permissions(doc)
        
        # Configurar cache de usuário
        cache_key = f"user_setup:{doc.name}"
        cache_system.set(cache_key, {
            "user": doc.name,
            "setup_completed": True,
            "government_level": getattr(doc, 'government_level', None)
        }, ttl=86400)
        
        # Audit do setup
        audit_system.log_event(
            event_type="USER_SETUP",
            user=frappe.session.user,
            details={
                "new_user": doc.name,
                "government_level": getattr(doc, 'government_level', None)
            }
        )
        
    except Exception as e:
        frappe.log_error(f"User setup error: {str(e)}", "User Setup Error")

def setup_government_permissions(user_doc):
    """Configurar permissões governamentais específicas"""
    try:
        government_level = getattr(user_doc, 'government_level', None)
        
        if not government_level:
            return
        
        # Mapeamento de níveis para roles
        role_mapping = {
            'federal': ['Federal User', 'Government User'],
            'estadual': ['State User', 'Government User'],
            'municipal': ['Municipal User', 'Government User']
        }
        
        if government_level in role_mapping:
            for role in role_mapping[government_level]:
                if not frappe.db.exists("Has Role", {"parent": user_doc.name, "role": role}):
                    user_doc.append("roles", {"role": role})
        
        user_doc.save(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Government permissions setup error: {str(e)}", "Permission Error")

def update_user_cache(doc, method):
    """Atualizar cache quando usuário é modificado"""
    try:
        # Invalidar cache específico do usuário
        invalidate_user_cache(doc.name)
        
        # Se mudou nível governamental, reconfigurar permissões
        if doc.has_value_changed('government_level'):
            setup_government_permissions(doc)
            
            audit_system.log_event(
                event_type="USER_GOVERNMENT_LEVEL_CHANGE",
                user=frappe.session.user,
                details={
                    "target_user": doc.name,
                    "old_level": doc.get_db_value('government_level'),
                    "new_level": doc.government_level
                }
            )
        
    except Exception as e:
        frappe.log_error(f"User cache update error: {str(e)}", "Cache Error")

def validate_user_government_data(doc, method):
    """Validar dados governamentais do usuário"""
    try:
        # Validar CPF se fornecido
        if doc.get('cpf'):
            if not GovNextValidator.validate_cpf(doc.cpf):
                frappe.throw(_("CPF inválido"))
        
        # Validar PIS/PASEP se fornecido
        if doc.get('pis_pasep'):
            if not GovNextValidator.validate_pis_pasep(doc.pis_pasep):
                frappe.throw(_("PIS/PASEP inválido"))
        
        # Validar título de eleitor se fornecido
        if doc.get('titulo_eleitor'):
            if not GovNextValidator.validate_titulo_eleitor(doc.titulo_eleitor):
                frappe.throw(_("Título de eleitor inválido"))
        
        # Verificar se nível governamental é válido
        if doc.get('government_level'):
            if not GovNextValidator.validate_government_level(doc.government_level):
                frappe.throw(_("Nível governamental inválido"))
        
    except Exception as e:
        frappe.log_error(f"User validation error: {str(e)}", "Validation Error")
        raise

def invalidate_government_cache_hook(doc, method):
    """Hook para invalidar cache de unidades governamentais"""
    try:
        invalidate_government_cache()
        
        # Invalidar cache relacionado
        cache_system.invalidate_group("org_structure")
        cache_system.invalidate_group("hierarchy")
        
    except Exception as e:
        frappe.log_error(f"Government cache invalidation error: {str(e)}", "Cache Error")

def validate_government_unit(doc, method):
    """Validar unidade governamental"""
    try:
        # Validar tipo de unidade
        if not GovNextValidator.validate_government_level(doc.unit_type):
            frappe.throw(_("Tipo de unidade governamental inválido"))
        
        # Validar CNPJ se fornecido
        if doc.get('cnpj'):
            if not GovNextValidator.validate_cnpj(doc.cnpj):
                frappe.throw(_("CNPJ inválido"))
        
        # Validar hierarquia
        if doc.parent_unit:
            if doc.parent_unit == doc.name:
                frappe.throw(_("Unidade não pode ser pai de si mesma"))
            
            # Verificar ciclos na hierarquia
            if check_hierarchy_cycle(doc.name, doc.parent_unit):
                frappe.throw(_("Hierarquia circular detectada"))
        
        # Validar email de contato
        if doc.get('contact_email'):
            if not GovNextValidator.validate_email(doc.contact_email):
                frappe.throw(_("Email de contato inválido"))
        
        # Validar telefone de contato
        if doc.get('contact_phone'):
            if not GovNextValidator.validate_phone(doc.contact_phone):
                frappe.throw(_("Telefone de contato inválido"))
        
    except Exception as e:
        frappe.log_error(f"Government unit validation error: {str(e)}", "Validation Error")
        raise

def check_hierarchy_cycle(unit_name, parent_unit, visited=None):
    """Verificar se há ciclo na hierarquia de unidades"""
    if visited is None:
        visited = set()
    
    if parent_unit in visited:
        return True
    
    visited.add(parent_unit)
    
    parent_of_parent = frappe.db.get_value("Government Unit", parent_unit, "parent_unit")
    if parent_of_parent:
        return check_hierarchy_cycle(unit_name, parent_of_parent, visited)
    
    return False

def invalidate_budget_cache_hook(doc, method):
    """Hook para invalidar cache de orçamentos"""
    try:
        invalidate_budget_cache()
        
        # Invalidar cache relacionado
        cache_system.invalidate_group("financial_report")
        cache_system.invalidate_group("transparency_data")
        
    except Exception as e:
        frappe.log_error(f"Budget cache invalidation error: {str(e)}", "Cache Error")

def validate_public_budget(doc, method):
    """Validar orçamento público"""
    try:
        # Validar valores monetários
        if doc.get('total_revenue'):
            if not GovNextValidator.validate_currency(doc.total_revenue):
                frappe.throw(_("Valor de receita inválido"))
        
        if doc.get('total_expenses'):
            if not GovNextValidator.validate_currency(doc.total_expenses):
                frappe.throw(_("Valor de despesa inválido"))
        
        # Validar ano fiscal
        if doc.get('fiscal_year'):
            try:
                year = int(doc.fiscal_year)
                if year < 2000 or year > 2100:
                    frappe.throw(_("Ano fiscal inválido"))
            except ValueError:
                frappe.throw(_("Ano fiscal deve ser um número"))
        
        # Validar categoria orçamentária
        if doc.get('budget_category'):
            if not GovNextValidator.validate_budget_category(doc.budget_category):
                frappe.throw(_("Categoria orçamentária inválida"))
        
        # Verificar se unidade governamental existe e está ativa
        if doc.government_unit:
            unit = frappe.get_doc("Government Unit", doc.government_unit)
            if not unit.is_active:
                frappe.throw(_("Unidade governamental não está ativa"))
        
    except Exception as e:
        frappe.log_error(f"Budget validation error: {str(e)}", "Validation Error")
        raise

def on_budget_submit(doc, method):
    """Executar quando orçamento é submetido"""
    try:
        # Notificar transparência
        notify_budget_publication(doc)
        
        # Invalidar cache de transparência
        cache_system.invalidate_group("transparency_data")
        
        # Audit da submissão
        audit_system.log_event(
            event_type="BUDGET_SUBMITTED",
            user=frappe.session.user,
            doctype="Public Budget",
            docname=doc.name,
            details={
                "government_unit": doc.government_unit,
                "fiscal_year": doc.fiscal_year,
                "total_revenue": doc.total_revenue,
                "total_expenses": doc.total_expenses
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Budget submit error: {str(e)}", "Budget Error")

def notify_budget_publication(budget_doc):
    """Notificar publicação de orçamento"""
    try:
        # Criar notificação para usuários interessados
        users_to_notify = frappe.get_all(
            "User",
            filters={
                "enabled": 1,
                "government_level": budget_doc.get("government_level")
            },
            fields=["name", "email"]
        )
        
        for user in users_to_notify:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"Novo orçamento publicado: {budget_doc.title}",
                "for_user": user.name,
                "email_content": f"Um novo orçamento foi publicado para {budget_doc.government_unit}",
                "document_type": "Public Budget",
                "document_name": budget_doc.name
            }).insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Budget notification error: {str(e)}", "Notification Error")

def invalidate_tender_cache_hook(doc, method):
    """Hook para invalidar cache de licitações"""
    try:
        invalidate_tender_cache()
        
        # Invalidar cache relacionado
        cache_system.invalidate_group("procurement")
        cache_system.invalidate_group("transparency_data")
        
    except Exception as e:
        frappe.log_error(f"Tender cache invalidation error: {str(e)}", "Cache Error")

def validate_public_tender(doc, method):
    """Validar licitação pública"""
    try:
        # Validar tipo de licitação
        if doc.get('tender_type'):
            if not GovNextValidator.validate_tender_type(doc.tender_type):
                frappe.throw(_("Tipo de licitação inválido"))
        
        # Validar datas
        if doc.get('start_date') and doc.get('end_date'):
            if doc.start_date >= doc.end_date:
                frappe.throw(_("Data de início deve ser anterior à data de fim"))
        
        # Validar valor total
        if doc.get('total_value'):
            if not GovNextValidator.validate_currency(doc.total_value):
                frappe.throw(_("Valor total inválido"))
        
        # Verificar se unidade governamental existe e está ativa
        if doc.government_unit:
            unit = frappe.get_doc("Government Unit", doc.government_unit)
            if not unit.is_active:
                frappe.throw(_("Unidade governamental não está ativa"))
        
        # Validar modalidade baseada no valor (Lei 8.666/93)
        if doc.total_value and doc.tender_type:
            validate_tender_modality_by_value(doc)
        
    except Exception as e:
        frappe.log_error(f"Tender validation error: {str(e)}", "Validation Error")
        raise

def validate_tender_modality_by_value(doc):
    """Validar modalidade de licitação baseada no valor (Lei 8.666/93)"""
    try:
        value = float(doc.total_value)
        tender_type = doc.tender_type
        
        # Limites para obras e serviços de engenharia
        if doc.get('category') == 'Obras e Serviços de Engenharia':
            if tender_type == 'Convite' and value > 150000:
                frappe.throw(_("Valor excede limite para modalidade Convite em obras/engenharia (R$ 150.000)"))
            elif tender_type == 'Tomada de Preços' and value > 1500000:
                frappe.throw(_("Valor excede limite para modalidade Tomada de Preços em obras/engenharia (R$ 1.500.000)"))
        
        # Limites para outros serviços e compras
        else:
            if tender_type == 'Convite' and value > 80000:
                frappe.throw(_("Valor excede limite para modalidade Convite (R$ 80.000)"))
            elif tender_type == 'Tomada de Preços' and value > 650000:
                frappe.throw(_("Valor excede limite para modalidade Tomada de Preços (R$ 650.000)"))
        
    except (ValueError, TypeError):
        # Se não conseguir converter valor, pular validação
        pass
    except Exception as e:
        frappe.log_error(f"Tender modality validation error: {str(e)}", "Validation Error")

def on_tender_submit(doc, method):
    """Executar quando licitação é submetida"""
    try:
        # Notificar publicação
        notify_tender_publication(doc)
        
        # Invalidar cache de transparência
        cache_system.invalidate_group("transparency_data")
        
        # Audit da submissão
        audit_system.log_event(
            event_type="TENDER_SUBMITTED",
            user=frappe.session.user,
            doctype="Public Tender",
            docname=doc.name,
            details={
                "government_unit": doc.government_unit,
                "tender_type": doc.tender_type,
                "total_value": doc.total_value,
                "start_date": doc.start_date,
                "end_date": doc.end_date
            }
        )
        
    except Exception as e:
        frappe.log_error(f"Tender submit error: {str(e)}", "Tender Error")

def notify_tender_publication(tender_doc):
    """Notificar publicação de licitação"""
    try:
        # Criar notificação para usuários interessados
        users_to_notify = frappe.get_all(
            "User",
            filters={
                "enabled": 1,
                "government_level": tender_doc.get("government_level")
            },
            fields=["name", "email"]
        )
        
        for user in users_to_notify:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"Nova licitação publicada: {tender_doc.tender_title}",
                "for_user": user.name,
                "email_content": f"Uma nova licitação foi publicada: {tender_doc.tender_title}",
                "document_type": "Public Tender",
                "document_name": tender_doc.name
            }).insert(ignore_permissions=True)
        
        # Webhook para sistemas externos
        trigger_tender_webhook(tender_doc)
        
    except Exception as e:
        frappe.log_error(f"Tender notification error: {str(e)}", "Notification Error")

def trigger_tender_webhook(tender_doc):
    """Disparar webhook para licitação"""
    try:
        webhook_data = {
            "event": "tender_published",
            "data": {
                "name": tender_doc.name,
                "title": tender_doc.tender_title,
                "government_unit": tender_doc.government_unit,
                "tender_type": tender_doc.tender_type,
                "total_value": tender_doc.total_value,
                "start_date": str(tender_doc.start_date),
                "end_date": str(tender_doc.end_date),
                "published_at": frappe.utils.now()
            }
        }
        
        # Enfileirar job para envio de webhook
        frappe.enqueue(
            "govnext_core.webhooks.send_webhook",
            queue="default",
            timeout=300,
            event="tender_published",
            data=webhook_data
        )
        
    except Exception as e:
        frappe.log_error(f"Tender webhook error: {str(e)}", "Webhook Error")