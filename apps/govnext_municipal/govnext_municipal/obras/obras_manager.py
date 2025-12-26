# -*- coding: utf-8 -*-
"""
Módulo de Gestão de Obras Públicas
Sistema completo para controle e fiscalização de obras municipais
"""

import frappe
from frappe import _
from datetime import datetime, date, timedelta
import json
from enum import Enum

class StatusObra(Enum):
    """Status possíveis da obra"""
    PLANEJADA = "Planejada"
    LICITACAO = "Em Licitação"
    CONTRATADA = "Contratada"
    EM_EXECUCAO = "Em Execução"
    PARALISADA = "Paralisada"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"

class TipoObra(Enum):
    """Tipos de obras"""
    PAVIMENTACAO = "Pavimentação"
    SANEAMENTO = "Saneamento"
    EDIFICACAO = "Edificação"
    ILUMINACAO = "Iluminação Pública"
    PRACA = "Praça/Área de Lazer"
    PONTE = "Ponte/Viaduto"
    DRENAGEM = "Drenagem"
    PAISAGISMO = "Paisagismo"
    REFORMA = "Reforma"
    DEMOLICAO = "Demolição"

class ObrasManager:
    """Gerenciador completo de obras públicas"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.settings = self.get_obras_settings()
    
    def get_obras_settings(self):
        """Obter configurações de obras"""
        try:
            settings = frappe.get_single("Obras Settings")
            return settings
        except:
            return self.get_default_settings()
    
    def get_default_settings(self):
        """Configurações padrão"""
        return {
            "margem_atraso_alerta": 10,  # dias
            "frequencia_medicao": "Mensal",
            "percentual_max_medicao": 80,  # % para medição sem conclusão
            "prazo_entrega_projeto": 30,  # dias
            "multa_atraso_percentual": 0.1  # % por dia
        }
    
    def create_obra(self, obra_data, orcamento_data, cronograma_data):
        """Criar nova obra pública"""
        try:
            # Gerar código da obra
            codigo_obra = self.generate_obra_code()
            
            # Criar obra
            obra = frappe.new_doc("Obra Publica")
            obra.update({
                "codigo": codigo_obra,
                "nome": obra_data["nome"],
                "tipo_obra": obra_data["tipo_obra"],
                "descricao": obra_data["descricao"],
                "endereco": obra_data["endereco"],
                "bairro": obra_data.get("bairro", ""),
                "coordenadas_gps": obra_data.get("coordenadas_gps", ""),
                
                # Dados do projeto
                "valor_orcado": orcamento_data["valor_total"],
                "fonte_recurso": orcamento_data["fonte_recurso"],
                "programa_governo": orcamento_data.get("programa_governo", ""),
                "convênio": orcamento_data.get("convenio", ""),
                
                # Cronograma
                "data_inicio_prevista": cronograma_data["data_inicio"],
                "data_fim_prevista": cronograma_data["data_fim"],
                "prazo_execucao_dias": cronograma_data["prazo_dias"],
                
                # Status inicial
                "status": StatusObra.PLANEJADA.value,
                "data_criacao": frappe.utils.nowdate(),
                "responsavel_projeto": frappe.session.user,
                "secretaria_responsavel": obra_data.get("secretaria", "Obras")
            })
            
            # Adicionar itens do orçamento
            for item in orcamento_data.get("itens", []):
                obra.append("orcamento_itens", {
                    "item_servico": item["descricao"],
                    "unidade": item["unidade"],
                    "quantidade": item["quantidade"],
                    "valor_unitario": item["valor_unitario"],
                    "valor_total": item["quantidade"] * item["valor_unitario"]
                })
            
            obra.insert()
            
            # Criar cronograma detalhado
            self.create_cronograma_detalhado(obra.name, cronograma_data)
            
            # Criar histórico inicial
            self.add_historico_entry(
                obra.name,
                "Obra criada",
                f"Obra {codigo_obra} criada no sistema",
                "info"
            )
            
            return {
                "success": True,
                "obra_id": obra.name,
                "codigo_obra": codigo_obra,
                "valor_orcado": orcamento_data["valor_total"]
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Obra Creation Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_obra_code(self):
        """Gerar código sequencial da obra"""
        year = datetime.now().year
        
        # Buscar último número do ano
        last_number = frappe.db.sql("""
            SELECT MAX(CAST(SUBSTRING(codigo, 1, 4) AS UNSIGNED))
            FROM `tabObra Publica`
            WHERE YEAR(data_criacao) = %s
        """, [year])[0][0] or 0
        
        next_number = last_number + 1
        return f"{next_number:04d}/{year}"
    
    def create_cronograma_detalhado(self, obra_id, cronograma_data):
        """Criar cronograma físico-financeiro detalhado"""
        etapas = cronograma_data.get("etapas", [])
        
        for etapa in etapas:
            cronograma = frappe.new_doc("Cronograma Obra")
            cronograma.update({
                "obra": obra_id,
                "etapa": etapa["nome"],
                "descricao": etapa["descricao"],
                "data_inicio_prevista": etapa["data_inicio"],
                "data_fim_prevista": etapa["data_fim"],
                "percentual_fisico": etapa["percentual_fisico"],
                "valor_previsto": etapa["valor_previsto"],
                "ordem_execucao": etapa.get("ordem", 1),
                "status": "Planejada"
            })
            cronograma.insert()
    
    def iniciar_licitacao(self, obra_id, licitacao_data):
        """Iniciar processo licitatório da obra"""
        try:
            obra = frappe.get_doc("Obra Publica", obra_id)
            
            # Atualizar status
            obra.status = StatusObra.LICITACAO.value
            obra.data_inicio_licitacao = frappe.utils.nowdate()
            obra.save()
            
            # Criar processo licitatório
            licitacao = frappe.new_doc("Licitacao Obra")
            licitacao.update({
                "obra": obra_id,
                "modalidade": licitacao_data["modalidade"],
                "numero_edital": licitacao_data["numero_edital"],
                "data_publicacao": licitacao_data["data_publicacao"],
                "data_abertura": licitacao_data["data_abertura"],
                "valor_estimado": obra.valor_orcado,
                "objeto": f"Execução de {obra.nome}",
                "status": "Publicada"
            })
            licitacao.insert()
            
            # Histórico
            self.add_historico_entry(
                obra_id,
                "Licitação iniciada",
                f"Processo licitatório iniciado - Edital {licitacao_data['numero_edital']}",
                "info"
            )
            
            return {
                "success": True,
                "licitacao_id": licitacao.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def contratar_obra(self, obra_id, contrato_data):
        """Contratar obra após licitação"""
        try:
            obra = frappe.get_doc("Obra Publica", obra_id)
            
            # Atualizar obra
            obra.status = StatusObra.CONTRATADA.value
            obra.empresa_contratada = contrato_data["empresa"]
            obra.cnpj_contratada = contrato_data["cnpj"]
            obra.valor_contratado = contrato_data["valor_contrato"]
            obra.data_assinatura_contrato = contrato_data["data_assinatura"]
            obra.numero_contrato = contrato_data["numero_contrato"]
            obra.prazo_execucao_contratual = contrato_data["prazo_execucao"]
            obra.save()
            
            # Recalcular datas baseado no contrato
            if contrato_data.get("data_inicio_execucao"):
                obra.data_inicio_real = contrato_data["data_inicio_execucao"]
                obra.data_fim_prevista = frappe.utils.add_days(
                    contrato_data["data_inicio_execucao"],
                    contrato_data["prazo_execucao"]
                )
                obra.save()
            
            # Histórico
            self.add_historico_entry(
                obra_id,
                "Obra contratada",
                f"Contrato {contrato_data['numero_contrato']} assinado com {contrato_data['empresa']}",
                "success"
            )
            
            return {
                "success": True,
                "message": "Obra contratada com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def iniciar_execucao(self, obra_id, dados_inicio):
        """Iniciar execução da obra"""
        try:
            obra = frappe.get_doc("Obra Publica", obra_id)
            
            # Verificar se está contratada
            if obra.status != StatusObra.CONTRATADA.value:
                frappe.throw(_("Obra deve estar contratada para iniciar execução"))
            
            # Atualizar obra
            obra.status = StatusObra.EM_EXECUCAO.value
            obra.data_inicio_real = dados_inicio["data_inicio"]
            obra.responsavel_fiscalizacao = dados_inicio["fiscal_responsavel"]
            obra.diario_obra_ativo = True
            obra.save()
            
            # Atualizar cronograma
            self.update_cronograma_inicio(obra_id, dados_inicio["data_inicio"])
            
            # Histórico
            self.add_historico_entry(
                obra_id,
                "Execução iniciada",
                f"Obra iniciada em {dados_inicio['data_inicio']}",
                "success"
            )
            
            return {
                "success": True,
                "message": "Execução iniciada com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_cronograma_inicio(self, obra_id, data_inicio):
        """Atualizar cronograma com data de início real"""
        cronogramas = frappe.get_all(
            "Cronograma Obra",
            filters={"obra": obra_id},
            fields=["name", "data_inicio_prevista", "data_fim_prevista"],
            order_by="ordem_execucao"
        )
        
        data_atual = frappe.utils.getdate(data_inicio)
        
        for cronograma in cronogramas:
            doc = frappe.get_doc("Cronograma Obra", cronograma["name"])
            
            # Calcular defasagem
            data_prevista = frappe.utils.getdate(cronograma["data_inicio_prevista"])
            diferenca_dias = (data_atual - data_prevista).days
            
            # Atualizar datas
            doc.data_inicio_real = data_atual
            doc.data_fim_real = frappe.utils.add_days(
                cronograma["data_fim_prevista"],
                diferenca_dias
            )
            doc.status = "Em Execução" if doc.ordem_execucao == 1 else "Aguardando"
            doc.save()
            
            # Próxima etapa
            data_atual = doc.data_fim_real
    
    def create_medicao(self, obra_id, medicao_data):
        """Criar medição de obra"""
        try:
            obra = frappe.get_doc("Obra Publica", obra_id)
            
            if obra.status != StatusObra.EM_EXECUCAO.value:
                frappe.throw(_("Obra deve estar em execução para medição"))
            
            # Gerar número da medição
            numero_medicao = self.get_next_medicao_number(obra_id)
            
            # Criar medição
            medicao = frappe.new_doc("Medicao Obra")
            medicao.update({
                "obra": obra_id,
                "numero": numero_medicao,
                "periodo_inicio": medicao_data["periodo_inicio"],
                "periodo_fim": medicao_data["periodo_fim"],
                "data_medicao": frappe.utils.nowdate(),
                "fiscal_responsavel": medicao_data["fiscal_responsavel"],
                "observacoes": medicao_data.get("observacoes", ""),
                "status": "Em Análise"
            })
            
            # Adicionar itens medidos
            valor_total_medicao = 0
            for item in medicao_data["itens"]:
                valor_item = item["quantidade_executada"] * item["valor_unitario"]
                valor_total_medicao += valor_item
                
                medicao.append("itens", {
                    "item_servico": item["item_servico"],
                    "unidade": item["unidade"],
                    "quantidade_prevista": item["quantidade_prevista"],
                    "quantidade_executada": item["quantidade_executada"],
                    "valor_unitario": item["valor_unitario"],
                    "valor_total": valor_item,
                    "percentual_executado": (item["quantidade_executada"] / item["quantidade_prevista"]) * 100
                })
            
            medicao.valor_total = valor_total_medicao
            medicao.insert()
            
            # Atualizar percentual da obra
            self.update_percentual_obra(obra_id)
            
            # Histórico
            self.add_historico_entry(
                obra_id,
                f"Medição {numero_medicao} criada",
                f"Medição no valor de R$ {valor_total_medicao:,.2f}",
                "info"
            )
            
            return {
                "success": True,
                "medicao_id": medicao.name,
                "numero_medicao": numero_medicao,
                "valor_medicao": valor_total_medicao
            }
            
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Medicao Creation Error")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_next_medicao_number(self, obra_id):
        """Obter próximo número de medição"""
        last_number = frappe.db.sql("""
            SELECT MAX(numero)
            FROM `tabMedicao Obra`
            WHERE obra = %s
        """, [obra_id])[0][0] or 0
        
        return last_number + 1
    
    def update_percentual_obra(self, obra_id):
        """Atualizar percentual executado da obra"""
        # Calcular percentual baseado nas medições
        percentual_executado = frappe.db.sql("""
            SELECT SUM(percentual_executado * valor_total) / SUM(valor_total) as percentual_medio
            FROM `tabMedicao Obra Item`
            WHERE parent IN (
                SELECT name FROM `tabMedicao Obra`
                WHERE obra = %s AND status = 'Aprovada'
            )
        """, [obra_id])[0][0] or 0
        
        # Atualizar obra
        obra = frappe.get_doc("Obra Publica", obra_id)
        obra.percentual_executado = min(percentual_executado, 100)
        
        # Calcular valor executado
        obra.valor_executado = (obra.valor_contratado or obra.valor_orcado) * (percentual_executado / 100)
        
        obra.save()
    
    def add_foto_obra(self, obra_id, foto_data):
        """Adicionar foto da obra"""
        try:
            foto = frappe.new_doc("Foto Obra")
            foto.update({
                "obra": obra_id,
                "titulo": foto_data["titulo"],
                "descricao": foto_data.get("descricao", ""),
                "data_foto": foto_data.get("data_foto", frappe.utils.nowdate()),
                "arquivo": foto_data["arquivo"],
                "etapa_obra": foto_data.get("etapa", ""),
                "coordenadas_gps": foto_data.get("coordenadas", ""),
                "fotografo": frappe.session.user
            })
            foto.insert()
            
            return {
                "success": True,
                "foto_id": foto.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_diario_obra(self, obra_id, diario_data):
        """Criar entrada no diário de obra"""
        try:
            diario = frappe.new_doc("Diario Obra")
            diario.update({
                "obra": obra_id,
                "data": diario_data["data"],
                "condicoes_tempo": diario_data["condicoes_tempo"],
                "servicos_executados": diario_data["servicos_executados"],
                "mao_obra_presente": diario_data.get("mao_obra_presente", 0),
                "equipamentos_utilizados": diario_data.get("equipamentos", ""),
                "materiais_entregues": diario_data.get("materiais", ""),
                "observacoes": diario_data.get("observacoes", ""),
                "problemas_encontrados": diario_data.get("problemas", ""),
                "responsavel": frappe.session.user
            })
            diario.insert()
            
            return {
                "success": True,
                "diario_id": diario.name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def concluir_obra(self, obra_id, dados_conclusao):
        """Concluir obra"""
        try:
            obra = frappe.get_doc("Obra Publica", obra_id)
            
            # Atualizar obra
            obra.status = StatusObra.CONCLUIDA.value
            obra.data_conclusao = dados_conclusao["data_conclusao"]
            obra.percentual_executado = 100
            obra.observacoes_conclusao = dados_conclusao.get("observacoes", "")
            obra.save()
            
            # Criar medição final se necessário
            if dados_conclusao.get("medicao_final"):
                self.create_medicao_final(obra_id, dados_conclusao["medicao_final"])
            
            # Histórico
            self.add_historico_entry(
                obra_id,
                "Obra concluída",
                f"Obra concluída em {dados_conclusao['data_conclusao']}",
                "success"
            )
            
            return {
                "success": True,
                "message": "Obra concluída com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_medicao_final(self, obra_id, medicao_data):
        """Criar medição final da obra"""
        medicao_data["tipo"] = "Final"
        return self.create_medicao(obra_id, medicao_data)
    
    def add_historico_entry(self, obra_id, titulo, descricao, tipo="info"):
        """Adicionar entrada no histórico da obra"""
        historico = frappe.new_doc("Historico Obra")
        historico.update({
            "obra": obra_id,
            "titulo": titulo,
            "descricao": descricao,
            "tipo": tipo,
            "data_evento": frappe.utils.now(),
            "usuario": frappe.session.user
        })
        historico.insert()
    
    def get_obra_dashboard(self, obra_id):
        """Obter dados do dashboard da obra"""
        try:
            obra = frappe.get_doc("Obra Publica", obra_id)
            
            # Dados básicos
            dashboard = {
                "obra": {
                    "codigo": obra.codigo,
                    "nome": obra.nome,
                    "status": obra.status,
                    "percentual_executado": obra.percentual_executado,
                    "valor_orcado": obra.valor_orcado,
                    "valor_contratado": obra.valor_contratado or obra.valor_orcado,
                    "valor_executado": obra.valor_executado or 0,
                    "data_inicio_prevista": obra.data_inicio_prevista,
                    "data_fim_prevista": obra.data_fim_prevista,
                    "data_inicio_real": obra.data_inicio_real,
                    "empresa_contratada": obra.empresa_contratada
                }
            }
            
            # Cronograma
            dashboard["cronograma"] = frappe.get_all(
                "Cronograma Obra",
                filters={"obra": obra_id},
                fields=["etapa", "percentual_fisico", "status", "data_inicio_prevista", "data_fim_prevista"],
                order_by="ordem_execucao"
            )
            
            # Medições
            dashboard["medicoes"] = frappe.get_all(
                "Medicao Obra",
                filters={"obra": obra_id},
                fields=["numero", "data_medicao", "valor_total", "status"],
                order_by="numero desc",
                limit=5
            )
            
            # Fotos recentes
            dashboard["fotos_recentes"] = frappe.get_all(
                "Foto Obra",
                filters={"obra": obra_id},
                fields=["titulo", "data_foto", "arquivo"],
                order_by="data_foto desc",
                limit=4
            )
            
            # Últimas entradas do diário
            dashboard["diario_recente"] = frappe.get_all(
                "Diario Obra",
                filters={"obra": obra_id},
                fields=["data", "servicos_executados", "observacoes"],
                order_by="data desc",
                limit=3
            )
            
            return {
                "success": True,
                "data": dashboard
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_obras_statistics(self, ano=None):
        """Obter estatísticas de obras"""
        ano = ano or self.current_year
        
        try:
            stats = {}
            
            # Obras por status
            for status in StatusObra:
                stats[f"obras_{status.value.lower().replace(' ', '_')}"] = frappe.db.count(
                    "Obra Publica",
                    {"status": status.value, "YEAR(data_criacao)": ano}
                )
            
            # Valores
            stats["valor_total_orcado"] = frappe.db.sql("""
                SELECT SUM(valor_orcado)
                FROM `tabObra Publica`
                WHERE YEAR(data_criacao) = %s
            """, [ano])[0][0] or 0
            
            stats["valor_total_contratado"] = frappe.db.sql("""
                SELECT SUM(valor_contratado)
                FROM `tabObra Publica`
                WHERE YEAR(data_criacao) = %s
                AND valor_contratado IS NOT NULL
            """, [ano])[0][0] or 0
            
            stats["valor_total_executado"] = frappe.db.sql("""
                SELECT SUM(valor_executado)
                FROM `tabObra Publica`
                WHERE YEAR(data_criacao) = %s
                AND valor_executado IS NOT NULL
            """, [ano])[0][0] or 0
            
            # Obras por tipo
            stats["obras_por_tipo"] = frappe.db.sql("""
                SELECT tipo_obra, COUNT(*) as quantidade
                FROM `tabObra Publica`
                WHERE YEAR(data_criacao) = %s
                GROUP BY tipo_obra
            """, [ano], as_dict=True)
            
            return {
                "success": True,
                "data": stats
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Instância global
obras_manager = ObrasManager()

# APIs públicas
@frappe.whitelist()
def create_obra_publica(obra_data, orcamento_data, cronograma_data):
    """API para criar obra pública"""
    try:
        if isinstance(obra_data, str):
            obra_data = json.loads(obra_data)
        if isinstance(orcamento_data, str):
            orcamento_data = json.loads(orcamento_data)
        if isinstance(cronograma_data, str):
            cronograma_data = json.loads(cronograma_data)
        
        return obras_manager.create_obra(obra_data, orcamento_data, cronograma_data)
    except Exception as e:
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_obra_dashboard_api(obra_id):
    """API para obter dashboard da obra"""
    return obras_manager.get_obra_dashboard(obra_id)

@frappe.whitelist()
def create_medicao_obra(obra_id, medicao_data):
    """API para criar medição"""
    if isinstance(medicao_data, str):
        medicao_data = json.loads(medicao_data)
    
    return obras_manager.create_medicao(obra_id, medicao_data)

@frappe.whitelist()
def get_obras_stats(ano=None):
    """API para estatísticas de obras"""
    return obras_manager.get_obras_statistics(int(ano) if ano else None)