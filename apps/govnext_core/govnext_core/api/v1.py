# -*- coding: utf-8 -*-
"""
GovNext API v1
API REST para integração com sistemas governamentais
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from ..utils.cache_manager import cached_function, cache_manager
from ..utils.audit import audit_operation
from .v1.utils.response_formatter import format_api_response, api_error_handler
from .v1.middleware.rate_limiter import rate_limit
from .common import validate_api_key, get_api_permissions

# Configuração da API
API_VERSION = "1.0"
API_PREFIX = "/api/v1"

# ========== ENDPOINTS DE TRANSPARÊNCIA ==========

@frappe.whitelist(allow_guest=True)
@rate_limit(100, 3600)  # 100 requests per hour
@api_error_handler
def get_transparency_data(category=None, year=None, month=None, limit=100, offset=0):
    """
    Endpoint principal para dados de transparência
    """
    try:
        filters = {}
        
        if year:
            filters['year'] = int(year)
        
        if month:
            filters['month'] = int(month)
        
        if category == "receitas":
            data = get_revenue_data(filters, limit, offset)
        elif category == "despesas":
            data = get_expense_data(filters, limit, offset)
        elif category == "contratos":
            data = get_contract_data(filters, limit, offset)
        elif category == "licitacoes":
            data = get_tender_data(filters, limit, offset)
        elif category == "orcamento":
            data = get_budget_data(filters, limit, offset)
        elif category == "servidores":
            data = get_employee_data(filters, limit, offset)
        else:
            data = get_general_transparency_data(filters, limit, offset)
        
        return format_api_response(
            data=data,
            message="Dados de transparência obtidos com sucesso",
            meta={
                "category": category,
                "total_records": len(data) if isinstance(data, list) else 1,
                "api_version": API_VERSION
            }
        )
        
    except Exception as e:
        return format_api_response(
            success=False,
            message=str(e),
            error_code="TRANSPARENCY_ERROR"
        )

@cached_function('transparency_data', ttl=1800)
def get_revenue_data(filters, limit, offset):
    """Obter dados de receitas"""
    conditions = []
    values = []
    
    if filters.get('year'):
        conditions.append("YEAR(posting_date) = %s")
        values.append(filters['year'])
    
    if filters.get('month'):
        conditions.append("MONTH(posting_date) = %s")
        values.append(filters['month'])
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            account as conta,
            SUM(debit) as valor,
            posting_date as data,
            voucher_no as documento,
            remarks as observacoes
        FROM `tabGL Entry`
        WHERE is_cancelled = 0
        AND account LIKE '3.%'  -- Contas de receita
        {where_clause}
        GROUP BY account, posting_date, voucher_no
        ORDER BY posting_date DESC
        LIMIT %s OFFSET %s
    """
    
    values.extend([limit, offset])
    
    return frappe.db.sql(query, values, as_dict=True)

@cached_function('transparency_data', ttl=1800)
def get_expense_data(filters, limit, offset):
    """Obter dados de despesas"""
    conditions = []
    values = []
    
    if filters.get('year'):
        conditions.append("YEAR(posting_date) = %s")
        values.append(filters['year'])
    
    if filters.get('month'):
        conditions.append("MONTH(posting_date) = %s")
        values.append(filters['month'])
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            account as conta,
            SUM(credit) as valor,
            posting_date as data,
            voucher_no as documento,
            remarks as observacoes,
            party as favorecido
        FROM `tabGL Entry`
        WHERE is_cancelled = 0
        AND account LIKE '4.%'  -- Contas de despesa
        {where_clause}
        GROUP BY account, posting_date, voucher_no, party
        ORDER BY posting_date DESC
        LIMIT %s OFFSET %s
    """
    
    values.extend([limit, offset])
    
    return frappe.db.sql(query, values, as_dict=True)

@cached_function('transparency_data', ttl=3600)
def get_contract_data(filters, limit, offset):
    """Obter dados de contratos"""
    conditions = []
    values = []
    
    if filters.get('year'):
        conditions.append("YEAR(start_date) = %s")
        values.append(filters['year'])
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            name as numero_contrato,
            title as objeto,
            supplier as contratado,
            total_amount as valor,
            start_date as data_inicio,
            end_date as data_fim,
            status
        FROM `tabPurchase Order`
        WHERE docstatus = 1
        {where_clause}
        ORDER BY start_date DESC
        LIMIT %s OFFSET %s
    """
    
    values.extend([limit, offset])
    
    return frappe.db.sql(query, values, as_dict=True)

@cached_function('transparency_data', ttl=3600)
def get_tender_data(filters, limit, offset):
    """Obter dados de licitações"""
    conditions = []
    values = []
    
    if filters.get('year'):
        conditions.append("YEAR(opening_date) = %s")
        values.append(filters['year'])
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            name as numero_licitacao,
            tender_title as objeto,
            tender_type as modalidade,
            estimated_amount as valor_estimado,
            opening_date as data_abertura,
            status,
            winner as vencedor
        FROM `tabPublic Tender`
        WHERE docstatus >= 0
        {where_clause}
        ORDER BY opening_date DESC
        LIMIT %s OFFSET %s
    """
    
    values.extend([limit, offset])
    
    return frappe.db.sql(query, values, as_dict=True)

@cached_function('budget_data', ttl=3600)
def get_budget_data(filters, limit, offset):
    """Obter dados orçamentários"""
    year = filters.get('year', datetime.now().year)
    
    query = """
        SELECT 
            account as conta,
            budget_amount as orcado,
            actual_amount as realizado,
            (actual_amount / budget_amount * 100) as percentual_execucao
        FROM `tabBudget Account`
        WHERE parent IN (
            SELECT name FROM `tabBudget`
            WHERE fiscal_year = %s
        )
        ORDER BY account
        LIMIT %s OFFSET %s
    """
    
    return frappe.db.sql(query, [year, limit, offset], as_dict=True)

@cached_function('transparency_data', ttl=7200)
def get_employee_data(filters, limit, offset):
    """Obter dados de servidores (dados públicos apenas)"""
    conditions = []
    values = []
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            employee_name as nome,
            designation as cargo,
            department as lotacao,
            date_of_joining as data_admissao,
            employment_type as tipo_vinculo,
            status
        FROM `tabEmployee`
        WHERE status = 'Active'
        {where_clause}
        ORDER BY employee_name
        LIMIT %s OFFSET %s
    """
    
    values.extend([limit, offset])
    
    return frappe.db.sql(query, values, as_dict=True)

def get_general_transparency_data(filters, limit, offset):
    """Obter dados gerais de transparência"""
    return {
        "resumo_receitas": get_revenue_summary(filters.get('year')),
        "resumo_despesas": get_expense_summary(filters.get('year')),
        "licitacoes_ativas": get_active_tenders_count(),
        "contratos_vigentes": get_active_contracts_count(),
        "execucao_orcamentaria": get_budget_execution_percentage(filters.get('year'))
    }

# ========== ENDPOINTS DE ORÇAMENTO ==========

@frappe.whitelist(allow_guest=True)
@rate_limit(50, 3600)
@api_error_handler
def get_budget_summary(year=None):
    """Resumo da execução orçamentária"""
    year = year or datetime.now().year
    
    data = cache_manager.get('budget_data', f'summary_{year}')
    
    if not data:
        # Calcular dados orçamentários
        budget_query = """
            SELECT 
                SUM(budget_amount) as total_orcado,
                SUM(actual_amount) as total_realizado
            FROM `tabBudget Account`
            WHERE parent IN (
                SELECT name FROM `tabBudget`
                WHERE fiscal_year = %s
            )
        """
        
        result = frappe.db.sql(budget_query, [year], as_dict=True)
        
        if result:
            total_orcado = result[0].get('total_orcado', 0)
            total_realizado = result[0].get('total_realizado', 0)
            
            data = {
                "ano": year,
                "total_orcado": total_orcado,
                "total_realizado": total_realizado,
                "percentual_execucao": round((total_realizado / total_orcado * 100), 2) if total_orcado > 0 else 0,
                "saldo_disponivel": total_orcado - total_realizado
            }
        else:
            data = {
                "ano": year,
                "total_orcado": 0,
                "total_realizado": 0,
                "percentual_execucao": 0,
                "saldo_disponivel": 0
            }
        
        cache_manager.set('budget_data', f'summary_{year}', data, ttl=3600)
    
    return format_api_response(data=data, message="Resumo orçamentário obtido com sucesso")

# ========== ENDPOINTS MUNICIPAIS ==========

@frappe.whitelist(allow_guest=True)
@rate_limit(100, 3600)
@api_error_handler
def get_municipal_data(category=None):
    """Dados específicos municipais"""
    if category == "iptu":
        data = get_iptu_data()
    elif category == "iss":
        data = get_iss_data()
    elif category == "alvaras":
        data = get_license_data()
    elif category == "obras":
        data = get_public_works_data()
    else:
        data = get_municipal_summary()
    
    return format_api_response(data=data, message="Dados municipais obtidos com sucesso")

@cached_function('municipal_data', ttl=3600)
def get_iptu_data():
    """Dados de IPTU"""
    current_year = datetime.now().year
    
    return {
        "arrecadacao_atual": frappe.db.sql("""
            SELECT SUM(valor_pago) 
            FROM `tabIPTU Payment`
            WHERE YEAR(data_pagamento) = %s
        """, [current_year])[0][0] or 0,
        "imoveis_cadastrados": frappe.db.count("IPTU Cadastro"),
        "carnês_emitidos": frappe.db.count("IPTU Lancamento", {
            "ano_referencia": current_year
        }),
        "inadimplencia": calculate_iptu_default_rate(current_year)
    }

@cached_function('municipal_data', ttl=3600)
def get_iss_data():
    """Dados de ISS"""
    current_year = datetime.now().year
    
    return {
        "arrecadacao_atual": frappe.db.sql("""
            SELECT SUM(valor_iss) 
            FROM `tabISS Declaracao`
            WHERE YEAR(data_competencia) = %s
        """, [current_year])[0][0] or 0,
        "prestadores_ativos": frappe.db.count("ISS Prestador", {"ativo": 1}),
        "declaracoes_mes": frappe.db.count("ISS Declaracao", {
            "data_competencia": [">=", frappe.utils.get_first_day()]
        })
    }

@cached_function('municipal_data', ttl=7200)
def get_license_data():
    """Dados de licenças e alvarás"""
    current_year = datetime.now().year
    
    return {
        "alvaras_emitidos": frappe.db.count("Alvara Municipal", {
            "data_emissao": [">=", f"{current_year}-01-01"]
        }),
        "licencas_vigentes": frappe.db.count("Alvara Municipal", {
            "data_vencimento": [">=", frappe.utils.nowdate()]
        }),
        "processos_andamento": frappe.db.count("Processo Licenciamento", {
            "status": "Em Análise"
        })
    }

@cached_function('municipal_data', ttl=3600)
def get_public_works_data():
    """Dados de obras públicas"""
    return {
        "obras_andamento": frappe.db.count("Obra Publica", {"status": "Em Execução"}),
        "obras_concluidas": frappe.db.count("Obra Publica", {"status": "Concluída"}),
        "investimento_total": frappe.db.sql("""
            SELECT SUM(valor_contrato) 
            FROM `tabObra Publica`
            WHERE status IN ('Em Execução', 'Concluída')
        """)[0][0] or 0
    }

def get_municipal_summary():
    """Resumo geral municipal"""
    return {
        "iptu": get_iptu_data(),
        "iss": get_iss_data(),
        "alvaras": get_license_data(),
        "obras": get_public_works_data()
    }

# ========== ENDPOINTS DE RELATÓRIOS ==========

@frappe.whitelist()
@rate_limit(20, 3600)
@audit_operation("GENERATE_REPORT")
@api_error_handler
def generate_transparency_report(report_type, format="json", filters=None):
    """Gerar relatórios de transparência"""
    if not validate_api_key():
        frappe.throw(_("Chave de API inválida"))
    
    permissions = get_api_permissions()
    if "generate_reports" not in permissions:
        frappe.throw(_("Sem permissão para gerar relatórios"))
    
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    filters = filters or {}
    
    if report_type == "receitas_despesas":
        data = generate_revenue_expense_report(filters)
    elif report_type == "execucao_orcamentaria":
        data = generate_budget_execution_report(filters)
    elif report_type == "contratos_licitacoes":
        data = generate_contracts_tenders_report(filters)
    elif report_type == "compliance":
        data = generate_compliance_report(filters)
    else:
        frappe.throw(_("Tipo de relatório não suportado"))
    
    if format.lower() == "pdf":
        return generate_pdf_report(data, report_type)
    elif format.lower() == "excel":
        return generate_excel_report(data, report_type)
    else:
        return format_api_response(data=data, message="Relatório gerado com sucesso")

# ========== ENDPOINTS DE BUSCA ==========

@frappe.whitelist(allow_guest=True)
@rate_limit(200, 3600)
@api_error_handler
def search_transparency_data(query, category=None, limit=50):
    """Busca unificada nos dados de transparência"""
    if not query or len(query) < 3:
        frappe.throw(_("Query deve ter pelo menos 3 caracteres"))
    
    results = {
        "receitas": search_revenue_data(query, limit) if not category or category == "receitas" else [],
        "despesas": search_expense_data(query, limit) if not category or category == "despesas" else [],
        "contratos": search_contract_data(query, limit) if not category or category == "contratos" else [],
        "licitacoes": search_tender_data(query, limit) if not category or category == "licitacoes" else [],
        "servidores": search_employee_data(query, limit) if not category or category == "servidores" else []
    }
    
    # Calcular total de resultados
    total_results = sum(len(results[key]) for key in results)
    
    return format_api_response(
        data=results,
        message=f"Busca concluída: {total_results} resultados encontrados",
        meta={
            "query": query,
            "category": category,
            "total_results": total_results
        }
    )

# ========== FUNÇÕES AUXILIARES ==========

def calculate_iptu_default_rate(year):
    """Calcular taxa de inadimplência do IPTU"""
    total_lancado = frappe.db.count("IPTU Lancamento", {"ano_referencia": year})
    total_pago = frappe.db.sql("""
        SELECT COUNT(DISTINCT imovel_codigo)
        FROM `tabIPTU Payment`
        WHERE YEAR(data_pagamento) = %s
    """, [year])[0][0] or 0
    
    if total_lancado == 0:
        return 0
    
    return round(((total_lancado - total_pago) / total_lancado * 100), 2)

def get_revenue_summary(year=None):
    """Resumo de receitas"""
    year = year or datetime.now().year
    
    return frappe.db.sql("""
        SELECT SUM(debit) as total
        FROM `tabGL Entry`
        WHERE account LIKE '3.%'
        AND YEAR(posting_date) = %s
        AND is_cancelled = 0
    """, [year])[0][0] or 0

def get_expense_summary(year=None):
    """Resumo de despesas"""
    year = year or datetime.now().year
    
    return frappe.db.sql("""
        SELECT SUM(credit) as total
        FROM `tabGL Entry`
        WHERE account LIKE '4.%'
        AND YEAR(posting_date) = %s
        AND is_cancelled = 0
    """, [year])[0][0] or 0

def get_active_tenders_count():
    """Contar licitações ativas"""
    return frappe.db.count("Public Tender", {"status": "Active"})

def get_active_contracts_count():
    """Contar contratos vigentes"""
    return frappe.db.count("Purchase Order", {
        "docstatus": 1,
        "end_date": [">=", frappe.utils.nowdate()]
    })

def get_budget_execution_percentage(year=None):
    """Percentual de execução orçamentária"""
    year = year or datetime.now().year
    
    result = frappe.db.sql("""
        SELECT 
            SUM(budget_amount) as orcado,
            SUM(actual_amount) as realizado
        FROM `tabBudget Account`
        WHERE parent IN (
            SELECT name FROM `tabBudget`
            WHERE fiscal_year = %s
        )
    """, [year], as_dict=True)
    
    if result and result[0].get('orcado', 0) > 0:
        return round((result[0].get('realizado', 0) / result[0].get('orcado', 0) * 100), 2)
    
    return 0

# ========== FUNÇÕES DE BUSCA ==========

def search_revenue_data(query, limit):
    """Buscar nos dados de receita"""
    return frappe.db.sql("""
        SELECT account, SUM(debit) as valor, posting_date
        FROM `tabGL Entry`
        WHERE account LIKE '3.%'
        AND (account LIKE %s OR remarks LIKE %s)
        AND is_cancelled = 0
        GROUP BY account, posting_date
        ORDER BY posting_date DESC
        LIMIT %s
    """, [f"%{query}%", f"%{query}%", limit], as_dict=True)

def search_expense_data(query, limit):
    """Buscar nos dados de despesa"""
    return frappe.db.sql("""
        SELECT account, SUM(credit) as valor, posting_date, party
        FROM `tabGL Entry`
        WHERE account LIKE '4.%'
        AND (account LIKE %s OR remarks LIKE %s OR party LIKE %s)
        AND is_cancelled = 0
        GROUP BY account, posting_date, party
        ORDER BY posting_date DESC
        LIMIT %s
    """, [f"%{query}%", f"%{query}%", f"%{query}%", limit], as_dict=True)

def search_contract_data(query, limit):
    """Buscar nos dados de contratos"""
    return frappe.db.sql("""
        SELECT name, title, supplier, total_amount, start_date
        FROM `tabPurchase Order`
        WHERE docstatus = 1
        AND (title LIKE %s OR supplier LIKE %s)
        ORDER BY start_date DESC
        LIMIT %s
    """, [f"%{query}%", f"%{query}%", limit], as_dict=True)

def search_tender_data(query, limit):
    """Buscar nos dados de licitações"""
    return frappe.db.sql("""
        SELECT name, tender_title, tender_type, estimated_amount, opening_date
        FROM `tabPublic Tender`
        WHERE tender_title LIKE %s
        ORDER BY opening_date DESC
        LIMIT %s
    """, [f"%{query}%", limit], as_dict=True)

def search_employee_data(query, limit):
    """Buscar nos dados de servidores"""
    return frappe.db.sql("""
        SELECT employee_name, designation, department
        FROM `tabEmployee`
        WHERE status = 'Active'
        AND (employee_name LIKE %s OR designation LIKE %s OR department LIKE %s)
        ORDER BY employee_name
        LIMIT %s
    """, [f"%{query}%", f"%{query}%", f"%{query}%", limit], as_dict=True)

# ========== RELATÓRIOS ==========

def generate_revenue_expense_report(filters):
    """Gerar relatório de receitas e despesas"""
    year = filters.get('year', datetime.now().year)
    
    return {
        "receitas": get_revenue_data(filters, 1000, 0),
        "despesas": get_expense_data(filters, 1000, 0),
        "resumo": {
            "total_receitas": get_revenue_summary(year),
            "total_despesas": get_expense_summary(year)
        }
    }

def generate_budget_execution_report(filters):
    """Gerar relatório de execução orçamentária"""
    return get_budget_data(filters, 1000, 0)

def generate_contracts_tenders_report(filters):
    """Gerar relatório de contratos e licitações"""
    return {
        "contratos": get_contract_data(filters, 1000, 0),
        "licitacoes": get_tender_data(filters, 1000, 0)
    }

def generate_compliance_report(filters):
    """Gerar relatório de compliance"""
    from ..utils.audit import generate_compliance_report as audit_compliance
    return audit_compliance(filters.get('type', 'LAI'))

def generate_pdf_report(data, report_type):
    """Gerar relatório em PDF"""
    # Implementar geração de PDF
    frappe.throw(_("Geração de PDF não implementada ainda"))

def generate_excel_report(data, report_type):
    """Gerar relatório em Excel"""
    # Implementar geração de Excel
    frappe.throw(_("Geração de Excel não implementada ainda"))