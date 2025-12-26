# -*- coding: utf-8 -*-
"""
Módulo de Gestão de ISS (Imposto Sobre Serviços)
Sistema completo para gestão de ISS municipal
"""

import frappe
from frappe import _
from datetime import datetime, date, timedelta
import json
import calendar

class ISSManager:
    """Gerenciador completo de ISS"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.settings = self.get_iss_settings()
    
    def get_iss_settings(self):
        """Obter configurações de ISS do município"""
        try:
            settings = frappe.get_single("ISS Settings")
            return settings
        except:
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Configurações padrão de ISS"""
        return {
            "aliquota_minima": 2.0,
            "aliquota_maxima": 5.0,
            "valor_minimo_mensal": 25.0,
            "deducao_material": True,
            "prazo_declaracao": 10,  # Dia do mês para entrega
            "multa_atraso_declaracao": 50.0,
            "juros_atraso": 1.0,
            "multa_atraso_pagamento": 2.0,
            "desconto_pontualidade": 5.0
        }
    
    def calculate_iss(self, prestador_id, competencia_mes, competencia_ano, servicos):
        """
        Calcular ISS para um prestador em determinada competência
        """
        # Obter dados do prestador
        prestador = frappe.get_doc("ISS Prestador", prestador_id)
        
        total_iss = 0
        detalhes_servicos = []
        
        for servico in servicos:
            calculo_servico = self.calculate_iss_servico(
                prestador, 
                servico,
                competencia_mes,
                competencia_ano
            )
            
            total_iss += calculo_servico["iss_devido"]
            detalhes_servicos.append(calculo_servico)
        
        # Aplicar valor mínimo
        valor_minimo = self.settings.get("valor_minimo_mensal", 25.0)
        total_iss = max(total_iss, valor_minimo)
        
        return {
            "prestador_id": prestador_id,
            "competencia": f"{competencia_mes:02d}/{competencia_ano}",
            "total_servicos": sum(s["valor_servico"] for s in detalhes_servicos),
            "total_deducoes": sum(s["deducoes"] for s in detalhes_servicos),
            "base_calculo": sum(s["base_calculo"] for s in detalhes_servicos),
            "total_iss": total_iss,
            "detalhes_servicos": detalhes_servicos
        }
    
    def calculate_iss_servico(self, prestador, servico, mes, ano):
        """Calcular ISS para um serviço específico"""
        # Obter dados da atividade
        atividade = frappe.get_doc("ISS Atividade", servico["codigo_atividade"])
        
        valor_servico = servico["valor_servico"]
        
        # Calcular deduções permitidas
        deducoes = self.calculate_deducoes(servico, atividade)
        
        # Base de cálculo
        base_calculo = valor_servico - deducoes
        
        # Aplicar alíquota
        aliquota = self.get_aliquota_atividade(atividade, prestador)
        
        # Calcular ISS
        iss_devido = base_calculo * (aliquota / 100)
        
        return {
            "codigo_atividade": servico["codigo_atividade"],
            "descricao_atividade": atividade.descricao,
            "valor_servico": valor_servico,
            "deducoes": deducoes,
            "base_calculo": base_calculo,
            "aliquota": aliquota,
            "iss_devido": iss_devido
        }
    
    def calculate_deducoes(self, servico, atividade):
        """Calcular deduções permitidas"""
        deducoes = 0
        
        # Dedução de materiais (se permitido para a atividade)
        if atividade.permite_deducao_material and self.settings.get("deducao_material"):
            deducoes += servico.get("valor_materiais", 0)
        
        # Dedução de subcontratação
        if atividade.permite_deducao_subcontratacao:
            deducoes += servico.get("valor_subcontratacao", 0)
        
        # Outras deduções específicas
        deducoes += servico.get("outras_deducoes", 0)
        
        # Limitar deduções ao valor do serviço
        return min(deducoes, servico["valor_servico"])
    
    def get_aliquota_atividade(self, atividade, prestador):
        """Obter alíquota aplicável à atividade"""
        # Verificar se prestador tem alíquota específica
        if prestador.regime_especial:
            return prestador.aliquota_especial or atividade.aliquota
        
        # Verificar microempresa/EPP
        if prestador.categoria == "Microempresa":
            return min(atividade.aliquota, 2.0)  # Alíquota reduzida para ME
        
        return atividade.aliquota
    
    def create_declaracao(self, prestador_id, competencia_mes, competencia_ano, servicos):
        """Criar declaração de ISS"""
        try:
            # Calcular ISS
            calculo = self.calculate_iss(prestador_id, competencia_mes, competencia_ano, servicos)
            
            # Verificar se já existe declaração para a competência
            exists = frappe.db.exists("ISS Declaracao", {
                "prestador": prestador_id,
                "competencia_mes": competencia_mes,
                "competencia_ano": competencia_ano
            })
            
            if exists:
                frappe.throw(_("Já existe declaração para esta competência"))
            
            # Criar documento de declaração
            declaracao = frappe.new_doc("ISS Declaracao")
            declaracao.update({
                "prestador": prestador_id,
                "competencia_mes": competencia_mes,
                "competencia_ano": competencia_ano,
                "data_declaracao": frappe.utils.nowdate(),
                "valor_total_servicos": calculo["total_servicos"],
                "valor_total_deducoes": calculo["total_deducoes"],
                "base_calculo_total": calculo["base_calculo"],
                "valor_iss_total": calculo["total_iss"],
                "situacao": "Declarada"
            })
            
            # Adicionar detalhes dos serviços
            for detalhe in calculo["detalhes_servicos"]:
                declaracao.append("servicos", {
                    "codigo_atividade": detalhe["codigo_atividade"],
                    "descricao_atividade": detalhe["descricao_atividade"],
                    "valor_servico": detalhe["valor_servico"],
                    "valor_deducoes": detalhe["deducoes"],
                    "base_calculo": detalhe["base_calculo"],
                    "aliquota": detalhe["aliquota"],
                    "valor_iss": detalhe["iss_devido"]
                })
            
            declaracao.insert()
            
            # Gerar guia de pagamento
            guia = self.generate_guia_pagamento(declaracao)
            
            return {
                "success": True,
                "declaracao_id": declaracao.name,
                "guia_id": guia.name,
                "valor_iss": calculo["total_iss"]
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "ISS Declaration Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_guia_pagamento(self, declaracao):
        """Gerar guia de pagamento de ISS"""
        # Calcular data de vencimento
        vencimento = self.calculate_vencimento(
            declaracao.competencia_mes,
            declaracao.competencia_ano
        )
        
        # Criar guia
        guia = frappe.new_doc("ISS Guia Pagamento")
        guia.update({
            "declaracao": declaracao.name,
            "prestador": declaracao.prestador,
            "competencia_mes": declaracao.competencia_mes,
            "competencia_ano": declaracao.competencia_ano,
            "valor_principal": declaracao.valor_iss_total,
            "valor_desconto": 0,
            "valor_multa": 0,
            "valor_juros": 0,
            "valor_total": declaracao.valor_iss_total,
            "data_vencimento": vencimento,
            "situacao": "Pendente"
        })
        
        # Calcular desconto por pontualidade
        if self.is_pagamento_em_dia(vencimento):
            desconto = declaracao.valor_iss_total * (self.settings.get("desconto_pontualidade", 5) / 100)
            guia.valor_desconto = desconto
            guia.valor_total = declaracao.valor_iss_total - desconto
        
        guia.insert()
        return guia
    
    def calculate_vencimento(self, mes, ano):
        """Calcular data de vencimento baseada na competência"""
        # Vencimento no mês seguinte
        if mes == 12:
            mes_vencimento = 1
            ano_vencimento = ano + 1
        else:
            mes_vencimento = mes + 1
            ano_vencimento = ano
        
        dia_vencimento = self.settings.get("prazo_declaracao", 10)
        
        # Ajustar se cair em fim de semana
        vencimento = date(ano_vencimento, mes_vencimento, dia_vencimento)
        
        # Se cair em sábado ou domingo, mover para segunda
        if vencimento.weekday() == 5:  # Sábado
            vencimento += timedelta(days=2)
        elif vencimento.weekday() == 6:  # Domingo
            vencimento += timedelta(days=1)
        
        return vencimento
    
    def is_pagamento_em_dia(self, data_vencimento):
        """Verificar se pagamento será feito em dia para desconto"""
        return date.today() <= data_vencimento
    
    def process_pagamento(self, guia_id, data_pagamento=None):
        """Processar pagamento de ISS"""
        try:
            guia = frappe.get_doc("ISS Guia Pagamento", guia_id)
            data_pagamento = data_pagamento or date.today()
            
            if isinstance(data_pagamento, str):
                data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date()
            
            # Calcular multa e juros se em atraso
            if data_pagamento > guia.data_vencimento:
                multa_juros = self.calculate_multa_juros(
                    guia.valor_principal,
                    guia.data_vencimento,
                    data_pagamento
                )
                
                guia.valor_multa = multa_juros["multa"]
                guia.valor_juros = multa_juros["juros"]
                guia.valor_total = guia.valor_principal + guia.valor_multa + guia.valor_juros
            
            # Criar registro de pagamento
            pagamento = frappe.new_doc("ISS Pagamento")
            pagamento.update({
                "guia_pagamento": guia_id,
                "prestador": guia.prestador,
                "competencia_mes": guia.competencia_mes,
                "competencia_ano": guia.competencia_ano,
                "valor_principal": guia.valor_principal,
                "valor_desconto": guia.valor_desconto,
                "valor_multa": guia.valor_multa,
                "valor_juros": guia.valor_juros,
                "valor_pago": guia.valor_total,
                "data_pagamento": data_pagamento,
                "forma_pagamento": "Boleto"  # Default
            })
            
            pagamento.insert()
            
            # Atualizar status da guia
            guia.situacao = "Pago"
            guia.data_pagamento = data_pagamento
            guia.save()
            
            # Atualizar status da declaração
            declaracao = frappe.get_doc("ISS Declaracao", guia.declaracao)
            declaracao.situacao = "Pago"
            declaracao.save()
            
            return {
                "success": True,
                "pagamento_id": pagamento.name,
                "valor_pago": guia.valor_total
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "ISS Payment Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_multa_juros(self, valor_principal, data_vencimento, data_pagamento):
        """Calcular multa e juros por atraso"""
        dias_atraso = (data_pagamento - data_vencimento).days
        
        # Multa fixa
        multa_percentual = self.settings.get("multa_atraso_pagamento", 2.0)
        multa = valor_principal * (multa_percentual / 100)
        
        # Juros mensais
        meses_atraso = dias_atraso / 30
        juros_percentual = self.settings.get("juros_atraso", 1.0)
        juros = valor_principal * (juros_percentual / 100) * meses_atraso
        
        return {
            "multa": multa,
            "juros": juros,
            "dias_atraso": dias_atraso
        }
    
    def generate_nfse(self, declaracao_id, servico_id, tomador_data):
        """Gerar Nota Fiscal de Serviços Eletrônica"""
        try:
            declaracao = frappe.get_doc("ISS Declaracao", declaracao_id)
            servico = next(s for s in declaracao.servicos if s.name == servico_id)
            
            # Gerar número da NFSe
            numero_nfse = self.get_next_nfse_number()
            
            # Criar NFSe
            nfse = frappe.new_doc("NFSe")
            nfse.update({
                "numero": numero_nfse,
                "prestador": declaracao.prestador,
                "tomador_nome": tomador_data["nome"],
                "tomador_cpf_cnpj": tomador_data["cpf_cnpj"],
                "tomador_endereco": tomador_data.get("endereco", ""),
                "codigo_servico": servico.codigo_atividade,
                "descricao_servico": servico.descricao_atividade,
                "valor_servico": servico.valor_servico,
                "valor_deducoes": servico.valor_deducoes,
                "base_calculo": servico.base_calculo,
                "aliquota": servico.aliquota,
                "valor_iss": servico.valor_iss,
                "competencia_mes": declaracao.competencia_mes,
                "competencia_ano": declaracao.competencia_ano,
                "data_emissao": frappe.utils.nowdate(),
                "situacao": "Emitida"
            })
            
            nfse.insert()
            nfse.submit()
            
            return {
                "success": True,
                "nfse_id": nfse.name,
                "numero_nfse": numero_nfse
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "NFSe Generation Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_next_nfse_number(self):
        """Obter próximo número de NFSe"""
        last_number = frappe.db.sql("""
            SELECT MAX(CAST(numero AS UNSIGNED)) 
            FROM `tabNFSe` 
            WHERE YEAR(data_emissao) = %s
        """, [self.current_year])[0][0] or 0
        
        return str(last_number + 1).zfill(8)  # 8 dígitos
    
    def get_iss_statistics(self, ano=None, mes=None):
        """Obter estatísticas de ISS"""
        ano = ano or self.current_year
        filters = {"competencia_ano": ano}
        
        if mes:
            filters["competencia_mes"] = mes
        
        try:
            stats = {
                "prestadores_ativos": frappe.db.count("ISS Prestador", {"ativo": 1}),
                "declaracoes_periodo": frappe.db.count("ISS Declaracao", filters),
                "valor_declarado": frappe.db.sql("""
                    SELECT SUM(valor_iss_total) 
                    FROM `tabISS Declaracao` 
                    WHERE competencia_ano = %s
                    {} 
                """.format("AND competencia_mes = %(mes)s" if mes else ""), 
                {"ano": ano, "mes": mes})[0][0] or 0,
                "valor_arrecadado": frappe.db.sql("""
                    SELECT SUM(valor_pago) 
                    FROM `tabISS Pagamento` 
                    WHERE competencia_ano = %s
                    {}
                """.format("AND competencia_mes = %(mes)s" if mes else ""),
                {"ano": ano, "mes": mes})[0][0] or 0,
                "nfse_emitidas": frappe.db.count("NFSe", {
                    "competencia_ano": ano,
                    **({"competencia_mes": mes} if mes else {})
                })
            }
            
            # Calcular inadimplência
            stats["declaracoes_pagas"] = frappe.db.count("ISS Declaracao", {
                **filters,
                "situacao": "Pago"
            })
            
            if stats["declaracoes_periodo"] > 0:
                stats["percentual_adimplencia"] = round(
                    (stats["declaracoes_pagas"] / stats["declaracoes_periodo"]) * 100, 2
                )
            else:
                stats["percentual_adimplencia"] = 0
            
            if stats["valor_declarado"] > 0:
                stats["percentual_arrecadacao"] = round(
                    (stats["valor_arrecadado"] / stats["valor_declarado"]) * 100, 2
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

# Instância global do gerenciador
iss_manager = ISSManager()

# APIs públicas
@frappe.whitelist()
def calculate_iss_preview(prestador_id, competencia_mes, competencia_ano, servicos):
    """API para prévia de cálculo de ISS"""
    try:
        if isinstance(servicos, str):
            servicos = json.loads(servicos)
        
        result = iss_manager.calculate_iss(
            prestador_id, 
            int(competencia_mes), 
            int(competencia_ano), 
            servicos
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
def create_iss_declaracao(prestador_id, competencia_mes, competencia_ano, servicos):
    """API para criar declaração de ISS"""
    try:
        if isinstance(servicos, str):
            servicos = json.loads(servicos)
        
        result = iss_manager.create_declaracao(
            prestador_id,
            int(competencia_mes),
            int(competencia_ano),
            servicos
        )
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def process_iss_payment(guia_id, data_pagamento=None):
    """API para processar pagamento de ISS"""
    return iss_manager.process_pagamento(guia_id, data_pagamento)

@frappe.whitelist()
def generate_nfse_api(declaracao_id, servico_id, tomador_data):
    """API para gerar NFSe"""
    if isinstance(tomador_data, str):
        tomador_data = json.loads(tomador_data)
    
    return iss_manager.generate_nfse(declaracao_id, servico_id, tomador_data)

@frappe.whitelist()
def get_iss_stats(ano=None, mes=None):
    """API para obter estatísticas de ISS"""
    return iss_manager.get_iss_statistics(
        int(ano) if ano else None,
        int(mes) if mes else None
    )