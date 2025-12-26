# -*- coding: utf-8 -*-
"""
Sistema de Auditoria Governamental
Módulo responsável por logging e auditoria de todas as operações do sistema
"""

import frappe
from frappe import _
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import traceback

class GovAuditSystem:
    """Sistema de Auditoria para operações governamentais"""
    
    def __init__(self):
        self.enabled = frappe.conf.get('audit_enabled', True)
        self.retention_days = frappe.conf.get('audit_retention_days', 2555)  # 7 anos
        
    def log_operation(self, operation_type, user, doctype=None, docname=None, 
                      old_doc=None, new_doc=None, details=None):
        """
        Registra operação no log de auditoria
        """
        if not self.enabled:
            return
            
        try:
            audit_log = {
                "doctype": "Audit Log",
                "operation_type": operation_type,
                "user": user,
                "timestamp": frappe.utils.now(),
                "document_type": doctype,
                "document_name": docname,
                "ip_address": getattr(frappe.local, 'request_ip', None),
                "user_agent": getattr(frappe.local.request, 'user_agent', None) if hasattr(frappe.local, 'request') else None,
                "session_id": frappe.session.sid if frappe.session else None,
                "details": json.dumps(details or {}),
                "checksum": None
            }
            
            # Adicionar dados do documento
            if old_doc:
                audit_log["old_values"] = json.dumps(old_doc.as_dict() if hasattr(old_doc, 'as_dict') else old_doc)
            
            if new_doc:
                audit_log["new_values"] = json.dumps(new_doc.as_dict() if hasattr(new_doc, 'as_dict') else new_doc)
            
            # Gerar checksum para integridade
            audit_log["checksum"] = self._generate_checksum(audit_log)
            
            # Inserir log (ignorando permissões para garantir auditoria)
            doc = frappe.get_doc(audit_log)
            doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
            
        except Exception as e:
            # Log de erro de auditoria não deve quebrar operação principal
            frappe.log_error(
                title="Audit System Error",
                message=f"Erro ao registrar auditoria: {str(e)}\n{traceback.format_exc()}"
            )
    
    def _generate_checksum(self, data):
        """Gera checksum SHA-256 para verificação de integridade"""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def verify_log_integrity(self, audit_log_name):
        """Verifica integridade de um log de auditoria"""
        doc = frappe.get_doc("Audit Log", audit_log_name)
        
        # Reconstruir dados para checksum
        data = {
            "operation_type": doc.operation_type,
            "user": doc.user,
            "timestamp": doc.timestamp,
            "document_type": doc.document_type,
            "document_name": doc.document_name,
            "ip_address": doc.ip_address,
            "user_agent": doc.user_agent,
            "session_id": doc.session_id,
            "details": doc.details,
            "old_values": doc.old_values,
            "new_values": doc.new_values
        }
        
        expected_checksum = self._generate_checksum(data)
        return doc.checksum == expected_checksum

# Instância global do sistema de auditoria
audit_system = GovAuditSystem()

def audit_operation(operation_type, details=None):
    """Decorator para auditoria automática de operações"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = frappe.session.user if frappe.session else "System"
            
            try:
                result = func(*args, **kwargs)
                
                # Log de sucesso
                audit_system.log_operation(
                    operation_type=f"{operation_type}_SUCCESS",
                    user=user,
                    details=details
                )
                
                return result
                
            except Exception as e:
                # Log de erro
                audit_system.log_operation(
                    operation_type=f"{operation_type}_ERROR",
                    user=user,
                    details={
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        **(details or {})
                    }
                )
                raise
                
        return wrapper
    return decorator

def audit_document_change(doc, method):
    """Hook para auditoria de mudanças em documentos"""
    if not audit_system.enabled:
        return
    
    # Não auditar logs de auditoria (evitar recursão)
    if doc.doctype in ["Audit Log", "Security Log", "Error Log"]:
        return
    
    user = frappe.session.user if frappe.session else "System"
    
    # Obter versão anterior para comparação
    old_doc = None
    if method in ["before_save", "before_cancel", "before_delete"]:
        if hasattr(doc, 'name') and doc.name and frappe.db.exists(doc.doctype, doc.name):
            old_doc = frappe.get_doc(doc.doctype, doc.name)
    
    operation_mapping = {
        "before_insert": "CREATE",
        "after_insert": "CREATE",
        "before_save": "UPDATE", 
        "after_save": "UPDATE",
        "before_cancel": "CANCEL",
        "after_cancel": "CANCEL",
        "before_delete": "DELETE",
        "after_delete": "DELETE"
    }
    
    operation_type = operation_mapping.get(method, method.upper())
    
    audit_system.log_operation(
        operation_type=operation_type,
        user=user,
        doctype=doc.doctype,
        docname=getattr(doc, 'name', None),
        old_doc=old_doc,
        new_doc=doc if method.startswith('after_') else None,
        details={
            "method": method,
            "flags": getattr(doc, 'flags', {})
        }
    )

def log_api_request(response):
    """Log de requisições da API"""
    if not audit_system.enabled:
        return
    
    if not hasattr(frappe.local, 'request'):
        return
    
    request = frappe.local.request
    
    # Filtrar endpoints que não precisam de auditoria
    skip_paths = ['/api/method/ping', '/api/method/version', '/assets/']
    if any(request.path.startswith(path) for path in skip_paths):
        return
    
    audit_system.log_operation(
        operation_type="API_REQUEST",
        user=frappe.session.user if frappe.session else "Anonymous",
        details={
            "method": request.method,
            "path": request.path,
            "query_string": request.query_string.decode() if request.query_string else None,
            "status_code": getattr(response, 'status_code', None),
            "response_size": len(response.data) if hasattr(response, 'data') else None
        }
    )

@frappe.whitelist()
def get_audit_trail(doctype, docname, limit=50):
    """Obter trilha de auditoria para um documento específico"""
    if not frappe.has_permission("Audit Log", "read"):
        frappe.throw(_("Sem permissão para acessar logs de auditoria"))
    
    filters = {
        "document_type": doctype,
        "document_name": docname
    }
    
    logs = frappe.get_all(
        "Audit Log",
        filters=filters,
        fields=[
            "name", "operation_type", "user", "timestamp", 
            "details", "old_values", "new_values"
        ],
        order_by="timestamp desc",
        limit=limit
    )
    
    # Verificar integridade dos logs
    for log in logs:
        log["integrity_verified"] = audit_system.verify_log_integrity(log["name"])
    
    return logs

@frappe.whitelist()
def generate_audit_report(from_date, to_date, operation_types=None, users=None):
    """Gerar relatório de auditoria"""
    if not frappe.has_permission("Audit Log", "read"):
        frappe.throw(_("Sem permissão para gerar relatórios de auditoria"))
    
    filters = {
        "timestamp": ["between", [from_date, to_date]]
    }
    
    if operation_types:
        filters["operation_type"] = ["in", operation_types]
    
    if users:
        filters["user"] = ["in", users]
    
    # Estatísticas gerais
    total_operations = frappe.db.count("Audit Log", filters)
    
    # Operações por tipo
    operations_by_type = frappe.db.sql("""
        SELECT operation_type, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp BETWEEN %s AND %s
        GROUP BY operation_type
        ORDER BY count DESC
    """, [from_date, to_date], as_dict=True)
    
    # Operações por usuário
    operations_by_user = frappe.db.sql("""
        SELECT user, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp BETWEEN %s AND %s
        GROUP BY user
        ORDER BY count DESC
        LIMIT 20
    """, [from_date, to_date], as_dict=True)
    
    # Operações por documento
    operations_by_doctype = frappe.db.sql("""
        SELECT document_type, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp BETWEEN %s AND %s
        AND document_type IS NOT NULL
        GROUP BY document_type
        ORDER BY count DESC
        LIMIT 20
    """, [from_date, to_date], as_dict=True)
    
    return {
        "summary": {
            "total_operations": total_operations,
            "period": f"{from_date} a {to_date}",
            "generated_at": frappe.utils.now(),
            "generated_by": frappe.session.user
        },
        "operations_by_type": operations_by_type,
        "operations_by_user": operations_by_user,
        "operations_by_doctype": operations_by_doctype
    }

@frappe.whitelist()
def cleanup_old_audit_logs():
    """Limpeza automática de logs antigos"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Sem permissão para limpeza de logs"))
    
    cutoff_date = frappe.utils.add_days(
        frappe.utils.nowdate(), 
        -audit_system.retention_days
    )
    
    # Contar logs que serão removidos
    count = frappe.db.count(
        "Audit Log",
        {"timestamp": ["<", cutoff_date]}
    )
    
    if count > 0:
        # Fazer backup antes de deletar
        backup_old_logs(cutoff_date)
        
        # Deletar logs antigos
        frappe.db.sql("""
            DELETE FROM `tabAudit Log`
            WHERE timestamp < %s
        """, [cutoff_date])
        
        frappe.db.commit()
        
        return {
            "message": _("Limpeza concluída"),
            "deleted_count": count,
            "cutoff_date": cutoff_date
        }
    
    return {"message": _("Nenhum log antigo encontrado")}

def backup_old_logs(cutoff_date):
    """Fazer backup de logs antigos antes da exclusão"""
    import os
    import gzip
    
    backup_dir = frappe.get_site_path("private", "backups", "audit_logs")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Exportar logs para arquivo
    old_logs = frappe.db.sql("""
        SELECT * FROM `tabAudit Log`
        WHERE timestamp < %s
        ORDER BY timestamp
    """, [cutoff_date], as_dict=True)
    
    if old_logs:
        backup_file = os.path.join(
            backup_dir, 
            f"audit_logs_{cutoff_date}_{frappe.utils.nowdate()}.json.gz"
        )
        
        with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
            json.dump(old_logs, f, default=str, indent=2)
        
        frappe.log_error(
            title="Audit Logs Backup",
            message=f"Backup criado: {backup_file} ({len(old_logs)} registros)"
        )

# Funções de validação e compliance
@frappe.whitelist()
def validate_audit_integrity():
    """Validar integridade de todos os logs de auditoria"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Sem permissão para validação de integridade"))
    
    # Verificar logs dos últimos 30 dias
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -30)
    
    logs = frappe.get_all(
        "Audit Log",
        filters={"timestamp": [">", from_date]},
        fields=["name"],
        limit=10000
    )
    
    verified = 0
    corrupted = []
    
    for log in logs:
        if audit_system.verify_log_integrity(log["name"]):
            verified += 1
        else:
            corrupted.append(log["name"])
    
    return {
        "total_checked": len(logs),
        "verified": verified,
        "corrupted": len(corrupted),
        "corrupted_logs": corrupted[:10],  # Primeiros 10
        "integrity_percentage": round((verified / len(logs)) * 100, 2) if logs else 100
    }

# Compliance e relatórios legais
@frappe.whitelist()
def generate_compliance_report(report_type="LAI"):
    """Gerar relatórios de compliance (LAI, LRF, LGPD, etc.)"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Sem permissão para relatórios de compliance"))
    
    if report_type == "LAI":
        return generate_lai_compliance_report()
    elif report_type == "LGPD":
        return generate_lgpd_compliance_report()
    elif report_type == "LRF":
        return generate_lrf_compliance_report()
    else:
        frappe.throw(_("Tipo de relatório não suportado"))

def generate_lai_compliance_report():
    """Relatório de compliance Lei de Acesso à Informação"""
    # Últimos 12 meses
    from_date = frappe.utils.add_months(frappe.utils.nowdate(), -12)
    
    # Acessos a informações públicas
    transparency_access = frappe.db.sql("""
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp >= %s
        AND operation_type = 'API_REQUEST'
        AND JSON_EXTRACT(details, '$.path') LIKE '/transparencia%%'
        GROUP BY DATE(timestamp)
        ORDER BY date
    """, [from_date], as_dict=True)
    
    return {
        "report_type": "LAI",
        "period": f"{from_date} a {frappe.utils.nowdate()}",
        "transparency_access": transparency_access,
        "total_access": sum(item["count"] for item in transparency_access)
    }

def generate_lgpd_compliance_report():
    """Relatório de compliance LGPD"""
    # Operações envolvendo dados pessoais
    personal_data_operations = frappe.db.sql("""
        SELECT operation_type, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp >= %s
        AND (
            document_type = 'User'
            OR JSON_EXTRACT(details, '$.involves_personal_data') = true
        )
        GROUP BY operation_type
    """, [frappe.utils.add_months(frappe.utils.nowdate(), -12)], as_dict=True)
    
    return {
        "report_type": "LGPD",
        "personal_data_operations": personal_data_operations
    }

def generate_lrf_compliance_report():
    """Relatório de compliance Lei de Responsabilidade Fiscal"""
    # Operações financeiras e orçamentárias
    fiscal_operations = frappe.db.sql("""
        SELECT operation_type, COUNT(*) as count
        FROM `tabAudit Log`
        WHERE timestamp >= %s
        AND (
            document_type IN ('Public Budget', 'Purchase Order', 'Payment Entry')
            OR JSON_EXTRACT(details, '$.fiscal_operation') = true
        )
        GROUP BY operation_type
    """, [frappe.utils.add_months(frappe.utils.nowdate(), -12)], as_dict=True)
    
    return {
        "report_type": "LRF", 
        "fiscal_operations": fiscal_operations
    }