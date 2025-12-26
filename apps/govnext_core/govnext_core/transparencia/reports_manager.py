# -*- coding: utf-8 -*-
"""
Módulo de Relatórios de Transparência
Sistema completo para geração de relatórios governamentais
"""

import frappe
from frappe import _
from datetime import datetime, date, timedelta
import json
import pandas as pd
import io
import base64
from ..utils.cache_manager import cached_function
from ..utils.audit import audit_operation

class TransparencyReportsManager:
    """Gerenciador de relatórios de transparência"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
    
    def generate_report(self, report_type, parameters, format_type="json"):
        """Gerar relatório baseado no tipo"""
        try:
            report_generators = {
                "receitas_despesas": self.generate_revenue_expense_report,
                "execucao_orcamentaria": self.generate_budget_execution_report,
                "licitacoes_contratos": self.generate_tenders_contracts_report,
                "obras_publicas": self.generate_public_works_report,
                "prestacao_contas": self.generate_accountability_report,
                "transparencia_geral": self.generate_general_transparency_report,
                "compliance_lai": self.generate_lai_compliance_report,
                "analise_financeira": self.generate_financial_analysis_report,
                "fornecedores": self.generate_suppliers_report,
                "funcionarios": self.generate_employees_report
            }
            
            if report_type not in report_generators:
                frappe.throw(_("Tipo de relatório não suportado: {0}").format(report_type))
            
            # Gerar dados do relatório
            report_data = report_generators[report_type](parameters)
            
            # Formatear saída baseado no tipo solicitado
            if format_type.lower() == "excel":
                return self.export_to_excel(report_data, report_type)
            elif format_type.lower() == "pdf":
                return self.export_to_pdf(report_data, report_type)
            elif format_type.lower() == "csv":
                return self.export_to_csv(report_data, report_type)
            else:
                return {
                    "success": True,
                    "data": report_data,
                    "report_type": report_type,
                    "generated_at": frappe.utils.now()
                }
                
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Report Generation Error: {report_type}")
            return {
                "success": False,
                "error": str(e),
                "report_type": report_type
            }
    
    @cached_function('reports_data', ttl=1800)
    def generate_revenue_expense_report(self, parameters):
        """Relatório detalhado de receitas e despesas"""
        year = parameters.get("year", self.current_year)
        month_start = parameters.get("month_start", 1)
        month_end = parameters.get("month_end", 12)
        detail_level = parameters.get("detail_level", "summary")
        
        # Receitas detalhadas
        receitas_query = """
            SELECT 
                account as conta,
                account_name as nome_conta,
                SUM(debit) as valor,
                MONTH(posting_date) as mes,
                COUNT(*) as numero_lancamentos
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND MONTH(posting_date) BETWEEN %s AND %s
            AND is_cancelled = 0
            GROUP BY account, MONTH(posting_date)
            ORDER BY account, mes
        """
        
        receitas = frappe.db.sql(receitas_query, [year, month_start, month_end], as_dict=True)
        
        # Despesas detalhadas
        despesas_query = """
            SELECT 
                account as conta,
                account_name as nome_conta,
                party as favorecido,
                SUM(credit) as valor,
                MONTH(posting_date) as mes,
                COUNT(*) as numero_lancamentos
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND MONTH(posting_date) BETWEEN %s AND %s
            AND is_cancelled = 0
            GROUP BY account, party, MONTH(posting_date)
            ORDER BY account, mes, valor DESC
        """
        
        despesas = frappe.db.sql(despesas_query, [year, month_start, month_end], as_dict=True)
        
        # Resumo por categoria
        resumo_receitas = self.categorize_accounts(receitas, "receita")
        resumo_despesas = self.categorize_accounts(despesas, "despesa")
        
        # Comparativo mensal
        comparativo_mensal = self.get_monthly_comparison(year, month_start, month_end)
        
        return {
            "parametros": {
                "ano": year,
                "mes_inicio": month_start,
                "mes_fim": month_end,
                "nivel_detalhe": detail_level
            },
            "receitas": {
                "detalhado": receitas,
                "resumo_categoria": resumo_receitas,
                "total": sum(r["valor"] for r in receitas)
            },
            "despesas": {
                "detalhado": despesas,
                "resumo_categoria": resumo_despesas,
                "total": sum(d["valor"] for d in despesas)
            },
            "comparativo_mensal": comparativo_mensal,
            "saldo_periodo": sum(r["valor"] for r in receitas) - sum(d["valor"] for d in despesas)
        }
    
    @cached_function('reports_data', ttl=3600)
    def generate_budget_execution_report(self, parameters):
        """Relatório de execução orçamentária"""
        year = parameters.get("year", self.current_year)
        include_projections = parameters.get("include_projections", True)
        
        # Execução por órgão/unidade
        execucao_orgao = frappe.db.sql("""
            SELECT 
                b.cost_center as orgao,
                ba.account_name as funcao,
                ba.budget_amount as orcado,
                ba.actual_amount as realizado,
                (ba.actual_amount / ba.budget_amount * 100) as percentual_execucao,
                (ba.budget_amount - ba.actual_amount) as saldo_disponivel
            FROM `tabBudget Account` ba
            JOIN `tabBudget` b ON ba.parent = b.name
            WHERE b.fiscal_year = %s
            AND ba.budget_amount > 0
            ORDER BY b.cost_center, ba.account_name
        """, [year], as_dict=True)
        
        # Resumo por função de governo
        resumo_funcao = frappe.db.sql("""
            SELECT 
                SUBSTRING(ba.account, 1, 2) as codigo_funcao,
                SUM(ba.budget_amount) as total_orcado,
                SUM(ba.actual_amount) as total_realizado,
                (SUM(ba.actual_amount) / SUM(ba.budget_amount) * 100) as percentual_execucao
            FROM `tabBudget Account` ba
            JOIN `tabBudget` b ON ba.parent = b.name
            WHERE b.fiscal_year = %s
            AND ba.budget_amount > 0
            GROUP BY SUBSTRING(ba.account, 1, 2)
            ORDER BY total_orcado DESC
        """, [year], as_dict=True)
        
        # Evolução mensal da execução
        evolucao_mensal = []
        for mes in range(1, 13):
            execucao_mes = frappe.db.sql("""
                SELECT 
                    SUM(ba.budget_amount) as orcado,
                    SUM(CASE WHEN MONTH(ge.posting_date) <= %s THEN ge.credit ELSE 0 END) as realizado_ate_mes
                FROM `tabBudget Account` ba
                JOIN `tabBudget` b ON ba.parent = b.name
                LEFT JOIN `tabGL Entry` ge ON ge.account = ba.account 
                    AND YEAR(ge.posting_date) = %s 
                    AND ge.is_cancelled = 0
                WHERE b.fiscal_year = %s
            """, [mes, year, year], as_dict=True)
            
            if execucao_mes:
                orcado = execucao_mes[0]["orcado"] or 0
                realizado = execucao_mes[0]["realizado_ate_mes"] or 0
                
                evolucao_mensal.append({
                    "mes": mes,
                    "mes_nome": calendar.month_abbr[mes],
                    "orcado_acumulado": orcado,
                    "realizado_acumulado": realizado,
                    "percentual_execucao": (realizado / orcado * 100) if orcado > 0 else 0
                })
        
        # Análise de variações
        variacoes = self.analyze_budget_variances(execucao_orgao)
        
        return {
            "parametros": {
                "ano": year,
                "inclui_projecoes": include_projections
            },
            "execucao_por_orgao": execucao_orgao,
            "resumo_por_funcao": resumo_funcao,
            "evolucao_mensal": evolucao_mensal,
            "analise_variacoes": variacoes,
            "totais": {
                "total_orcado": sum(e["orcado"] for e in execucao_orgao),
                "total_realizado": sum(e["realizado"] for e in execucao_orgao),
                "percentual_execucao_geral": sum(e["realizado"] for e in execucao_orgao) / sum(e["orcado"] for e in execucao_orgao) * 100 if sum(e["orcado"] for e in execucao_orgao) > 0 else 0
            }
        }
    
    @cached_function('reports_data', ttl=3600)
    def generate_tenders_contracts_report(self, parameters):
        """Relatório de licitações e contratos"""
        year = parameters.get("year", self.current_year)
        include_analysis = parameters.get("include_analysis", True)
        
        # Licitações do período
        licitacoes = frappe.db.sql("""
            SELECT 
                name as numero,
                tender_title as objeto,
                tender_type as modalidade,
                estimated_amount as valor_estimado,
                opening_date as data_abertura,
                status,
                winner as vencedor,
                winner_amount as valor_vencedor
            FROM `tabPublic Tender`
            WHERE YEAR(opening_date) = %s
            ORDER BY opening_date DESC
        """, [year], as_dict=True)
        
        # Contratos decorrentes
        contratos = frappe.db.sql("""
            SELECT 
                po.name as numero_contrato,
                po.supplier as fornecedor,
                po.total_amount as valor_contrato,
                po.transaction_date as data_assinatura,
                po.schedule_date as prazo_entrega,
                CASE 
                    WHEN po.schedule_date >= CURDATE() THEN 'Vigente'
                    ELSE 'Vencido'
                END as situacao
            FROM `tabPurchase Order` po
            WHERE po.docstatus = 1
            AND YEAR(po.transaction_date) = %s
            ORDER BY po.total_amount DESC
        """, [year], as_dict=True)
        
        # Análises estatísticas
        analises = {}
        if include_analysis:
            analises = {
                "licitacoes_por_modalidade": self.group_by_field(licitacoes, "modalidade", "valor_estimado"),
                "economia_obtida": self.calculate_bid_savings(licitacoes),
                "fornecedores_mais_contratados": self.get_top_suppliers(contratos),
                "distribuicao_valores": self.analyze_value_distribution(contratos),
                "tempo_medio_licitacao": self.calculate_average_bidding_time(year)
            }
        
        return {
            "parametros": {
                "ano": year,
                "inclui_analises": include_analysis
            },
            "licitacoes": licitacoes,
            "contratos": contratos,
            "analises": analises,
            "resumo": {
                "total_licitacoes": len(licitacoes),
                "valor_total_estimado": sum(l.get("valor_estimado", 0) for l in licitacoes),
                "total_contratos": len(contratos),
                "valor_total_contratado": sum(c.get("valor_contrato", 0) for c in contratos)
            }
        }
    
    @cached_function('reports_data', ttl=3600)
    def generate_public_works_report(self, parameters):
        """Relatório de obras públicas"""
        year = parameters.get("year", self.current_year)
        include_photos = parameters.get("include_photos", False)
        
        # Obras do período
        obras = frappe.db.sql("""
            SELECT 
                codigo,
                nome,
                tipo_obra,
                status,
                valor_orcado,
                valor_contratado,
                valor_executado,
                percentual_executado,
                data_inicio_prevista,
                data_fim_prevista,
                data_inicio_real,
                data_conclusao,
                empresa_contratada,
                endereco
            FROM `tabObra Publica`
            WHERE YEAR(data_criacao) = %s
            ORDER BY valor_orcado DESC
        """, [year], as_dict=True)
        
        # Acompanhamento de cronograma
        cronograma = []
        for obra in obras:
            cronograma_obra = frappe.get_all(
                "Cronograma Obra",
                filters={"obra": obra["codigo"]},
                fields=["etapa", "percentual_fisico", "status", "data_inicio_prevista", "data_fim_prevista"]
            )
            cronograma.append({
                "obra": obra["codigo"],
                "nome": obra["nome"],
                "etapas": cronograma_obra
            })
        
        # Medições realizadas
        medicoes = frappe.db.sql("""
            SELECT 
                mo.obra,
                mo.numero,
                mo.valor_total,
                mo.data_medicao,
                mo.status
            FROM `tabMedicao Obra` mo
            JOIN `tabObra Publica` op ON mo.obra = op.name
            WHERE YEAR(op.data_criacao) = %s
            ORDER BY mo.obra, mo.numero
        """, [year], as_dict=True)
        
        # Fotos das obras (se solicitado)
        fotos = []
        if include_photos:
            fotos = frappe.db.sql("""
                SELECT 
                    fo.obra,
                    fo.titulo,
                    fo.data_foto,
                    fo.arquivo
                FROM `tabFoto Obra` fo
                JOIN `tabObra Publica` op ON fo.obra = op.name
                WHERE YEAR(op.data_criacao) = %s
                ORDER BY fo.obra, fo.data_foto DESC
            """, [year], as_dict=True)
        
        return {
            "parametros": {
                "ano": year,
                "inclui_fotos": include_photos
            },
            "obras": obras,
            "cronograma": cronograma,
            "medicoes": medicoes,
            "fotos": fotos,
            "resumo": {
                "total_obras": len(obras),
                "valor_total_orcado": sum(o.get("valor_orcado", 0) for o in obras),
                "obras_em_execucao": len([o for o in obras if o["status"] == "Em Execução"]),
                "obras_concluidas": len([o for o in obras if o["status"] == "Concluída"]),
                "percentual_medio_execucao": sum(o.get("percentual_executado", 0) for o in obras) / len(obras) if obras else 0
            }
        }
    
    def generate_accountability_report(self, parameters):
        """Relatório de prestação de contas"""
        year = parameters.get("year", self.current_year)
        quarter = parameters.get("quarter", None)
        
        # Demonstrativo de receitas realizadas
        receitas_realizadas = self.get_realized_revenues(year, quarter)
        
        # Demonstrativo de despesas realizadas
        despesas_realizadas = self.get_realized_expenses(year, quarter)
        
        # Demonstrativo da dívida ativa
        divida_ativa = self.get_active_debt(year)
        
        # Indicadores fiscais
        indicadores_fiscais = self.calculate_fiscal_indicators(year)
        
        # Cumprimento de metas fiscais
        metas_fiscais = self.check_fiscal_targets(year)
        
        return {
            "parametros": {
                "ano": year,
                "trimestre": quarter,
                "data_geracao": frappe.utils.now()
            },
            "receitas_realizadas": receitas_realizadas,
            "despesas_realizadas": despesas_realizadas,
            "divida_ativa": divida_ativa,
            "indicadores_fiscais": indicadores_fiscais,
            "metas_fiscais": metas_fiscais
        }
    
    def generate_general_transparency_report(self, parameters):
        """Relatório geral de transparência"""
        year = parameters.get("year", self.current_year)
        
        # Compilar todos os dados principais
        dados_gerais = {
            "receitas_despesas": self.generate_revenue_expense_report({"year": year}),
            "orcamento": self.generate_budget_execution_report({"year": year}),
            "licitacoes": self.generate_tenders_contracts_report({"year": year}),
            "obras": self.generate_public_works_report({"year": year})
        }
        
        # Índices de transparência
        indices_transparencia = self.calculate_transparency_indices(year)
        
        # Compliance com leis
        compliance = self.check_legal_compliance(year)
        
        return {
            "parametros": {
                "ano": year,
                "tipo": "Relatório Geral de Transparência"
            },
            "dados_gerais": dados_gerais,
            "indices_transparencia": indices_transparencia,
            "compliance_legal": compliance
        }
    
    # Métodos auxiliares
    def categorize_accounts(self, entries, account_type):
        """Categorizar contas por tipo"""
        categories = {}
        
        for entry in entries:
            if account_type == "receita":
                if entry["conta"].startswith("3.1.1"):
                    category = "Receitas Tributárias"
                elif entry["conta"].startswith("3.1.2"):
                    category = "Receitas de Contribuições"
                elif entry["conta"].startswith("3.1.3"):
                    category = "Receita Patrimonial"
                elif entry["conta"].startswith("3.1.4"):
                    category = "Receita de Serviços"
                elif entry["conta"].startswith("3.2"):
                    category = "Receitas de Capital"
                else:
                    category = "Outras Receitas"
            else:  # despesa
                if entry["conta"].startswith("4.1"):
                    category = "Despesas Correntes"
                elif entry["conta"].startswith("4.4"):
                    category = "Despesas de Capital"
                else:
                    category = "Outras Despesas"
            
            if category not in categories:
                categories[category] = {"valor": 0, "quantidade": 0}
            
            categories[category]["valor"] += entry["valor"]
            categories[category]["quantidade"] += 1
        
        return categories
    
    def get_monthly_comparison(self, year, month_start, month_end):
        """Comparativo mensal"""
        comparison = []
        
        for month in range(month_start, month_end + 1):
            receitas = frappe.db.sql("""
                SELECT SUM(debit) as total
                FROM `tabGL Entry`
                WHERE account LIKE '3.%'
                AND YEAR(posting_date) = %s
                AND MONTH(posting_date) = %s
                AND is_cancelled = 0
            """, [year, month])[0][0] or 0
            
            despesas = frappe.db.sql("""
                SELECT SUM(credit) as total
                FROM `tabGL Entry`
                WHERE account LIKE '4.%'
                AND YEAR(posting_date) = %s
                AND MONTH(posting_date) = %s
                AND is_cancelled = 0
            """, [year, month])[0][0] or 0
            
            comparison.append({
                "mes": month,
                "receitas": receitas,
                "despesas": despesas,
                "saldo": receitas - despesas
            })
        
        return comparison
    
    def analyze_budget_variances(self, execucao_data):
        """Analisar variações orçamentárias"""
        variacoes = {
            "superexecucao": [],
            "subexecucao": [],
            "execucao_normal": []
        }
        
        for item in execucao_data:
            percentual = item.get("percentual_execucao", 0)
            
            if percentual > 100:
                variacoes["superexecucao"].append(item)
            elif percentual < 70:
                variacoes["subexecucao"].append(item)
            else:
                variacoes["execucao_normal"].append(item)
        
        return variacoes
    
    def group_by_field(self, data, field, value_field=None):
        """Agrupar dados por campo"""
        grouped = {}
        
        for item in data:
            key = item.get(field, "Não Informado")
            
            if key not in grouped:
                grouped[key] = {"count": 0, "total_value": 0}
            
            grouped[key]["count"] += 1
            
            if value_field and item.get(value_field):
                grouped[key]["total_value"] += item[value_field]
        
        return grouped
    
    def calculate_bid_savings(self, licitacoes):
        """Calcular economia obtida em licitações"""
        total_estimado = sum(l.get("valor_estimado", 0) for l in licitacoes if l.get("valor_estimado"))
        total_contratado = sum(l.get("valor_vencedor", 0) for l in licitacoes if l.get("valor_vencedor"))
        
        economia = total_estimado - total_contratado
        percentual = (economia / total_estimado * 100) if total_estimado > 0 else 0
        
        return {
            "valor_estimado_total": total_estimado,
            "valor_contratado_total": total_contratado,
            "economia_absoluta": economia,
            "economia_percentual": percentual
        }
    
    def get_top_suppliers(self, contratos, limit=10):
        """Obter principais fornecedores"""
        fornecedores = {}
        
        for contrato in contratos:
            fornecedor = contrato.get("fornecedor", "Não Informado")
            valor = contrato.get("valor_contrato", 0)
            
            if fornecedor not in fornecedores:
                fornecedores[fornecedor] = {"contratos": 0, "valor_total": 0}
            
            fornecedores[fornecedor]["contratos"] += 1
            fornecedores[fornecedor]["valor_total"] += valor
        
        # Ordenar por valor total
        top_fornecedores = sorted(
            fornecedores.items(),
            key=lambda x: x[1]["valor_total"],
            reverse=True
        )[:limit]
        
        return [{"fornecedor": f, **data} for f, data in top_fornecedores]
    
    def export_to_excel(self, data, report_type):
        """Exportar relatório para Excel"""
        try:
            # Criar arquivo Excel em memória
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Converter dados para DataFrames e escrever em abas
                if report_type == "receitas_despesas":
                    pd.DataFrame(data["receitas"]["detalhado"]).to_excel(writer, sheet_name='Receitas', index=False)
                    pd.DataFrame(data["despesas"]["detalhado"]).to_excel(writer, sheet_name='Despesas', index=False)
                elif report_type == "execucao_orcamentaria":
                    pd.DataFrame(data["execucao_por_orgao"]).to_excel(writer, sheet_name='Execução por Órgão', index=False)
                # Adicionar mais tipos conforme necessário
            
            output.seek(0)
            
            # Codificar em base64 para retorno
            excel_data = base64.b64encode(output.read()).decode()
            
            return {
                "success": True,
                "file_data": excel_data,
                "file_name": f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao gerar Excel: {str(e)}"
            }
    
    def export_to_csv(self, data, report_type):
        """Exportar relatório para CSV"""
        try:
            # Implementar exportação CSV
            csv_data = "Implementar exportação CSV"
            
            return {
                "success": True,
                "file_data": csv_data,
                "file_name": f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "content_type": "text/csv"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao gerar CSV: {str(e)}"
            }
    
    def export_to_pdf(self, data, report_type):
        """Exportar relatório para PDF"""
        try:
            # Implementar exportação PDF
            pdf_data = "Implementar exportação PDF"
            
            return {
                "success": True,
                "file_data": pdf_data,
                "file_name": f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "content_type": "application/pdf"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao gerar PDF: {str(e)}"
            }

# Instância global
reports_manager = TransparencyReportsManager()

# APIs públicas
@frappe.whitelist(allow_guest=True)
@audit_operation("GENERATE_TRANSPARENCY_REPORT")
def generate_transparency_report_api(report_type, parameters=None, format_type="json"):
    """API para gerar relatórios de transparência"""
    try:
        if isinstance(parameters, str):
            parameters = json.loads(parameters)
        
        parameters = parameters or {}
        
        return reports_manager.generate_report(report_type, parameters, format_type)
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist(allow_guest=True)
def get_available_reports():
    """API para listar relatórios disponíveis"""
    return {
        "success": True,
        "reports": [
            {
                "type": "receitas_despesas",
                "name": "Receitas e Despesas",
                "description": "Relatório detalhado de receitas e despesas",
                "parameters": ["year", "month_start", "month_end", "detail_level"]
            },
            {
                "type": "execucao_orcamentaria",
                "name": "Execução Orçamentária",
                "description": "Relatório de execução do orçamento",
                "parameters": ["year", "include_projections"]
            },
            {
                "type": "licitacoes_contratos",
                "name": "Licitações e Contratos",
                "description": "Relatório de processos licitatórios e contratos",
                "parameters": ["year", "include_analysis"]
            },
            {
                "type": "obras_publicas",
                "name": "Obras Públicas",
                "description": "Relatório de obras e investimentos",
                "parameters": ["year", "include_photos"]
            },
            {
                "type": "prestacao_contas",
                "name": "Prestação de Contas",
                "description": "Relatório oficial de prestação de contas",
                "parameters": ["year", "quarter"]
            }
        ]
    }