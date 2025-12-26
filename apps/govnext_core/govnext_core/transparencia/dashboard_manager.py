# -*- coding: utf-8 -*-
"""
Módulo de Dashboards para Portal da Transparência
Sistema avançado de visualização de dados governamentais
"""

import frappe
from frappe import _
from datetime import datetime, date, timedelta
import json
import calendar
from ..utils.cache_manager import cached_function, cache_manager

class TransparencyDashboardManager:
    """Gerenciador de dashboards de transparência"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
    
    def get_executive_dashboard(self, year=None, month=None):
        """Dashboard executivo principal"""
        year = year or self.current_year
        month = month or self.current_month
        
        try:
            dashboard = {
                "periodo": {
                    "ano": year,
                    "mes": month,
                    "mes_nome": calendar.month_name[month],
                    "ultima_atualizacao": frappe.utils.now()
                },
                "indicadores_principais": self.get_main_indicators(year, month),
                "receitas_despesas": self.get_revenue_expense_summary(year, month),
                "execucao_orcamentaria": self.get_budget_execution(year),
                "licitacoes_contratos": self.get_tenders_contracts_summary(year),
                "obras_publicas": self.get_public_works_summary(year),
                "transparencia_metrics": self.get_transparency_metrics(year, month)
            }
            
            return {
                "success": True,
                "data": dashboard
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Executive Dashboard Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    @cached_function('transparency_data', ttl=1800)
    def get_main_indicators(self, year, month):
        """Indicadores principais do município"""
        # Receita total do ano
        receita_total = frappe.db.sql("""
            SELECT SUM(debit) as total
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
        """, [year])[0][0] or 0
        
        # Despesa total do ano
        despesa_total = frappe.db.sql("""
            SELECT SUM(credit) as total
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
        """, [year])[0][0] or 0
        
        # Receita do mês
        receita_mes = frappe.db.sql("""
            SELECT SUM(debit) as total
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND MONTH(posting_date) = %s
            AND is_cancelled = 0
        """, [year, month])[0][0] or 0
        
        # Despesa do mês
        despesa_mes = frappe.db.sql("""
            SELECT SUM(credit) as total
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND MONTH(posting_date) = %s
            AND is_cancelled = 0
        """, [year, month])[0][0] or 0
        
        # Obras em execução
        obras_execucao = frappe.db.count("Obra Publica", {"status": "Em Execução"})
        
        # Licitações ativas
        licitacoes_ativas = frappe.db.count("Public Tender", {"status": "Active"})
        
        # População estimada (valor configurável)
        populacao = frappe.db.get_single_value("Municipality Settings", "population") or 50000
        
        # Calcular per capita
        receita_per_capita = receita_total / populacao if populacao > 0 else 0
        despesa_per_capita = despesa_total / populacao if populacao > 0 else 0
        
        return {
            "receita_total_ano": receita_total,
            "despesa_total_ano": despesa_total,
            "saldo_ano": receita_total - despesa_total,
            "receita_mes": receita_mes,
            "despesa_mes": despesa_mes,
            "saldo_mes": receita_mes - despesa_mes,
            "obras_em_execucao": obras_execucao,
            "licitacoes_ativas": licitacoes_ativas,
            "populacao": populacao,
            "receita_per_capita": receita_per_capita,
            "despesa_per_capita": despesa_per_capita
        }
    
    @cached_function('transparency_data', ttl=3600)
    def get_revenue_expense_summary(self, year, month):
        """Resumo de receitas e despesas"""
        # Receitas por categoria
        receitas_categoria = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 3) as categoria,
                SUM(debit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 3)
            ORDER BY valor DESC
        """, [year], as_dict=True)
        
        # Despesas por categoria
        despesas_categoria = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 3) as categoria,
                SUM(credit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 3)
            ORDER BY valor DESC
        """, [year], as_dict=True)
        
        # Evolução mensal
        evolucao_mensal = []
        for mes in range(1, 13):
            receita_mes = frappe.db.sql("""
                SELECT SUM(debit) as total
                FROM `tabGL Entry`
                WHERE account LIKE '3.%'
                AND YEAR(posting_date) = %s
                AND MONTH(posting_date) = %s
                AND is_cancelled = 0
            """, [year, mes])[0][0] or 0
            
            despesa_mes = frappe.db.sql("""
                SELECT SUM(credit) as total
                FROM `tabGL Entry`
                WHERE account LIKE '4.%'
                AND YEAR(posting_date) = %s
                AND MONTH(posting_date) = %s
                AND is_cancelled = 0
            """, [year, mes])[0][0] or 0
            
            evolucao_mensal.append({
                "mes": mes,
                "mes_nome": calendar.month_abbr[mes],
                "receitas": receita_mes,
                "despesas": despesa_mes,
                "saldo": receita_mes - despesa_mes
            })
        
        return {
            "receitas_por_categoria": receitas_categoria,
            "despesas_por_categoria": despesas_categoria,
            "evolucao_mensal": evolucao_mensal
        }
    
    @cached_function('budget_data', ttl=7200)
    def get_budget_execution(self, year):
        """Execução orçamentária"""
        # Execução por função
        execucao_funcao = frappe.db.sql("""
            SELECT 
                account_name as funcao,
                budget_amount as orcado,
                actual_amount as realizado,
                (actual_amount / budget_amount * 100) as percentual
            FROM `tabBudget Account`
            WHERE parent IN (
                SELECT name FROM `tabBudget`
                WHERE fiscal_year = %s
            )
            AND budget_amount > 0
            ORDER BY budget_amount DESC
            LIMIT 10
        """, [year], as_dict=True)
        
        # Resumo geral
        resumo_orcamento = frappe.db.sql("""
            SELECT 
                SUM(budget_amount) as total_orcado,
                SUM(actual_amount) as total_realizado
            FROM `tabBudget Account`
            WHERE parent IN (
                SELECT name FROM `tabBudget`
                WHERE fiscal_year = %s
            )
        """, [year], as_dict=True)
        
        resumo = resumo_orcamento[0] if resumo_orcamento else {
            "total_orcado": 0,
            "total_realizado": 0
        }
        
        if resumo["total_orcado"] > 0:
            resumo["percentual_execucao"] = (resumo["total_realizado"] / resumo["total_orcado"]) * 100
        else:
            resumo["percentual_execucao"] = 0
        
        return {
            "resumo": resumo,
            "execucao_por_funcao": execucao_funcao
        }
    
    @cached_function('transparency_data', ttl=3600)
    def get_tenders_contracts_summary(self, year):
        """Resumo de licitações e contratos"""
        # Licitações por status
        licitacoes_status = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as quantidade,
                SUM(estimated_amount) as valor_total
            FROM `tabPublic Tender`
            WHERE YEAR(opening_date) = %s
            GROUP BY status
        """, [year], as_dict=True)
        
        # Contratos vigentes
        contratos_vigentes = frappe.db.sql("""
            SELECT 
                COUNT(*) as quantidade,
                SUM(total_amount) as valor_total
            FROM `tabPurchase Order`
            WHERE docstatus = 1
            AND end_date >= CURDATE()
            AND YEAR(transaction_date) = %s
        """, [year], as_dict=True)
        
        # Maiores contratos
        maiores_contratos = frappe.db.sql("""
            SELECT 
                name as numero,
                supplier as fornecedor,
                total_amount as valor,
                transaction_date as data
            FROM `tabPurchase Order`
            WHERE docstatus = 1
            AND YEAR(transaction_date) = %s
            ORDER BY total_amount DESC
            LIMIT 10
        """, [year], as_dict=True)
        
        return {
            "licitacoes_por_status": licitacoes_status,
            "contratos_vigentes": contratos_vigentes[0] if contratos_vigentes else {"quantidade": 0, "valor_total": 0},
            "maiores_contratos": maiores_contratos
        }
    
    @cached_function('municipal_data', ttl=3600)
    def get_public_works_summary(self, year):
        """Resumo de obras públicas"""
        # Obras por status
        obras_status = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as quantidade,
                SUM(valor_orcado) as valor_total
            FROM `tabObra Publica`
            WHERE YEAR(data_criacao) = %s
            GROUP BY status
        """, [year], as_dict=True)
        
        # Investimento por tipo
        investimento_tipo = frappe.db.sql("""
            SELECT 
                tipo_obra,
                COUNT(*) as quantidade,
                SUM(valor_orcado) as investimento
            FROM `tabObra Publica`
            WHERE YEAR(data_criacao) = %s
            GROUP BY tipo_obra
            ORDER BY investimento DESC
        """, [year], as_dict=True)
        
        # Obras em destaque (maiores investimentos)
        obras_destaque = frappe.db.sql("""
            SELECT 
                codigo,
                nome,
                status,
                valor_orcado,
                percentual_executado
            FROM `tabObra Publica`
            WHERE YEAR(data_criacao) = %s
            ORDER BY valor_orcado DESC
            LIMIT 5
        """, [year], as_dict=True)
        
        return {
            "obras_por_status": obras_status,
            "investimento_por_tipo": investimento_tipo,
            "obras_em_destaque": obras_destaque
        }
    
    @cached_function('transparency_data', ttl=1800)
    def get_transparency_metrics(self, year, month):
        """Métricas de transparência e acesso"""
        # Acessos ao portal (simulado - implementar com analytics real)
        acessos_mes = frappe.db.count("Web Page View", {
            "creation": [">=", f"{year}-{month:02d}-01"]
        })
        
        # Downloads de dados
        downloads_dados = frappe.db.count("File", {
            "attached_to_doctype": ["in", ["Public Budget", "Public Tender", "GL Entry"]],
            "creation": [">=", f"{year}-{month:02d}-01"]
        })
        
        # Solicitações de informação
        solicitacoes_info = frappe.db.count("Request Log", {
            "creation": [">=", f"{year}-{month:02d}-01"]
        })
        
        # Tempo médio de resposta (simulado)
        tempo_resposta_medio = 5.2  # dias
        
        # Índice de transparência (calculado)
        indice_transparencia = self.calculate_transparency_index(year)
        
        return {
            "acessos_portal_mes": acessos_mes,
            "downloads_dados_mes": downloads_dados,
            "solicitacoes_info_mes": solicitacoes_info,
            "tempo_resposta_medio_dias": tempo_resposta_medio,
            "indice_transparencia": indice_transparencia
        }
    
    def calculate_transparency_index(self, year):
        """Calcular índice de transparência"""
        # Critérios para índice de transparência
        criterios = {
            "receitas_publicadas": 0,
            "despesas_publicadas": 0,
            "licitacoes_publicadas": 0,
            "contratos_publicados": 0,
            "orcamento_publicado": 0,
            "obras_publicadas": 0
        }
        
        # Verificar se dados estão sendo publicados regularmente
        meses_com_receitas = frappe.db.sql("""
            SELECT COUNT(DISTINCT MONTH(posting_date))
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
        """, [year])[0][0] or 0
        
        criterios["receitas_publicadas"] = min(meses_com_receitas / 12 * 100, 100)
        
        meses_com_despesas = frappe.db.sql("""
            SELECT COUNT(DISTINCT MONTH(posting_date))
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
        """, [year])[0][0] or 0
        
        criterios["despesas_publicadas"] = min(meses_com_despesas / 12 * 100, 100)
        
        # Licitações e contratos
        licitacoes_ano = frappe.db.count("Public Tender", {"YEAR(opening_date)": year})
        criterios["licitacoes_publicadas"] = min(licitacoes_ano / 10 * 100, 100)  # Meta: 10 licitações/ano
        
        contratos_ano = frappe.db.count("Purchase Order", {"YEAR(transaction_date)": year})
        criterios["contratos_publicados"] = min(contratos_ano / 20 * 100, 100)  # Meta: 20 contratos/ano
        
        # Orçamento
        orcamento_existe = frappe.db.exists("Budget", {"fiscal_year": year})
        criterios["orcamento_publicado"] = 100 if orcamento_existe else 0
        
        # Obras
        obras_ano = frappe.db.count("Obra Publica", {"YEAR(data_criacao)": year})
        criterios["obras_publicadas"] = min(obras_ano / 5 * 100, 100)  # Meta: 5 obras/ano
        
        # Calcular média ponderada
        pesos = {
            "receitas_publicadas": 0.2,
            "despesas_publicadas": 0.2,
            "licitacoes_publicadas": 0.15,
            "contratos_publicados": 0.15,
            "orcamento_publicado": 0.15,
            "obras_publicadas": 0.15
        }
        
        indice = sum(criterios[k] * pesos[k] for k in criterios.keys())
        
        return {
            "indice_geral": round(indice, 1),
            "criterios": criterios,
            "classificacao": self.get_transparency_classification(indice)
        }
    
    def get_transparency_classification(self, indice):
        """Classificar nível de transparência"""
        if indice >= 90:
            return {"nivel": "Excelente", "cor": "success"}
        elif indice >= 75:
            return {"nivel": "Bom", "cor": "primary"}
        elif indice >= 60:
            return {"nivel": "Regular", "cor": "warning"}
        else:
            return {"nivel": "Insuficiente", "cor": "danger"}
    
    def get_financial_dashboard(self, year=None):
        """Dashboard financeiro detalhado"""
        year = year or self.current_year
        
        try:
            # Análise de receitas
            analise_receitas = self.get_detailed_revenue_analysis(year)
            
            # Análise de despesas
            analise_despesas = self.get_detailed_expense_analysis(year)
            
            # Comparativo com anos anteriores
            comparativo_anos = self.get_year_comparison(year)
            
            # Projeções
            projecoes = self.get_financial_projections(year)
            
            dashboard = {
                "ano": year,
                "analise_receitas": analise_receitas,
                "analise_despesas": analise_despesas,
                "comparativo_anos": comparativo_anos,
                "projecoes": projecoes,
                "ultima_atualizacao": frappe.utils.now()
            }
            
            return {
                "success": True,
                "data": dashboard
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @cached_function('financial_data', ttl=3600)
    def get_detailed_revenue_analysis(self, year):
        """Análise detalhada de receitas"""
        # Receitas por fonte
        receitas_fonte = frappe.db.sql("""
            SELECT 
                CASE 
                    WHEN account LIKE '3.1%' THEN 'Receitas Correntes'
                    WHEN account LIKE '3.2%' THEN 'Receitas de Capital'
                    ELSE 'Outras Receitas'
                END as fonte,
                SUM(debit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY fonte
        """, [year], as_dict=True)
        
        # Receitas tributárias vs não tributárias
        receitas_tipo = frappe.db.sql("""
            SELECT 
                CASE 
                    WHEN account LIKE '3.1.1%' THEN 'Tributárias'
                    ELSE 'Não Tributárias'
                END as tipo,
                SUM(debit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '3.1%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY tipo
        """, [year], as_dict=True)
        
        # Top 10 receitas
        top_receitas = frappe.db.sql("""
            SELECT 
                account as conta,
                SUM(debit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY account
            ORDER BY valor DESC
            LIMIT 10
        """, [year], as_dict=True)
        
        return {
            "receitas_por_fonte": receitas_fonte,
            "receitas_por_tipo": receitas_tipo,
            "top_receitas": top_receitas
        }
    
    @cached_function('financial_data', ttl=3600)
    def get_detailed_expense_analysis(self, year):
        """Análise detalhada de despesas"""
        # Despesas por função
        despesas_funcao = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 5) as funcao,
                SUM(credit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY funcao
            ORDER BY valor DESC
            LIMIT 10
        """, [year], as_dict=True)
        
        # Despesas correntes vs capital
        despesas_tipo = frappe.db.sql("""
            SELECT 
                CASE 
                    WHEN account LIKE '4.1%' OR account LIKE '4.2%' THEN 'Correntes'
                    WHEN account LIKE '4.3%' OR account LIKE '4.4%' THEN 'Capital'
                    ELSE 'Outras'
                END as tipo,
                SUM(credit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY tipo
        """, [year], as_dict=True)
        
        # Maiores fornecedores
        maiores_fornecedores = frappe.db.sql("""
            SELECT 
                party as fornecedor,
                SUM(credit) as valor_total
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            AND party IS NOT NULL
            GROUP BY party
            ORDER BY valor_total DESC
            LIMIT 10
        """, [year], as_dict=True)
        
        return {
            "despesas_por_funcao": despesas_funcao,
            "despesas_por_tipo": despesas_tipo,
            "maiores_fornecedores": maiores_fornecedores
        }
    
    def get_year_comparison(self, year):
        """Comparativo entre anos"""
        comparativo = []
        
        for ano in range(year - 2, year + 1):
            receita = frappe.db.sql("""
                SELECT SUM(debit) as total
                FROM `tabGL Entry`
                WHERE account LIKE '3.%'
                AND YEAR(posting_date) = %s
                AND is_cancelled = 0
            """, [ano])[0][0] or 0
            
            despesa = frappe.db.sql("""
                SELECT SUM(credit) as total
                FROM `tabGL Entry`
                WHERE account LIKE '4.%'
                AND YEAR(posting_date) = %s
                AND is_cancelled = 0
            """, [ano])[0][0] or 0
            
            comparativo.append({
                "ano": ano,
                "receita": receita,
                "despesa": despesa,
                "saldo": receita - despesa
            })
        
        return comparativo
    
    def get_financial_projections(self, year):
        """Projeções financeiras"""
        # Calcular tendência baseada nos meses já decorridos
        meses_decorridos = datetime.now().month if year == self.current_year else 12
        
        receita_acumulada = frappe.db.sql("""
            SELECT SUM(debit) as total
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND MONTH(posting_date) <= %s
            AND is_cancelled = 0
        """, [year, meses_decorridos])[0][0] or 0
        
        despesa_acumulada = frappe.db.sql("""
            SELECT SUM(credit) as total
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND MONTH(posting_date) <= %s
            AND is_cancelled = 0
        """, [year, meses_decorridos])[0][0] or 0
        
        if meses_decorridos > 0 and year == self.current_year:
            projecao_receita = (receita_acumulada / meses_decorridos) * 12
            projecao_despesa = (despesa_acumulada / meses_decorridos) * 12
        else:
            projecao_receita = receita_acumulada
            projecao_despesa = despesa_acumulada
        
        return {
            "receita_acumulada": receita_acumulada,
            "despesa_acumulada": despesa_acumulada,
            "projecao_receita_anual": projecao_receita,
            "projecao_despesa_anual": projecao_despesa,
            "projecao_saldo": projecao_receita - projecao_despesa,
            "meses_decorridos": meses_decorridos
        }

# Instância global
dashboard_manager = TransparencyDashboardManager()

# APIs públicas
@frappe.whitelist(allow_guest=True)
def get_executive_dashboard_api(year=None, month=None):
    """API para dashboard executivo"""
    return dashboard_manager.get_executive_dashboard(
        int(year) if year else None,
        int(month) if month else None
    )

@frappe.whitelist(allow_guest=True)
def get_financial_dashboard_api(year=None):
    """API para dashboard financeiro"""
    return dashboard_manager.get_financial_dashboard(
        int(year) if year else None
    )

@frappe.whitelist(allow_guest=True)
def get_transparency_index():
    """API para índice de transparência"""
    year = datetime.now().year
    month = datetime.now().month
    metrics = dashboard_manager.get_transparency_metrics(year, month)
    
    return {
        "success": True,
        "data": metrics["indice_transparencia"]
    }