# -*- coding: utf-8 -*-
"""
Módulo de Gestão de Alvarás e Licenciamento
Sistema completo para processos de licenciamento municipal
"""

import frappe
from frappe import _
from datetime import datetime, date, timedelta
import json
from enum import Enum

class TipoLicenca(Enum):
    """Tipos de licenças disponíveis"""
    FUNCIONAMENTO = "Alvará de Funcionamento"
    CONSTRUCAO = "Alvará de Construção"
    DEMOLICAO = "Alvará de Demolição"
    REFORMA = "Alvará de Reforma"
    EVENTO = "Licença para Evento"
    PROPAGANDA = "Licença de Propaganda"
    AMBIENTAL = "Licença Ambiental"
    SANITARIA = "Licença Sanitária"
    BOMBEIROS = "Licença do Corpo de Bombeiros"

class StatusProcesso(Enum):
    """Status possíveis do processo"""
    PROTOCOLADO = "Protocolado"
    EM_ANALISE = "Em Análise"
    EXIGENCIA = "Aguardando Exigências"
    APROVADO = "Aprovado"
    INDEFERIDO = "Indeferido"
    CANCELADO = "Cancelado"
    EXPEDIDO = "Expedido"

class AlvaraManager:
    """Gerenciador completo de alvarás e licenças"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.settings = self.get_alvara_settings()
    
    def get_alvara_settings(self):
        """Obter configurações de licenciamento"""
        try:
            settings = frappe.get_single("Alvara Settings")
            return settings
        except:
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Configurações padrão"""
        return {
            "prazo_analise_dias": 30,
            "prazo_resposta_exigencia": 15,
            "validade_alvara_meses": 12,
            "taxa_protocolo": 50.0,
            "taxa_vistoria": 100.0,
            "multa_funcionamento_irregular": 500.0
        }
    
    def create_processo(self, requerente_data, licenca_data, documentos=[]):
        """Criar novo processo de licenciamento"""
        try:
            # Gerar número do processo
            numero_processo = self.generate_processo_number()
            
            # Criar processo
            processo = frappe.new_doc("Processo Licenciamento")
            processo.update({
                "numero_processo": numero_processo,
                "tipo_licenca": licenca_data["tipo_licenca"],
                "descricao_atividade": licenca_data["descricao_atividade"],
                "endereco_atividade": licenca_data["endereco_atividade"],
                "area_total": licenca_data.get("area_total", 0),
                "valor_investimento": licenca_data.get("valor_investimento", 0),
                
                # Dados do requerente
                "requerente_nome": requerente_data["nome"],
                "requerente_cpf_cnpj": requerente_data["cpf_cnpj"],
                "requerente_telefone": requerente_data.get("telefone", ""),
                "requerente_email": requerente_data.get("email", ""),
                "requerente_endereco": requerente_data.get("endereco", ""),
                
                # Controle do processo
                "data_protocolo": frappe.utils.nowdate(),
                "status": StatusProcesso.PROTOCOLADO.value,
                "prazo_analise": self.calculate_prazo_analise(),
                "responsavel_analise": self.get_analista_responsavel(licenca_data["tipo_licenca"])
            })
            
            # Adicionar documentos
            for doc in documentos:
                processo.append("documentos", {
                    "nome_documento": doc["nome"],
                    "obrigatorio": doc.get("obrigatorio", True),
                    "status": "Pendente",
                    "observacoes": doc.get("observacoes", "")
                })
            
            # Calcular taxas
            taxas = self.calculate_taxas(licenca_data)
            processo.valor_taxas = taxas["total"]
            
            processo.insert()
            
            # Gerar guia de pagamento das taxas
            guia = self.generate_guia_taxas(processo, taxas)
            
            # Criar timeline inicial
            self.add_timeline_entry(
                processo.name,
                "Processo protocolado",
                f"Processo {numero_processo} protocolado em {frappe.utils.nowdate()}",
                "info"
            )
            
            return {
                "success": True,
                "processo_id": processo.name,
                "numero_processo": numero_processo,
                "guia_pagamento": guia.name,
                "valor_taxas": taxas["total"]
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Processo Creation Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_processo_number(self):
        """Gerar número sequencial do processo"""
        year = datetime.now().year
        
        # Buscar último número do ano
        last_number = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(numero_processo, 1, 6) AS UNSIGNED))
            FROM `tabProcesso Licenciamento`
            WHERE YEAR(data_protocolo) = %s
        """, [year])[0][0] or 0
        
        next_number = last_number + 1
        return f"{next_number:06d}/{year}"
    
    def calculate_prazo_analise(self):
        """Calcular prazo de análise"""
        prazo_dias = self.settings.get("prazo_analise_dias", 30)
        return frappe.utils.add_days(frappe.utils.nowdate(), prazo_dias)
    
    def get_analista_responsavel(self, tipo_licenca):
        """Obter analista responsável baseado no tipo de licença"""
        # Mapear tipos de licença para setores
        setores = {
            TipoLicenca.FUNCIONAMENTO.value: "Tributário",
            TipoLicenca.CONSTRUCAO.value: "Engenharia",
            TipoLicenca.DEMOLICAO.value: "Engenharia",
            TipoLicenca.REFORMA.value: "Engenharia",
            TipoLicenca.AMBIENTAL.value: "Meio Ambiente",
            TipoLicenca.SANITARIA.value: "Vigilância Sanitária",
            TipoLicenca.BOMBEIROS.value: "Corpo de Bombeiros"
        }
        
        setor = setores.get(tipo_licenca, "Licenciamento")
        
        # Buscar analista disponível do setor
        analista = frappe.db.get_value(
            "User",
            {"department": setor, "enabled": 1},
            "name"
        )
        
        return analista
    
    def calculate_taxas(self, licenca_data):
        """Calcular taxas do processo"""
        taxas = {
            "protocolo": self.settings.get("taxa_protocolo", 50.0),
            "vistoria": 0,
            "emissao": 0,
            "total": 0
        }
        
        tipo_licenca = licenca_data["tipo_licenca"]
        
        # Taxa de vistoria para alguns tipos
        if tipo_licenca in [
            TipoLicenca.FUNCIONAMENTO.value,
            TipoLicenca.CONSTRUCAO.value,
            TipoLicenca.SANITARIA.value
        ]:
            taxas["vistoria"] = self.settings.get("taxa_vistoria", 100.0)
        
        # Taxa de emissão baseada no tipo e área
        area = licenca_data.get("area_total", 0)
        if tipo_licenca == TipoLicenca.CONSTRUCAO.value:
            taxas["emissao"] = max(50.0, area * 0.5)  # R$ 0,50 por m²
        elif tipo_licenca == TipoLicenca.FUNCIONAMENTO.value:
            taxas["emissao"] = max(30.0, area * 0.3)  # R$ 0,30 por m²
        else:
            taxas["emissao"] = 30.0  # Taxa fixa
        
        taxas["total"] = sum(taxas.values())
        return taxas
    
    def generate_guia_taxas(self, processo, taxas):
        """Gerar guia de pagamento das taxas"""
        guia = frappe.new_doc("Guia Pagamento Licenca")
        guia.update({
            "processo": processo.name,
            "numero_processo": processo.numero_processo,
            "requerente": processo.requerente_nome,
            "cpf_cnpj": processo.requerente_cpf_cnpj,
            "valor_protocolo": taxas["protocolo"],
            "valor_vistoria": taxas["vistoria"],
            "valor_emissao": taxas["emissao"],
            "valor_total": taxas["total"],
            "data_vencimento": frappe.utils.add_days(frappe.utils.nowdate(), 10),
            "situacao": "Pendente"
        })
        
        guia.insert()
        return guia
    
    def process_pagamento_taxas(self, guia_id, data_pagamento=None):
        """Processar pagamento das taxas"""
        try:
            guia = frappe.get_doc("Guia Pagamento Licenca", guia_id)
            data_pagamento = data_pagamento or frappe.utils.nowdate()
            
            # Atualizar guia
            guia.situacao = "Pago"
            guia.data_pagamento = data_pagamento
            guia.save()
            
            # Atualizar processo
            processo = frappe.get_doc("Processo Licenciamento", guia.processo)
            processo.taxas_pagas = True
            processo.data_pagamento_taxas = data_pagamento
            
            # Se estava aguardando pagamento, iniciar análise
            if processo.status == StatusProcesso.PROTOCOLADO.value:
                processo.status = StatusProcesso.EM_ANALISE.value
                processo.data_inicio_analise = data_pagamento
            
            processo.save()
            
            # Adicionar entrada na timeline
            self.add_timeline_entry(
                processo.name,
                "Taxas pagas",
                f"Taxas pagas em {data_pagamento}. Processo encaminhado para análise.",
                "success"
            )
            
            return {
                "success": True,
                "message": "Pagamento processado com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def iniciar_analise(self, processo_id, analista_id):
        """Iniciar análise técnica do processo"""
        try:
            processo = frappe.get_doc("Processo Licenciamento", processo_id)
            
            # Verificar se taxas foram pagas
            if not processo.taxas_pagas:
                frappe.throw(_("Taxas não foram pagas"))
            
            # Atualizar processo
            processo.status = StatusProcesso.EM_ANALISE.value
            processo.responsavel_analise = analista_id
            processo.data_inicio_analise = frappe.utils.nowdate()
            processo.save()
            
            # Timeline
            analista_nome = frappe.get_value("User", analista_id, "full_name")
            self.add_timeline_entry(
                processo.name,
                "Análise iniciada",
                f"Análise iniciada pelo analista {analista_nome}",
                "info"
            )
            
            return {
                "success": True,
                "message": "Análise iniciada com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_exigencia(self, processo_id, descricao, documentos_necessarios=[]):
        """Criar exigência técnica"""
        try:
            processo = frappe.get_doc("Processo Licenciamento", processo_id)
            
            # Criar documento de exigência
            exigencia = frappe.new_doc("Exigencia Tecnica")
            exigencia.update({
                "processo": processo_id,
                "descricao": descricao,
                "data_exigencia": frappe.utils.nowdate(),
                "prazo_resposta": frappe.utils.add_days(
                    frappe.utils.nowdate(),
                    self.settings.get("prazo_resposta_exigencia", 15)
                ),
                "status": "Pendente",
                "analista": frappe.session.user
            })
            
            # Adicionar documentos necessários
            for doc in documentos_necessarios:
                exigencia.append("documentos", {
                    "nome_documento": doc,
                    "status": "Pendente"
                })
            
            exigencia.insert()
            
            # Atualizar processo
            processo.status = StatusProcesso.EXIGENCIA.value
            processo.save()
            
            # Timeline
            self.add_timeline_entry(
                processo.name,
                "Exigência emitida",
                f"Exigência técnica emitida. Prazo: {exigencia.prazo_resposta}",
                "warning"
            )
            
            return {
                "success": True,
                "exigencia_id": exigencia.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def responder_exigencia(self, exigencia_id, resposta, documentos=[]):
        """Responder exigência técnica"""
        try:
            exigencia = frappe.get_doc("Exigencia Tecnica", exigencia_id)
            
            # Verificar prazo
            if frappe.utils.getdate() > exigencia.prazo_resposta:
                frappe.throw(_("Prazo para resposta da exigência expirado"))
            
            # Atualizar exigência
            exigencia.resposta = resposta
            exigencia.data_resposta = frappe.utils.nowdate()
            exigencia.status = "Respondida"
            
            # Adicionar documentos da resposta
            for doc in documentos:
                exigencia.append("documentos_resposta", {
                    "nome_documento": doc["nome"],
                    "anexo": doc.get("anexo", "")
                })
            
            exigencia.save()
            
            # Atualizar processo
            processo = frappe.get_doc("Processo Licenciamento", exigencia.processo)
            processo.status = StatusProcesso.EM_ANALISE.value
            processo.save()
            
            # Timeline
            self.add_timeline_entry(
                processo.name,
                "Exigência respondida",
                f"Exigência respondida em {frappe.utils.nowdate()}",
                "info"
            )
            
            return {
                "success": True,
                "message": "Exigência respondida com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def aprovar_processo(self, processo_id, observacoes=""):
        """Aprovar processo de licenciamento"""
        try:
            processo = frappe.get_doc("Processo Licenciamento", processo_id)
            
            # Atualizar processo
            processo.status = StatusProcesso.APROVADO.value
            processo.data_aprovacao = frappe.utils.nowdate()
            processo.observacoes_aprovacao = observacoes
            processo.save()
            
            # Gerar alvará
            alvara = self.generate_alvara(processo)
            
            # Timeline
            self.add_timeline_entry(
                processo.name,
                "Processo aprovado",
                f"Processo aprovado. Alvará {alvara.numero} gerado.",
                "success"
            )
            
            return {
                "success": True,
                "alvara_id": alvara.name,
                "numero_alvara": alvara.numero
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def indeferir_processo(self, processo_id, motivos):
        """Indeferir processo de licenciamento"""
        try:
            processo = frappe.get_doc("Processo Licenciamento", processo_id)
            
            # Atualizar processo
            processo.status = StatusProcesso.INDEFERIDO.value
            processo.data_indeferimento = frappe.utils.nowdate()
            processo.motivos_indeferimento = motivos
            processo.save()
            
            # Timeline
            self.add_timeline_entry(
                processo.name,
                "Processo indeferido",
                f"Processo indeferido em {frappe.utils.nowdate()}",
                "danger"
            )
            
            return {
                "success": True,
                "message": "Processo indeferido"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_alvara(self, processo):
        """Gerar alvará aprovado"""
        # Gerar número do alvará
        numero_alvara = self.generate_alvara_number(processo.tipo_licenca)
        
        # Calcular validade
        validade_meses = self.settings.get("validade_alvara_meses", 12)
        data_validade = frappe.utils.add_months(frappe.utils.nowdate(), validade_meses)
        
        # Criar alvará
        alvara = frappe.new_doc("Alvara Municipal")
        alvara.update({
            "numero": numero_alvara,
            "processo": processo.name,
            "tipo_licenca": processo.tipo_licenca,
            "requerente_nome": processo.requerente_nome,
            "requerente_cpf_cnpj": processo.requerente_cpf_cnpj,
            "endereco_atividade": processo.endereco_atividade,
            "descricao_atividade": processo.descricao_atividade,
            "area_licenciada": processo.area_total,
            "data_emissao": frappe.utils.nowdate(),
            "data_validade": data_validade,
            "status": "Vigente"
        })
        
        alvara.insert()
        alvara.submit()
        
        # Atualizar processo
        processo.status = StatusProcesso.EXPEDIDO.value
        processo.alvara_gerado = alvara.name
        processo.save()
        
        return alvara
    
    def generate_alvara_number(self, tipo_licenca):
        """Gerar número do alvará"""
        year = datetime.now().year
        
        # Prefixo baseado no tipo
        prefixos = {
            TipoLicenca.FUNCIONAMENTO.value: "AF",
            TipoLicenca.CONSTRUCAO.value: "AC",
            TipoLicenca.DEMOLICAO.value: "AD",
            TipoLicenca.REFORMA.value: "AR",
            TipoLicenca.EVENTO.value: "AE",
            TipoLicenca.PROPAGANDA.value: "AP",
            TipoLicenca.AMBIENTAL.value: "AA",
            TipoLicenca.SANITARIA.value: "AS",
            TipoLicenca.BOMBEIROS.value: "AB"
        }
        
        prefixo = prefixos.get(tipo_licenca, "AL")
        
        # Buscar último número
        last_number = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(numero, 3, 6) AS UNSIGNED))
            FROM `tabAlvara Municipal`
            WHERE numero LIKE %s
            AND YEAR(data_emissao) = %s
        """, [f"{prefixo}%", year])[0][0] or 0
        
        next_number = last_number + 1
        return f"{prefixo}{next_number:06d}/{year}"
    
    def add_timeline_entry(self, processo_id, titulo, descricao, tipo="info"):
        """Adicionar entrada na timeline do processo"""
        timeline = frappe.new_doc("Processo Timeline")
        timeline.update({
            "processo": processo_id,
            "titulo": titulo,
            "descricao": descricao,
            "tipo": tipo,
            "data_evento": frappe.utils.now(),
            "usuario": frappe.session.user
        })
        timeline.insert()
    
    def get_processo_status(self, numero_processo):
        """Obter status atual do processo"""
        try:
            processo = frappe.get_doc("Processo Licenciamento", {"numero_processo": numero_processo})
            
            # Obter timeline
            timeline = frappe.get_all(
                "Processo Timeline",
                filters={"processo": processo.name},
                fields=["titulo", "descricao", "data_evento", "tipo"],
                order_by="data_evento desc"
            )
            
            # Obter exigências pendentes
            exigencias = frappe.get_all(
                "Exigencia Tecnica",
                filters={"processo": processo.name, "status": "Pendente"},
                fields=["name", "descricao", "prazo_resposta"]
            )
            
            return {
                "success": True,
                "data": {
                    "numero_processo": processo.numero_processo,
                    "status": processo.status,
                    "tipo_licenca": processo.tipo_licenca,
                    "data_protocolo": processo.data_protocolo,
                    "prazo_analise": processo.prazo_analise,
                    "taxas_pagas": processo.taxas_pagas,
                    "timeline": timeline,
                    "exigencias_pendentes": exigencias,
                    "alvara_numero": getattr(processo, 'alvara_gerado', None)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Instância global
alvara_manager = AlvaraManager()

# APIs públicas
@frappe.whitelist()
def create_licenciamento_processo(requerente_data, licenca_data, documentos=[]):
    """API para criar processo de licenciamento"""
    try:
        if isinstance(requerente_data, str):
            requerente_data = json.loads(requerente_data)
        if isinstance(licenca_data, str):
            licenca_data = json.loads(licenca_data)
        if isinstance(documentos, str):
            documentos = json.loads(documentos)
        
        return alvara_manager.create_processo(requerente_data, licenca_data, documentos)
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def consultar_processo(numero_processo):
    """API para consultar status do processo"""
    return alvara_manager.get_processo_status(numero_processo)

@frappe.whitelist()
def pagar_taxas_processo(guia_id, data_pagamento=None):
    """API para processar pagamento de taxas"""
    return alvara_manager.process_pagamento_taxas(guia_id, data_pagamento)