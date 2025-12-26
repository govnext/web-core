# -*- coding: utf-8 -*-
"""
Módulo PCASP (Plano de Contas Aplicado ao Setor Público)
Sistema completo para contabilidade pública brasileira
"""

import frappe
from frappe import _
from datetime import datetime, date
import json

class PCASPManager:
    """Gerenciador do Plano de Contas Aplicado ao Setor Público"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.pcasp_version = "2023"
    
    def create_pcasp_structure(self):
        """Criar estrutura completa do PCASP"""
        try:
            # Classes do PCASP
            classes = [
                {"codigo": "1", "nome": "ATIVO", "tipo": "Ativo"},
                {"codigo": "2", "nome": "PASSIVO E PATRIMÔNIO LÍQUIDO", "tipo": "Passivo"},
                {"codigo": "3", "nome": "VARIAÇÕES PATRIMONIAIS AUMENTATIVAS", "tipo": "Receita"},
                {"codigo": "4", "nome": "VARIAÇÕES PATRIMONIAIS DIMINUTIVAS", "tipo": "Despesa"},
                {"codigo": "5", "nome": "CONTROLES DA APROVAÇÃO DO PLANEJAMENTO E ORÇAMENTO", "tipo": "Controle"},
                {"codigo": "6", "nome": "CONTROLES DA EXECUÇÃO DO PLANEJAMENTO E ORÇAMENTO", "tipo": "Controle"},
                {"codigo": "7", "nome": "CONTROLES DEVEDORES", "tipo": "Controle"},
                {"codigo": "8", "nome": "CONTROLES CREDORES", "tipo": "Controle"}
            ]
            
            for classe in classes:
                self.create_account_if_not_exists(
                    classe["codigo"],
                    classe["nome"],
                    None,
                    classe["tipo"],
                    is_group=True
                )
            
            # Criar grupos principais
            self.create_main_groups()
            
            # Criar contas detalhadas mais utilizadas
            self.create_detailed_accounts()
            
            return {
                "success": True,
                "message": "Estrutura PCASP criada com sucesso"
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "PCASP Structure Creation Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_main_groups(self):
        """Criar grupos principais do PCASP"""
        # ATIVO (Classe 1)
        ativo_groups = [
            ("1.1", "ATIVO CIRCULANTE", "1"),
            ("1.2", "ATIVO NÃO CIRCULANTE", "1"),
            ("1.1.1", "CAIXA E EQUIVALENTES DE CAIXA", "1.1"),
            ("1.1.2", "CRÉDITOS A CURTO PRAZO", "1.1"),
            ("1.1.3", "DEMAIS CRÉDITOS E VALORES A CURTO PRAZO", "1.1"),
            ("1.1.4", "INVESTIMENTOS E APLICAÇÕES TEMPORÁRIAS A CURTO PRAZO", "1.1"),
            ("1.1.5", "ESTOQUES", "1.1"),
            ("1.2.1", "ATIVO REALIZÁVEL A LONGO PRAZO", "1.2"),
            ("1.2.2", "INVESTIMENTOS", "1.2"),
            ("1.2.3", "IMOBILIZADO", "1.2"),
            ("1.2.4", "INTANGÍVEL", "1.2")
        ]
        
        # PASSIVO (Classe 2)
        passivo_groups = [
            ("2.1", "PASSIVO CIRCULANTE", "2"),
            ("2.2", "PASSIVO NÃO CIRCULANTE", "2"),
            ("2.3", "PATRIMÔNIO LÍQUIDO", "2"),
            ("2.1.1", "OBRIGAÇÕES TRABALHISTAS, PREVIDENCIÁRIAS E ASSISTENCIAIS A PAGAR", "2.1"),
            ("2.1.2", "EMPRÉSTIMOS E FINANCIAMENTOS A CURTO PRAZO", "2.1"),
            ("2.1.3", "FORNECEDORES E CONTAS A PAGAR A CURTO PRAZO", "2.1"),
            ("2.2.1", "EMPRÉSTIMOS E FINANCIAMENTOS A LONGO PRAZO", "2.2"),
            ("2.2.2", "PROVISÕES A LONGO PRAZO", "2.2"),
            ("2.3.1", "PATRIMÔNIO SOCIAL E CAPITAL SOCIAL", "2.3"),
            ("2.3.2", "RESERVAS DE CAPITAL", "2.3"),
            ("2.3.3", "AJUSTES DE AVALIAÇÃO PATRIMONIAL", "2.3"),
            ("2.3.4", "RESERVAS DE LUCROS", "2.3"),
            ("2.3.5", "DEMAIS RESERVAS", "2.3"),
            ("2.3.6", "RESULTADOS ACUMULADOS", "2.3")
        ]
        
        # RECEITAS (Classe 3)
        receita_groups = [
            ("3.1", "VARIAÇÕES PATRIMONIAIS AUMENTATIVAS ORÇAMENTÁRIAS", "3"),
            ("3.2", "VARIAÇÕES PATRIMONIAIS AUMENTATIVAS EXTRAORÇAMENTÁRIAS", "3"),
            ("3.1.1", "IMPOSTOS, TAXAS E CONTRIBUIÇÕES DE MELHORIA", "3.1"),
            ("3.1.2", "CONTRIBUIÇÕES", "3.1"),
            ("3.1.3", "RECEITA PATRIMONIAL", "3.1"),
            ("3.1.4", "RECEITA DE SERVIÇOS", "3.1"),
            ("3.1.5", "TRANSFERÊNCIAS E DELEGAÇÕES RECEBIDAS", "3.1"),
            ("3.1.9", "OUTRAS VARIAÇÕES PATRIMONIAIS AUMENTATIVAS ORÇAMENTÁRIAS", "3.1")
        ]
        
        # DESPESAS (Classe 4)
        despesa_groups = [
            ("4.1", "VARIAÇÕES PATRIMONIAIS DIMINUTIVAS ORÇAMENTÁRIAS", "4"),
            ("4.2", "VARIAÇÕES PATRIMONIAIS DIMINUTIVAS EXTRAORÇAMENTÁRIAS", "4"),
            ("4.1.1", "PESSOAL E ENCARGOS", "4.1"),
            ("4.1.2", "JUROS E ENCARGOS DA DÍVIDA", "4.1"),
            ("4.1.3", "OUTRAS VARIAÇÕES PATRIMONIAIS DIMINUTIVAS ORÇAMENTÁRIAS", "4.1")
        ]
        
        all_groups = ativo_groups + passivo_groups + receita_groups + despesa_groups
        
        for codigo, nome, parent in all_groups:
            account_type = self.get_account_type_by_code(codigo)
            self.create_account_if_not_exists(codigo, nome, parent, account_type, is_group=True)
    
    def create_detailed_accounts(self):
        """Criar contas detalhadas mais utilizadas"""
        # Contas de Caixa e Bancos
        caixa_accounts = [
            ("1.1.1.1.1.01.00", "CAIXA", "1.1.1", "Asset"),
            ("1.1.1.2.1.01.00", "BANCOS CONTA MOVIMENTO", "1.1.1", "Asset"),
            ("1.1.1.2.1.02.00", "BANCOS CONTA ARRECADAÇÃO", "1.1.1", "Asset")
        ]
        
        # Principais receitas municipais
        receita_accounts = [
            ("3.1.1.1.1.01.00", "IMPOSTO SOBRE A PROPRIEDADE PREDIAL E TERRITORIAL URBANA", "3.1.1", "Income"),
            ("3.1.1.1.1.02.00", "IMPOSTO SOBRE TRANSMISSÃO DE BENS IMÓVEIS", "3.1.1", "Income"),
            ("3.1.1.1.1.04.00", "IMPOSTO SOBRE SERVIÇOS DE QUALQUER NATUREZA", "3.1.1", "Income"),
            ("3.1.1.2.1.01.00", "TAXAS PELO EXERCÍCIO DO PODER DE POLÍCIA", "3.1.1", "Income"),
            ("3.1.1.2.1.02.00", "TAXAS PELA PRESTAÇÃO DE SERVIÇOS", "3.1.1", "Income")
        ]
        
        # Principais despesas
        despesa_accounts = [
            ("4.1.1.1.1.01.00", "REMUNERAÇÃO PELO REGIME PRÓPRIO DE PREVIDÊNCIA SOCIAL", "4.1.1", "Expense"),
            ("4.1.1.1.1.02.00", "REMUNERAÇÃO PELO REGIME GERAL DE PREVIDÊNCIA SOCIAL", "4.1.1", "Expense"),
            ("4.1.1.1.2.01.00", "CONTRIBUIÇÕES PATRONAIS PELO REGIME PRÓPRIO DE PREVIDÊNCIA SOCIAL", "4.1.1", "Expense"),
            ("4.1.3.3.1.01.00", "MATERIAL DE CONSUMO", "4.1.3", "Expense"),
            ("4.1.3.3.2.01.00", "MATERIAL DE DISTRIBUIÇÃO GRATUITA", "4.1.3", "Expense")
        ]
        
        all_accounts = caixa_accounts + receita_accounts + despesa_accounts
        
        for codigo, nome, parent, account_type in all_accounts:
            self.create_account_if_not_exists(codigo, nome, parent, account_type, is_group=False)
    
    def create_account_if_not_exists(self, account_number, account_name, parent_account, account_type, is_group=False):
        """Criar conta se não existir"""
        if not frappe.db.exists("Account", account_number):
            account = frappe.new_doc("Account")
            account.update({
                "account_name": account_name,
                "account_number": account_number,
                "parent_account": parent_account,
                "account_type": account_type,
                "is_group": is_group,
                "company": frappe.defaults.get_user_default("Company"),
                "pcasp_compliant": True
            })
            account.insert(ignore_permissions=True)
    
    def get_account_type_by_code(self, code):
        """Determinar tipo de conta baseado no código PCASP"""
        if code.startswith("1"):
            return "Asset"
        elif code.startswith("2.1") or code.startswith("2.2"):
            return "Liability"
        elif code.startswith("2.3"):
            return "Equity"
        elif code.startswith("3"):
            return "Income"
        elif code.startswith("4"):
            return "Expense"
        else:
            return "Asset"  # Default
    
    def validate_pcasp_entry(self, account, debit=0, credit=0):
        """Validar lançamento conforme PCASP"""
        validations = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Verificar se conta é PCASP compliant
        account_doc = frappe.get_doc("Account", account)
        if not account_doc.pcasp_compliant:
            validations["warnings"].append(f"Conta {account} não está marcada como PCASP compliant")
        
        # Validações por classe
        if account.startswith("1"):  # ATIVO
            if credit > debit:
                validations["errors"].append("Contas de Ativo não podem ter saldo credor")
        elif account.startswith("2.1") or account.startswith("2.2"):  # PASSIVO
            if debit > credit:
                validations["errors"].append("Contas de Passivo devem ter saldo credor")
        elif account.startswith("3"):  # RECEITA
            if debit > credit:
                validations["errors"].append("Contas de Receita devem ter saldo credor")
        elif account.startswith("4"):  # DESPESA
            if credit > debit:
                validations["errors"].append("Contas de Despesa devem ter saldo devedor")
        
        if validations["errors"]:
            validations["is_valid"] = False
        
        return validations
    
    def get_balancete_verificacao(self, year=None, month=None):
        """Gerar Balancete de Verificação conforme PCASP"""
        year = year or self.current_year
        
        filters = {
            "posting_date": ["<=", f"{year}-12-31"],
            "is_cancelled": 0
        }
        
        if month:
            filters["posting_date"] = ["<=", f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"]
        
        # Buscar saldos por conta
        balancete = frappe.db.sql("""
            SELECT 
                account,
                account_name,
                SUM(debit) as total_debit,
                SUM(credit) as total_credit,
                (SUM(debit) - SUM(credit)) as saldo
            FROM `tabGL Entry`
            WHERE is_cancelled = 0
            AND posting_date <= %s
            GROUP BY account
            HAVING (SUM(debit) != 0 OR SUM(credit) != 0)
            ORDER BY account
        """, [f"{year}-12-31" if not month else f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"], as_dict=True)
        
        # Classificar por classe PCASP
        classificado = {
            "1": {"nome": "ATIVO", "contas": []},
            "2": {"nome": "PASSIVO E PATRIMÔNIO LÍQUIDO", "contas": []},
            "3": {"nome": "VARIAÇÕES PATRIMONIAIS AUMENTATIVAS", "contas": []},
            "4": {"nome": "VARIAÇÕES PATRIMONIAIS DIMINUTIVAS", "contas": []},
            "5": {"nome": "CONTROLES DA APROVAÇÃO", "contas": []},
            "6": {"nome": "CONTROLES DA EXECUÇÃO", "contas": []},
            "7": {"nome": "CONTROLES DEVEDORES", "contas": []},
            "8": {"nome": "CONTROLES CREDORES", "contas": []}
        }
        
        for conta in balancete:
            classe = conta["account"][0]
            if classe in classificado:
                classificado[classe]["contas"].append(conta)
        
        return {
            "success": True,
            "data": {
                "periodo": f"{month:02d}/{year}" if month else str(year),
                "balancete_classificado": classificado,
                "totais": {
                    "total_debitos": sum(c["total_debit"] for c in balancete),
                    "total_creditos": sum(c["total_credit"] for c in balancete)
                }
            }
        }
    
    def get_demonstrativo_variacao_patrimonial(self, year=None):
        """Gerar Demonstrativo das Variações Patrimoniais"""
        year = year or self.current_year
        
        # Variações Aumentativas (Receitas - Classe 3)
        var_aumentativas = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 5) as grupo,
                SUM(credit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '3.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 5)
            ORDER BY grupo
        """, [year], as_dict=True)
        
        # Variações Diminutivas (Despesas - Classe 4)
        var_diminutivas = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 5) as grupo,
                SUM(debit) as valor
            FROM `tabGL Entry`
            WHERE account LIKE '4.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 5)
            ORDER BY grupo
        """, [year], as_dict=True)
        
        total_aumentativas = sum(v["valor"] for v in var_aumentativas)
        total_diminutivas = sum(v["valor"] for v in var_diminutivas)
        resultado_patrimonial = total_aumentativas - total_diminutivas
        
        return {
            "success": True,
            "data": {
                "exercicio": year,
                "variacoes_aumentativas": var_aumentativas,
                "variacoes_diminutivas": var_diminutivas,
                "totais": {
                    "total_aumentativas": total_aumentativas,
                    "total_diminutivas": total_diminutivas,
                    "resultado_patrimonial": resultado_patrimonial
                }
            }
        }
    
    def get_balanco_patrimonial(self, year=None):
        """Gerar Balanço Patrimonial conforme PCASP"""
        year = year or self.current_year
        
        # ATIVO (Classe 1)
        ativo = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 3) as grupo,
                SUM(debit - credit) as saldo
            FROM `tabGL Entry`
            WHERE account LIKE '1.%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 3)
            HAVING SUM(debit - credit) != 0
            ORDER BY grupo
        """, [year], as_dict=True)
        
        # PASSIVO (Classe 2.1 e 2.2)
        passivo = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 3) as grupo,
                SUM(credit - debit) as saldo
            FROM `tabGL Entry`
            WHERE account LIKE '2.1%' OR account LIKE '2.2%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 3)
            HAVING SUM(credit - debit) != 0
            ORDER BY grupo
        """, [year], as_dict=True)
        
        # PATRIMÔNIO LÍQUIDO (Classe 2.3)
        patrimonio_liquido = frappe.db.sql("""
            SELECT 
                SUBSTRING(account, 1, 3) as grupo,
                SUM(credit - debit) as saldo
            FROM `tabGL Entry`
            WHERE account LIKE '2.3%'
            AND YEAR(posting_date) = %s
            AND is_cancelled = 0
            GROUP BY SUBSTRING(account, 1, 3)
            HAVING SUM(credit - debit) != 0
            ORDER BY grupo
        """, [year], as_dict=True)
        
        total_ativo = sum(a["saldo"] for a in ativo)
        total_passivo = sum(p["saldo"] for p in passivo)
        total_pl = sum(pl["saldo"] for pl in patrimonio_liquido)
        
        return {
            "success": True,
            "data": {
                "exercicio": year,
                "ativo": {
                    "grupos": ativo,
                    "total": total_ativo
                },
                "passivo": {
                    "grupos": passivo,
                    "total": total_passivo
                },
                "patrimonio_liquido": {
                    "grupos": patrimonio_liquido,
                    "total": total_pl
                },
                "verificacao": {
                    "ativo_total": total_ativo,
                    "passivo_pl_total": total_passivo + total_pl,
                    "diferenca": total_ativo - (total_passivo + total_pl)
                }
            }
        }

# Instância global
pcasp_manager = PCASPManager()

# APIs públicas
@frappe.whitelist()
def create_pcasp_structure_api():
    """API para criar estrutura PCASP"""
    if not frappe.has_permission("Account", "create"):
        frappe.throw(_("Sem permissão para criar contas"))
    
    return pcasp_manager.create_pcasp_structure()

@frappe.whitelist()
def get_balancete_verificacao_api(year=None, month=None):
    """API para Balancete de Verificação"""
    return pcasp_manager.get_balancete_verificacao(
        int(year) if year else None,
        int(month) if month else None
    )

@frappe.whitelist()
def get_demonstrativo_variacao_patrimonial_api(year=None):
    """API para Demonstrativo das Variações Patrimoniais"""
    return pcasp_manager.get_demonstrativo_variacao_patrimonial(
        int(year) if year else None
    )

@frappe.whitelist()
def get_balanco_patrimonial_api(year=None):
    """API para Balanço Patrimonial"""
    return pcasp_manager.get_balanco_patrimonial(
        int(year) if year else None
    )

@frappe.whitelist()
def validate_pcasp_entry_api(account, debit=0, credit=0):
    """API para validar lançamento PCASP"""
    return pcasp_manager.validate_pcasp_entry(
        account,
        float(debit),
        float(credit)
    )