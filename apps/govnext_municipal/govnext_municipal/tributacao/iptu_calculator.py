# -*- coding: utf-8 -*-
"""
Módulo de Cálculo de IPTU Avançado
Sistema completo para cálculo de IPTU com todas as regras municipais
"""

import frappe
from frappe import _
from datetime import datetime, date
import json

class IPTUCalculator:
    """Calculadora avançada de IPTU"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.settings = self.get_iptu_settings()
    
    def get_iptu_settings(self):
        """Obter configurações de IPTU do município"""
        try:
            settings = frappe.get_single("IPTU Settings")
            return settings
        except:
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Configurações padrão de IPTU"""
        return {
            "aliquota_residencial": 0.6,
            "aliquota_comercial": 1.0,
            "aliquota_industrial": 1.2,
            "aliquota_territorial": 1.5,
            "valor_minimo": 50.0,
            "desconto_pontualidade": 10.0,
            "desconto_idoso": 50.0,
            "desconto_deficiente": 30.0,
            "parcelas_permitidas": 10,
            "juros_atraso": 1.0,
            "multa_atraso": 2.0
        }
    
    def calculate_iptu(self, cadastro_id, ano=None):
        """
        Calcular IPTU para um imóvel específico
        """
        ano = ano or self.current_year
        
        # Obter dados do cadastro
        cadastro = frappe.get_doc("IPTU Cadastro", cadastro_id)
        
        # Calcular valor venal atualizado
        valor_venal = self.calculate_valor_venal(cadastro, ano)
        
        # Determinar alíquota baseada no uso
        aliquota = self.get_aliquota_by_usage(cadastro.uso_imovel)
        
        # Calcular IPTU bruto
        iptu_bruto = valor_venal * (aliquota / 100)
        
        # Aplicar valor mínimo
        iptu_bruto = max(iptu_bruto, self.settings.get("valor_minimo", 50.0))
        
        # Calcular descontos aplicáveis
        descontos = self.calculate_discounts(cadastro, iptu_bruto)
        
        # Valor líquido
        iptu_liquido = iptu_bruto - descontos["total"]
        
        # Gerar parcelas
        parcelas = self.generate_parcelas(iptu_liquido, ano)
        
        return {
            "valor_venal": valor_venal,
            "aliquota": aliquota,
            "iptu_bruto": iptu_bruto,
            "descontos": descontos,
            "iptu_liquido": iptu_liquido,
            "parcelas": parcelas
        }
    
    def calculate_valor_venal(self, cadastro, ano):
        """Calcular valor venal atualizado para o ano"""
        valor_base = cadastro.valor_venal_total or 0
        
        # Obter fator de atualização do ano
        fator_atualizacao = self.get_fator_atualizacao(ano)
        
        # Aplicar fator de atualização
        valor_atualizado = valor_base * fator_atualizacao
        
        # Considerar benfeitorias e melhoramentos
        valor_benfeitorias = self.calculate_valor_benfeitorias(cadastro)
        
        return valor_atualizado + valor_benfeitorias
    
    def get_fator_atualizacao(self, ano):
        """Obter fator de atualização monetária do ano"""
        try:
            fator = frappe.db.get_value(
                "IPTU Fator Atualizacao",
                {"ano": ano},
                "fator"
            )
            return fator or 1.0
        except:
            return 1.0
    
    def calculate_valor_benfeitorias(self, cadastro):
        """Calcular valor de benfeitorias e melhoramentos"""
        valor_benfeitorias = 0
        
        # Verificar benfeitorias cadastradas
        benfeitorias = frappe.get_all(
            "IPTU Benfeitoria",
            filters={"parent": cadastro.name},
            fields=["tipo", "valor", "ano_construcao"]
        )
        
        for benfeitoria in benfeitorias:
            # Aplicar depreciação baseada na idade
            idade = self.current_year - (benfeitoria.get("ano_construcao") or self.current_year)
            fator_depreciacao = max(0.5, 1 - (idade * 0.02))  # 2% ao ano, mínimo 50%
            
            valor_depreciado = benfeitoria.get("valor", 0) * fator_depreciacao
            valor_benfeitorias += valor_depreciado
        
        return valor_benfeitorias
    
    def get_aliquota_by_usage(self, uso_imovel):
        """Determinar alíquota baseada no uso do imóvel"""
        aliquotas = {
            "Residencial": self.settings.get("aliquota_residencial", 0.6),
            "Comercial": self.settings.get("aliquota_comercial", 1.0),
            "Industrial": self.settings.get("aliquota_industrial", 1.2),
            "Territorial": self.settings.get("aliquota_territorial", 1.5),
            "Misto": self.settings.get("aliquota_comercial", 1.0),
            "Público": 0.0,
            "Religioso": 0.0
        }
        
        return aliquotas.get(uso_imovel, self.settings.get("aliquota_residencial", 0.6))
    
    def calculate_discounts(self, cadastro, iptu_bruto):
        """Calcular todos os descontos aplicáveis"""
        descontos = {
            "pontualidade": 0,
            "idoso": 0,
            "deficiente": 0,
            "outros": 0,
            "total": 0
        }
        
        # Desconto por pontualidade (pagamento à vista)
        if self.settings.get("desconto_pontualidade", 0) > 0:
            descontos["pontualidade"] = iptu_bruto * (self.settings["desconto_pontualidade"] / 100)
        
        # Desconto para idosos
        if self.check_desconto_idoso(cadastro):
            descontos["idoso"] = iptu_bruto * (self.settings.get("desconto_idoso", 0) / 100)
        
        # Desconto para deficientes
        if self.check_desconto_deficiente(cadastro):
            descontos["deficiente"] = iptu_bruto * (self.settings.get("desconto_deficiente", 0) / 100)
        
        # Verificar outros descontos específicos
        descontos["outros"] = self.calculate_outros_descontos(cadastro, iptu_bruto)
        
        # Calcular total (aplicar apenas o maior desconto, não cumulativo)
        descontos["total"] = max(
            descontos["pontualidade"],
            descontos["idoso"], 
            descontos["deficiente"],
            descontos["outros"]
        )
        
        return descontos
    
    def check_desconto_idoso(self, cadastro):
        """Verificar se proprietário tem direito ao desconto de idoso"""
        if not cadastro.data_nascimento_proprietario:
            return False
        
        idade = self.calculate_age(cadastro.data_nascimento_proprietario)
        return idade >= 65  # 65 anos ou mais
    
    def check_desconto_deficiente(self, cadastro):
        """Verificar se proprietário tem direito ao desconto de deficiente"""
        return getattr(cadastro, 'proprietario_deficiente', False)
    
    def calculate_age(self, birth_date):
        """Calcular idade baseada na data de nascimento"""
        today = date.today()
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        
        return age
    
    def calculate_outros_descontos(self, cadastro, iptu_bruto):
        """Calcular outros descontos específicos do município"""
        desconto_total = 0
        
        # Desconto para imóveis em área de preservação
        if getattr(cadastro, 'area_preservacao', False):
            desconto_total += iptu_bruto * 0.2  # 20% de desconto
        
        # Desconto para imóveis com certificação ambiental
        if getattr(cadastro, 'certificacao_ambiental', False):
            desconto_total += iptu_bruto * 0.1  # 10% de desconto
        
        return desconto_total
    
    def generate_parcelas(self, valor_iptu, ano):
        """Gerar parcelas de pagamento"""
        parcelas_permitidas = self.settings.get("parcelas_permitidas", 10)
        parcelas = []
        
        # Parcela única (à vista com desconto)
        desconto_vista = self.settings.get("desconto_pontualidade", 10)
        valor_vista = valor_iptu * (1 - desconto_vista / 100)
        
        parcelas.append({
            "numero": 0,
            "tipo": "À Vista",
            "valor": valor_vista,
            "vencimento": f"{ano}-03-31",
            "desconto": desconto_vista
        })
        
        # Parcelas mensais
        valor_parcela = valor_iptu / parcelas_permitidas
        
        for i in range(1, parcelas_permitidas + 1):
            mes = 2 + i  # Começar em março
            if mes > 12:
                mes = 12
            
            vencimento = f"{ano}-{mes:02d}-10"
            
            parcelas.append({
                "numero": i,
                "tipo": "Parcelado",
                "valor": valor_parcela,
                "vencimento": vencimento,
                "desconto": 0
            })
        
        return parcelas
    
    def calculate_multa_juros(self, valor_parcela, data_vencimento, data_pagamento=None):
        """Calcular multa e juros por atraso"""
        data_pagamento = data_pagamento or date.today()
        
        if isinstance(data_vencimento, str):
            data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
        
        if data_pagamento <= data_vencimento:
            return {"multa": 0, "juros": 0, "total": valor_parcela}
        
        dias_atraso = (data_pagamento - data_vencimento).days
        
        # Calcular multa (fixa)
        multa_percentual = self.settings.get("multa_atraso", 2.0)
        multa = valor_parcela * (multa_percentual / 100)
        
        # Calcular juros (por mês ou fração)
        meses_atraso = (dias_atraso / 30) 
        juros_percentual = self.settings.get("juros_atraso", 1.0)
        juros = valor_parcela * (juros_percentual / 100) * meses_atraso
        
        total = valor_parcela + multa + juros
        
        return {
            "multa": multa,
            "juros": juros,
            "dias_atraso": dias_atraso,
            "total": total
        }

# Instância global da calculadora
iptu_calculator = IPTUCalculator()

@frappe.whitelist()
def calculate_iptu_for_property(cadastro_id, ano=None):
    """API para calcular IPTU de um imóvel"""
    try:
        result = iptu_calculator.calculate_iptu(cadastro_id, ano)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "IPTU Calculation Error")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def simulate_iptu_payment(cadastro_id, parcela_numero, data_pagamento=None):
    """Simular pagamento de parcela com cálculo de multa/juros"""
    try:
        # Obter dados da parcela
        lancamento = frappe.get_doc("IPTU Lancamento", {
            "inscricao_cadastral": cadastro_id,
            "ano": datetime.now().year
        })
        
        # Calcular multa e juros
        valor_parcela = lancamento.valor_iptu / lancamento.numero_parcelas
        data_vencimento = f"{lancamento.ano}-{3 + int(parcela_numero):02d}-10"
        
        result = iptu_calculator.calculate_multa_juros(
            valor_parcela, 
            data_vencimento, 
            data_pagamento
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def generate_iptu_carne(cadastro_id, ano=None):
    """Gerar carnê de IPTU para um imóvel"""
    try:
        ano = ano or datetime.now().year
        
        # Calcular IPTU
        calculo = iptu_calculator.calculate_iptu(cadastro_id, ano)
        
        # Obter dados do proprietário
        cadastro = frappe.get_doc("IPTU Cadastro", cadastro_id)
        
        # Criar documento de carnê
        carne = frappe.new_doc("IPTU Carne")
        carne.update({
            "inscricao_cadastral": cadastro_id,
            "ano_referencia": ano,
            "proprietario": cadastro.proprietario,
            "endereco_imovel": cadastro.endereco_completo,
            "valor_venal": calculo["valor_venal"],
            "valor_iptu": calculo["iptu_liquido"],
            "data_emissao": frappe.utils.nowdate()
        })
        
        # Adicionar parcelas
        for parcela in calculo["parcelas"]:
            carne.append("parcelas", {
                "numero_parcela": parcela["numero"],
                "tipo_pagamento": parcela["tipo"],
                "valor": parcela["valor"],
                "data_vencimento": parcela["vencimento"],
                "desconto": parcela.get("desconto", 0)
            })
        
        carne.insert()
        carne.submit()
        
        return {
            "success": True,
            "carne_id": carne.name,
            "message": f"Carnê gerado com sucesso: {carne.name}"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "IPTU Carnê Generation Error")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_iptu_statistics(ano=None):
    """Obter estatísticas de IPTU do município"""
    ano = ano or datetime.now().year
    
    try:
        stats = {
            "total_imoveis": frappe.db.count("IPTU Cadastro"),
            "carnes_emitidos": frappe.db.count("IPTU Carne", {"ano_referencia": ano}),
            "valor_total_lancado": frappe.db.sql("""
                SELECT SUM(valor_iptu) 
                FROM `tabIPTU Carne` 
                WHERE ano_referencia = %s
            """, [ano])[0][0] or 0,
            "valor_arrecadado": frappe.db.sql("""
                SELECT SUM(valor_pago) 
                FROM `tabIPTU Pagamento` 
                WHERE YEAR(data_pagamento) = %s
            """, [ano])[0][0] or 0,
            "inadimplencia_count": frappe.db.sql("""
                SELECT COUNT(*) 
                FROM `tabIPTU Carne` c
                WHERE c.ano_referencia = %s
                AND NOT EXISTS (
                    SELECT 1 FROM `tabIPTU Pagamento` p 
                    WHERE p.inscricao_cadastral = c.inscricao_cadastral 
                    AND YEAR(p.data_pagamento) = %s
                )
            """, [ano, ano])[0][0] or 0
        }
        
        # Calcular percentuais
        if stats["total_imoveis"] > 0:
            stats["percentual_emissao"] = round(
                (stats["carnes_emitidos"] / stats["total_imoveis"]) * 100, 2
            )
            stats["percentual_inadimplencia"] = round(
                (stats["inadimplencia_count"] / stats["total_imoveis"]) * 100, 2
            )
        else:
            stats["percentual_emissao"] = 0
            stats["percentual_inadimplencia"] = 0
        
        if stats["valor_total_lancado"] > 0:
            stats["percentual_arrecadacao"] = round(
                (stats["valor_arrecadado"] / stats["valor_total_lancado"]) * 100, 2
            )
        else:
            stats["percentual_arrecadacao"] = 0
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }