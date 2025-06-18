# -*- coding: utf-8 -*-
"""
Plano de Contas - PCASP (Plano de Contas Aplicado ao Setor Público)
Implementação completa do plano de contas público conforme padrões TCU
"""

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
import re
from datetime import datetime

class PlanoContas(Document):
    """
    Classe para gerenciamento do Plano de Contas PCASP
    Implementa validações e funcionalidades específicas do setor público
    """
    
    def validate(self):
        """Validações do plano de contas PCASP"""
        self.validar_codigo_pcasp()
        self.validar_hierarquia()
        self.calcular_nivel_conta()
        self.validar_conta_analitica()
        self.validar_vigencia()
        self.validar_natureza_conta()
        
    def before_save(self):
        """Ações antes de salvar"""
        self.processar_classificacao_pcasp()
        self.definir_funcao_conta()
        
    def validar_codigo_pcasp(self):
        """Validar formato do código PCASP (8 níveis)"""
        if not self.codigo_conta:
            frappe.throw(_("Código da conta é obrigatório"))
            
        # Formato PCASP: X.X.X.X.X.XX.XX.XX
        padrao_pcasp = r'^\d\.\d\.\d\.\d\.\d\.\d{2}\.\d{2}\.\d{2}$'
        
        if not re.match(padrao_pcasp, self.codigo_conta):
            frappe.throw(_("Código da conta deve seguir o formato PCASP de 8 níveis (ex: 1.1.1.1.1.01.01.01)"))
            
        # Validar primeiro dígito (classe)
        primeiro_digito = self.codigo_conta[0]
        classes_validas = ['1', '2', '3', '4', '5', '6', '7', '8']
        
        if primeiro_digito not in classes_validas:
            frappe.throw(_("Primeiro dígito deve ser entre 1 e 8 (classes PCASP)"))
            
    def calcular_nivel_conta(self):
        """Calcular nível hierárquico da conta"""
        if self.codigo_conta:
            # Contar pontos para determinar nível
            pontos = self.codigo_conta.count('.')
            
            # PCASP tem estrutura específica de níveis
            if pontos == 7:  # Formato completo X.X.X.X.X.XX.XX.XX
                # Verificar se é conta de último nível (analítica)
                partes = self.codigo_conta.split('.')
                if any(parte != '00' for parte in partes[5:8]):
                    self.nivel_conta = 8
                elif partes[4] != '0':
                    self.nivel_conta = 5
                elif partes[3] != '0':
                    self.nivel_conta = 4
                elif partes[2] != '0':
                    self.nivel_conta = 3
                elif partes[1] != '0':
                    self.nivel_conta = 2
                else:
                    self.nivel_conta = 1
            else:
                frappe.throw(_("Código PCASP deve ter formato completo de 8 níveis"))
                
    def validar_hierarquia(self):
        """Validar hierarquia de contas"""
        if self.conta_pai:
            conta_pai = frappe.get_doc("PlanoContas", self.conta_pai)
            
            # Verificar se a conta pai tem nível inferior
            if conta_pai.nivel_conta >= self.nivel_conta:
                frappe.throw(_("Conta pai deve ter nível hierárquico inferior"))
                
            # Verificar consistência de códigos
            codigo_pai = conta_pai.codigo_conta
            if not self.codigo_conta.startswith(codigo_pai[0]):
                frappe.throw(_("Conta deve pertencer à mesma classe da conta pai"))
                
    def validar_conta_analitica(self):
        """Validar configuração de conta analítica"""
        if self.conta_analitica:
            # Verificar se é conta de último nível
            if self.nivel_conta < 8:
                frappe.throw(_("Apenas contas de 8º nível podem ser analíticas"))
                
            # Verificar se não possui contas filhas
            contas_filhas = frappe.get_all("PlanoContas", 
                                         filters={"conta_pai": self.name})
            if contas_filhas:
                frappe.throw(_("Conta analítica não pode ter contas subordinadas"))
                
    def validar_vigencia(self):
        """Validar período de vigência"""
        if self.data_fim_vigencia and self.data_inicio_vigencia:
            if self.data_fim_vigencia < self.data_inicio_vigencia:
                frappe.throw(_("Data de fim de vigência deve ser posterior ao início"))
                
    def validar_natureza_conta(self):
        """Validar natureza da conta conforme PCASP"""
        if self.tipo_conta and self.natureza_conta:
            # Definir naturezas corretas por tipo
            naturezas_corretas = {
                "Ativo": "Devedora",
                "Passivo": "Credora", 
                "Patrimônio Líquido": "Credora",
                "Receita": "Credora",
                "Despesa": "Devedora",
                "Controles Devedores": "Devedora",
                "Controles Credores": "Credora"
            }
            
            natureza_esperada = naturezas_corretas.get(self.tipo_conta)
            if natureza_esperada and self.natureza_conta != natureza_esperada:
                frappe.throw(_("Natureza da conta '{0}' deve ser '{1}' para tipo '{2}'")
                           .format(self.natureza_conta, natureza_esperada, self.tipo_conta))
                
    def processar_classificacao_pcasp(self):
        """Processar classificação automática PCASP"""
        if self.codigo_conta:
            partes = self.codigo_conta.split('.')
            
            # Definir classe automaticamente
            classe_map = {
                '1': '1 - Ativo',
                '2': '2 - Passivo', 
                '3': '3 - Patrimônio Líquido',
                '4': '4 - Variações Patrimoniais Diminutivas',
                '5': '5 - Variações Patrimoniais Aumentativas',
                '6': '6 - Controles Devedores',
                '7': '7 - Controles Credores',
                '8': '8 - Controles Específicos'
            }
            
            self.classe_conta = classe_map.get(partes[0], '')
            
            # Definir tipo de conta baseado na classe
            tipo_map = {
                '1': 'Ativo',
                '2': 'Passivo',
                '3': 'Patrimônio Líquido', 
                '4': 'Despesa',
                '5': 'Receita',
                '6': 'Controles Devedores',
                '7': 'Controles Credores'
            }
            
            if not self.tipo_conta:
                self.tipo_conta = tipo_map.get(partes[0], '')
                
            # Definir natureza automaticamente
            if not self.natureza_conta:
                if partes[0] in ['1', '4', '6']:
                    self.natureza_conta = 'Devedora'
                elif partes[0] in ['2', '3', '5', '7']:
                    self.natureza_conta = 'Credora'
                    
            # Processar demais níveis
            if len(partes) >= 2:
                self.grupo_conta = partes[1]
            if len(partes) >= 3:
                self.subgrupo_conta = partes[2]
            if len(partes) >= 4:
                self.elemento_conta = partes[3]
            if len(partes) >= 5:
                self.subelemento_conta = partes[4]
            if len(partes) >= 6:
                self.item_conta = partes[5]
            if len(partes) >= 8:
                self.subitem_conta = f"{partes[6]}.{partes[7]}"
                
    def definir_funcao_conta(self):
        """Definir função da conta no sistema"""
        if not self.funcao_conta and self.codigo_conta:
            primeiro_digito = self.codigo_conta[0]
            
            if primeiro_digito in ['1', '2', '3']:
                self.funcao_conta = 'Patrimonial'
            elif primeiro_digito in ['4', '5']:
                self.funcao_conta = 'Orçamentária'
            elif primeiro_digito in ['6', '7']:
                self.funcao_conta = 'Controle'
            elif primeiro_digito == '8':
                self.funcao_conta = 'Compensação'
                
    @frappe.whitelist()
    def get_contas_filhas(self):
        """Retornar contas subordinadas"""
        return frappe.get_all("PlanoContas",
                            filters={"conta_pai": self.name, "status_conta": "Ativa"},
                            fields=["name", "codigo_conta", "descricao_conta", "conta_analitica"],
                            order_by="codigo_conta")
                            
    @frappe.whitelist()
    def get_saldo_atual(self, data_consulta=None):
        """Obter saldo atual da conta"""
        if not data_consulta:
            data_consulta = frappe.utils.today()
            
        # Consultar lançamentos contábeis
        lancamentos = frappe.db.sql("""
            SELECT 
                SUM(CASE WHEN conta_debito = %s THEN valor_debito ELSE 0 END) as total_debito,
                SUM(CASE WHEN conta_credito = %s THEN valor_credito ELSE 0 END) as total_credito
            FROM `tabLancamentoContabil`
            WHERE (conta_debito = %s OR conta_credito = %s)
            AND data_lancamento <= %s
            AND docstatus = 1
        """, (self.name, self.name, self.name, self.name, data_consulta), as_dict=True)
        
        if lancamentos:
            total_debito = lancamentos[0].total_debito or 0
            total_credito = lancamentos[0].total_credito or 0
            
            # Calcular saldo conforme natureza da conta
            if self.natureza_conta == "Devedora":
                saldo = total_debito - total_credito
            else:
                saldo = total_credito - total_debito
                
            return {
                "saldo": saldo,
                "total_debito": total_debito,
                "total_credito": total_credito,
                "natureza": self.natureza_conta
            }
        
        return {
            "saldo": 0,
            "total_debito": 0, 
            "total_credito": 0,
            "natureza": self.natureza_conta
        }
        
    def before_cancel(self):
        """Validações antes de cancelar conta"""
        # Verificar se há lançamentos na conta
        lancamentos = frappe.get_all("LancamentoContabil",
                                   filters=[
                                       ["conta_debito", "=", self.name],
                                       ["docstatus", "=", 1]
                                   ])
        
        if not lancamentos:
            lancamentos = frappe.get_all("LancamentoContabil", 
                                       filters=[
                                           ["conta_credito", "=", self.name],
                                           ["docstatus", "=", 1]
                                       ])
                                       
        if lancamentos:
            frappe.throw(_("Não é possível inativar conta com lançamentos contábeis"))
            
    @staticmethod
    def criar_plano_contas_padrao(exercicio_financeiro):
        """Criar plano de contas padrão PCASP"""
        contas_padrao = [
            # Ativo
            {"codigo": "1.1.1.1.1.01.01.01", "descricao": "Caixa", "analitica": True},
            {"codigo": "1.1.1.2.1.01.01.01", "descricao": "Bancos Conta Movimento", "analitica": True},
            {"codigo": "1.1.2.1.1.01.01.01", "descricao": "Créditos Tributários a Receber", "analitica": True},
            
            # Passivo  
            {"codigo": "2.1.1.1.1.01.01.01", "descricao": "Fornecedores Nacionais", "analitica": True},
            {"codigo": "2.1.3.1.1.01.01.01", "descricao": "Obrigações Trabalhistas", "analitica": True},
            
            # Patrimônio Líquido
            {"codigo": "3.1.1.1.1.01.01.01", "descricao": "Patrimônio Social", "analitica": True},
            
            # Variações Patrimoniais Diminutivas
            {"codigo": "4.1.1.1.1.01.01.01", "descricao": "Pessoal e Encargos", "analitica": True},
            {"codigo": "4.4.9.0.1.01.01.01", "descricao": "Material de Consumo", "analitica": True},
            
            # Variações Patrimoniais Aumentativas  
            {"codigo": "5.1.1.1.1.01.01.01", "descricao": "Impostos", "analitica": True},
            {"codigo": "5.1.1.2.1.01.01.01", "descricao": "Taxas", "analitica": True},
            
            # Controles
            {"codigo": "6.2.1.1.1.01.01.01", "descricao": "Execução Orçamentária da Receita", "analitica": True},
            {"codigo": "7.2.1.1.1.01.01.01", "descricao": "Execução Orçamentária da Despesa", "analitica": True}
        ]
        
        for conta_data in contas_padrao:
            if not frappe.db.exists("PlanoContas", conta_data["codigo"]):
                conta = frappe.new_doc("PlanoContas")
                conta.codigo_conta = conta_data["codigo"]
                conta.descricao_conta = conta_data["descricao"] 
                conta.conta_analitica = conta_data.get("analitica", False)
                conta.exercicio_financeiro = exercicio_financeiro
                conta.data_inicio_vigencia = frappe.utils.today()
                conta.status_conta = "Ativa"
                conta.escrituracao_pcasp = "S"
                conta.save()
                
        frappe.msgprint(_("Plano de contas padrão PCASP criado com sucesso"))