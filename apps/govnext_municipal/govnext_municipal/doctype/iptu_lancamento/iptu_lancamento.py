# Copyright (c) 2024, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, add_months, add_days, nowdate, cstr
from datetime import datetime, date

class IPTULancamento(Document):
    def validate(self):
        """Validações no lançamento do IPTU"""
        self.validate_year()
        self.validate_cadastro()
        self.get_configuracao_iptu()
        self.fetch_property_data()
        self.calculate_advanced_iptu()
        self.validate_parcelamento()
        self.generate_payment_schedule()
        self.check_inadimplencia()
    
    def validate_year(self):
        """Valida o ano do lançamento"""
        if not self.ano:
            self.ano = str(datetime.now().year)
        
        # Verifica se já existe lançamento para este imóvel no ano
        existing = frappe.get_value("IPTU Lancamento", 
                                   {"inscricao_cadastral": self.inscricao_cadastral, 
                                    "ano": self.ano, 
                                    "name": ("!=", self.name),
                                    "docstatus": ("!=", 2)})
        if existing:
            frappe.throw(f"Já existe lançamento de IPTU para este imóvel no ano {self.ano}")
    
    def validate_cadastro(self):
        """Valida se o cadastro imobiliário existe"""
        if not self.inscricao_cadastral:
            frappe.throw("Inscrição cadastral é obrigatória")
        
        cadastro = frappe.get_doc("IPTU Cadastro", self.inscricao_cadastral)
        if not cadastro:
            frappe.throw("Cadastro imobiliário não encontrado")
        
        # Valida se o imóvel não está isento
        if cadastro.isento and not self.isento_iptu:
            self.isento_iptu = True
            self.motivo_isencao = cadastro.motivo_isencao
    
    def get_configuracao_iptu(self):
        """Obtém a configuração ativa do IPTU para o ano"""
        if not self.configuracao_iptu:
            from frappe.utils import flt
            config = frappe.get_value("IPTU Configuracao", 
                                     {"ano": self.ano, "ativo": 1}, 
                                     "name")
            if config:
                self.configuracao_iptu = config
            else:
                frappe.throw(f"Nenhuma configuração ativa de IPTU encontrada para o ano {self.ano}")
    
    def fetch_property_data(self):
        """Busca dados do imóvel do cadastro"""
        if self.inscricao_cadastral:
            cadastro = frappe.get_doc("IPTU Cadastro", self.inscricao_cadastral)
            
            # Atualiza valor venal se não informado
            if not self.valor_venal_total:
                self.valor_venal_total = cadastro.valor_venal_total
            
            # Busca características do imóvel
            self.tipo_imovel = cadastro.tipo_imovel
            self.area_terreno = cadastro.area_terreno
            self.testada_principal = cadastro.testada_principal
            self.possui_pavimentacao = cadastro.possui_pavimentacao
            self.zona_urbana = cadastro.zona_urbana
            self.isento_iptu = cadastro.isento
            self.motivo_isencao = cadastro.motivo_isencao
    
    def calculate_advanced_iptu(self):
        """Calcula o IPTU usando o sistema avançado"""
        if self.isento_iptu:
            # Imóvel isento
            self.valor_iptu_base = 0
            self.valor_iptu_final = 0
            self.aliquota_aplicada = 0
            self.faixa_valor_aplicada = "ISENTO"
            self.desconto_total = 0
            return
        
        # Obtém configuração
        config = frappe.get_doc("IPTU Configuracao", self.configuracao_iptu)
        
        # Calcula IPTU usando a configuração avançada
        calculo = config.calcular_iptu(
            valor_venal=self.valor_venal_total,
            tipo_imovel=self.tipo_imovel or "Residencial",
            tem_desconto_idoso=self.tem_desconto_idoso,
            tem_desconto_deficiente=self.tem_desconto_deficiente,
            pagamento_vista=self.pagamento_vista,
            pagamento_janeiro=self.pagamento_janeiro,
            area_terreno=self.area_terreno or 0,
            testada_principal=self.testada_principal or 0,
            possui_pavimentacao=self.possui_pavimentacao,
            imovel_esquina=self.imovel_esquina,
            zona_urbana=self.zona_urbana
        )
        
        # Atualiza campos com resultado do cálculo
        self.aliquota_aplicada = calculo['aliquota_aplicada']
        self.faixa_valor_aplicada = calculo['faixa_valor']
        self.valor_iptu_base = calculo['valor_base']
        
        # Atualiza descontos individuais
        for desconto in calculo['detalhes_desconto']:
            if desconto['tipo'] == 'Desconto à Vista':
                self.desconto_vista = desconto['valor']
            elif desconto['tipo'] == 'Desconto Janeiro':
                self.desconto_janeiro = desconto['valor']
            elif desconto['tipo'] == 'Desconto Idoso':
                self.desconto_idoso = desconto['valor']
            elif desconto['tipo'] == 'Desconto Deficiente':
                self.desconto_deficiente = desconto['valor']
        
        self.desconto_total = calculo['total_desconto']
        self.valor_iptu_final = calculo['valor_final']
        
        # Atualiza multas e juros se em atraso
        if self.possui_atraso:
            self.calculate_multas_juros()
    
    def calculate_multas_juros(self):
        """Calcula multas e juros por atraso"""
        if not self.data_vencimento or not self.possui_atraso:
            return
        
        data_calculo = today()
        config = frappe.get_doc("IPTU Configuracao", self.configuracao_iptu)
        
        # Calcula multa e juros
        multa_juros = config.calcular_multa_juros(
            valor_original=self.valor_iptu_final,
            data_vencimento=self.data_vencimento,
            data_calculo=data_calculo
        )
        
        self.dias_atraso = multa_juros['dias_atraso']
        self.valor_multa = multa_juros['valor_multa']
        self.valor_juros = multa_juros['valor_juros']
        self.valor_total_atualizado = multa_juros['valor_total']
    
    def validate_parcelamento(self):
        """Valida configurações de parcelamento"""
        if self.permite_parcelamento and self.configuracao_iptu:
            config = frappe.get_doc("IPTU Configuracao", self.configuracao_iptu)
            
            if not config.permite_parcelamento:
                frappe.throw("Parcelamento não permitido pela configuração atual")
            
            if self.parcelas > config.maximo_parcelas:
                frappe.throw(f"Número máximo de parcelas permitido: {config.maximo_parcelas}")
    
    def generate_payment_schedule(self):
        """Gera cronograma de pagamento avançado"""
        if not self.parcelas or self.parcelas < 1:
            self.parcelas = 1
        
        valor_total = self.valor_total_atualizado or self.valor_iptu_final or 0
        
        if not valor_total:
            return
        
        # Limpa cronograma existente
        self.pagamentos = []
        
        valor_parcela = valor_total / self.parcelas
        data_vencimento = getdate(self.data_vencimento) or getdate()
        
        for i in range(self.parcelas):
            # Calcula data de vencimento (primeira parcela na data informada, demais mensalmente)
            if i == 0:
                vencimento = data_vencimento
            else:
                vencimento = add_months(data_vencimento, i)
            
            # Adiciona parcela ao cronograma
            self.append("pagamentos", {
                "parcela": i + 1,
                "valor": valor_parcela,
                "data_vencimento": vencimento,
                "status": "Pendente",
                "codigo_barras": self.generate_barcode(i + 1, valor_parcela, vencimento)
            })
    
    def generate_barcode(self, parcela, valor, vencimento):
        """Gera código de barras para a parcela"""
        # Implementação simplificada - em produção usaria padrão FEBRABAN
        codigo = f"{self.name}-{parcela:02d}-{int(valor*100):010d}-{vencimento.strftime('%Y%m%d')}"
        return codigo
    
    def check_inadimplencia(self):
        """Verifica se há inadimplência e cria/atualiza registro"""
        if self.status in ['Atrasado', 'Dívida Ativa']:
            self.create_or_update_inadimplencia()
    
    def create_or_update_inadimplencia(self):
        """Cria ou atualiza registro de inadimplência"""
        inadimplencia = frappe.get_value("IPTU Inadimplencia", 
                                        {"inscricao_cadastral": self.inscricao_cadastral,
                                         "ano": self.ano})
        
        if not inadimplencia:
            # Cria novo registro de inadimplência
            inadimplencia_doc = frappe.get_doc({
                "doctype": "IPTU Inadimplencia",
                "inscricao_cadastral": self.inscricao_cadastral,
                "proprietario": self.proprietario,
                "ano": self.ano,
                "data_inicio_inadimplencia": today(),
                "status_inadimplencia": "Inadimplente"
            })
            inadimplencia_doc.save()
        else:
            # Atualiza registro existente
            inadimplencia_doc = frappe.get_doc("IPTU Inadimplencia", inadimplencia)
            inadimplencia_doc.status_inadimplencia = "Inadimplente"
            inadimplencia_doc.data_ultima_atualizacao = today()
            inadimplencia_doc.save()
    
    def on_submit(self):
        """Ações quando o lançamento é confirmado"""
        self.send_notification()
        self.generate_carne()
    
    def send_notification(self):
        """Envia notificação ao proprietário"""
        if self.proprietario:
            try:
                customer = frappe.get_doc("Customer", self.proprietario)
                if customer.email_id:
                    subject = f"IPTU {self.ano} - Lançamento Realizado"
                    
                    message = f"""
                    <h3>IPTU {self.ano} - Lançamento Realizado</h3>
                    <p>Prezado(a) {customer.customer_name},</p>
                    
                    <p>Informamos que o IPTU referente ao ano {self.ano} para o imóvel de 
                    inscrição cadastral <strong>{self.inscricao_cadastral}</strong> foi lançado.</p>
                    
                    <h4>Detalhes do Lançamento:</h4>
                    <ul>
                        <li><strong>Valor Venal:</strong> R$ {flt(self.valor_venal_total):,.2f}</li>
                        <li><strong>Alíquota Aplicada:</strong> {flt(self.aliquota_aplicada):.4f}%</li>
                        <li><strong>Valor Base IPTU:</strong> R$ {flt(self.valor_iptu_base):,.2f}</li>
                        <li><strong>Total Descontos:</strong> R$ {flt(self.desconto_total):,.2f}</li>
                        <li><strong>Valor Final:</strong> R$ {flt(self.valor_iptu_final):,.2f}</li>
                        <li><strong>Número de Parcelas:</strong> {self.parcelas}</li>
                        <li><strong>Data Vencimento 1ª Parcela:</strong> {self.data_vencimento}</li>
                    </ul>
                    
                    <p>O carnê de pagamento será enviado em breve para o endereço cadastrado.</p>
                    <p>Você também pode acessar o Portal do Cidadão para emitir as guias de pagamento.</p>
                    
                    <p>Em caso de dúvidas, entre em contato com a Secretaria de Finanças.</p>
                    """
                    
                    frappe.sendmail(
                        recipients=[customer.email_id],
                        subject=subject,
                        message=message
                    )
                    
                    # Registra envio da notificação
                    self.add_comment("Info", f"Notificação enviada para {customer.email_id}")
                    
            except Exception as e:
                frappe.log_error(f"Erro ao enviar notificação de IPTU: {str(e)}")
    
    def generate_carne(self):
        """Gera carnê de pagamento automaticamente"""
        try:
            carne = frappe.get_doc({
                "doctype": "IPTU Carne",
                "inscricao_cadastral": self.inscricao_cadastral,
                "proprietario": self.proprietario,
                "ano": self.ano,
                "tipo_entrega": "Correios",
                "desconto_vista": self.desconto_vista,
                "desconto_janeiro": self.desconto_janeiro
            })
            
            # Adiciona parcelas ao carnê
            for pagamento in self.pagamentos:
                carne.append("parcelas_carne", {
                    "numero_parcela": pagamento.parcela,
                    "descricao_parcela": f"IPTU {self.ano} - Parcela {pagamento.parcela}/{self.parcelas}",
                    "valor_original": pagamento.valor,
                    "data_vencimento": pagamento.data_vencimento,
                    "codigo_barras": pagamento.codigo_barras,
                    "linha_digitavel": self.generate_linha_digitavel(pagamento.codigo_barras)
                })
            
            carne.save()
            carne.submit()
            
            self.add_comment("Info", f"Carnê {carne.name} gerado automaticamente")
            
        except Exception as e:
            frappe.log_error(f"Erro ao gerar carnê de IPTU: {str(e)}")
    
    def generate_linha_digitavel(self, codigo_barras):
        """Gera linha digitável a partir do código de barras"""
        # Implementação simplificada - em produção seguiria padrão bancário
        return codigo_barras.replace("-", "")
    
    @frappe.whitelist()
    def simular_parcelamento(self, numero_parcelas, valor_entrada=0):
        """Simula parcelamento do débito"""
        if not self.configuracao_iptu:
            frappe.throw("Configuração de IPTU não encontrada")
        
        config = frappe.get_doc("IPTU Configuracao", self.configuracao_iptu)
        valor_total = self.valor_total_atualizado or self.valor_iptu_final
        
        simulacao = config.simular_parcelamento(
            valor_total=valor_total,
            numero_parcelas=int(numero_parcelas),
            valor_entrada=flt(valor_entrada)
        )
        
        return simulacao
    
    @frappe.whitelist()
    def recalcular_iptu(self):
        """Recalcula o IPTU com base nos dados atuais"""
        self.calculate_advanced_iptu()
        self.generate_payment_schedule()
        self.save()
        
        return {
            "valor_iptu_final": self.valor_iptu_final,
            "desconto_total": self.desconto_total,
            "aliquota_aplicada": self.aliquota_aplicada
        }
    
    def on_cancel(self):
        """Ações quando o lançamento é cancelado"""
        # Cancela carnê associado se existir
        carne = frappe.get_value("IPTU Carne", 
                                {"inscricao_cadastral": self.inscricao_cadastral,
                                 "ano": self.ano,
                                 "docstatus": 1})
        if carne:
            carne_doc = frappe.get_doc("IPTU Carne", carne)
            carne_doc.cancel()
        
        # Remove inadimplência se existir
        inadimplencia = frappe.get_value("IPTU Inadimplencia",
                                        {"inscricao_cadastral": self.inscricao_cadastral,
                                         "ano": self.ano})
        if inadimplencia:
            frappe.delete_doc("IPTU Inadimplencia", inadimplencia)