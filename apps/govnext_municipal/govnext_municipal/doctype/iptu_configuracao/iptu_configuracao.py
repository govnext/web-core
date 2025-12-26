# Copyright (c) 2024, GovNext and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate, today, add_days
from datetime import datetime

class IPTUConfiguracao(Document):
    def validate(self):
        """Validações na configuração do IPTU"""
        self.validate_dates()
        self.validate_aliquotas()
        self.validate_desconto_percentuals()
        self.validate_parcelamento()
        self.set_only_one_active()
    
    def validate_dates(self):
        """Valida datas de vigência"""
        if self.data_inicio_vigencia and self.data_fim_vigencia:
            if getdate(self.data_inicio_vigencia) > getdate(self.data_fim_vigencia):
                frappe.throw("Data de início não pode ser maior que data de fim")
    
    def validate_aliquotas(self):
        """Valida se há pelo menos uma alíquota configurada"""
        if not self.aliquotas_progressivas:
            frappe.throw("É necessário configurar pelo menos uma alíquota")
        
        # Ordena as alíquotas por valor mínimo
        self.aliquotas_progressivas = sorted(
            self.aliquotas_progressivas, 
            key=lambda x: flt(x.valor_minimo)
        )
        
        # Valida se não há sobreposição de faixas
        for i, aliquota in enumerate(self.aliquotas_progressivas):
            if i > 0:
                anterior = self.aliquotas_progressivas[i-1]
                if flt(aliquota.valor_minimo) <= flt(anterior.valor_maximo):
                    frappe.throw(f"Faixa de valores da alíquota {i+1} sobrepõe com a anterior")
    
    def validate_desconto_percentuals(self):
        """Valida se os percentuais de desconto são válidos"""
        campos_percentual = [
            'desconto_pagamento_vista', 'desconto_pagamento_janeiro',
            'desconto_idoso', 'desconto_deficiente', 'percentual_multa',
            'percentual_juros_mes', 'percentual_juros_ano'
        ]
        
        for campo in campos_percentual:
            valor = flt(self.get(campo))
            if valor < 0 or valor > 100:
                label = self.meta.get_field(campo).label
                frappe.throw(f"{label} deve estar entre 0% e 100%")
    
    def validate_parcelamento(self):
        """Valida configurações de parcelamento"""
        if self.permite_parcelamento:
            if not self.maximo_parcelas or self.maximo_parcelas < 1:
                frappe.throw("Máximo de parcelas deve ser maior que zero")
            
            if not self.valor_minimo_parcela or self.valor_minimo_parcela <= 0:
                frappe.throw("Valor mínimo da parcela deve ser maior que zero")
            
            percentual_entrada = flt(self.percentual_entrada_minima)
            if percentual_entrada < 0 or percentual_entrada > 100:
                frappe.throw("Percentual mínimo de entrada deve estar entre 0% e 100%")
    
    def set_only_one_active(self):
        """Garante que apenas uma configuração por ano esteja ativa"""
        if self.ativo:
            # Desativa outras configurações do mesmo ano
            frappe.db.sql("""
                UPDATE `tabIPTU Configuracao` 
                SET ativo = 0 
                WHERE ano = %s AND name != %s AND ativo = 1
            """, (self.ano, self.name))
    
    @staticmethod
    def get_configuracao_ativa(ano=None):
        """Retorna a configuração ativa para o ano especificado"""
        if not ano:
            ano = str(datetime.now().year)
        
        config = frappe.get_value("IPTU Configuracao", 
                                 {"ano": ano, "ativo": 1}, 
                                 "*", as_dict=True)
        
        return config
    
    def calcular_iptu(self, valor_venal, tipo_imovel="Residencial", tem_desconto_idoso=False, 
                     tem_desconto_deficiente=False, pagamento_vista=False, 
                     pagamento_janeiro=False, area_terreno=0, testada_principal=0,
                     possui_pavimentacao=False, imovel_esquina=False, zona_urbana=True):
        """
        Calcula o valor do IPTU baseado na configuração
        
        Args:
            valor_venal (float): Valor venal do imóvel
            tipo_imovel (str): Tipo do imóvel (Residencial, Comercial, Industrial, etc.)
            tem_desconto_idoso (bool): Proprietário é idoso
            tem_desconto_deficiente (bool): Proprietário é deficiente
            pagamento_vista (bool): Pagamento à vista
            pagamento_janeiro (bool): Pagamento em janeiro
            area_terreno (float): Área do terreno em m²
            testada_principal (float): Testada principal em metros
            possui_pavimentacao (bool): Possui pavimentação
            imovel_esquina (bool): Imóvel de esquina
            zona_urbana (bool): Está em zona urbana
        
        Returns:
            dict: Detalhes do cálculo do IPTU
        """
        # Encontra a alíquota aplicável
        aliquota_aplicavel = self.get_aliquota_aplicavel(valor_venal)
        
        if not aliquota_aplicavel:
            frappe.throw("Nenhuma alíquota encontrada para o valor venal informado")
        
        # Calcula o valor base do IPTU
        valor_base = flt(valor_venal) * flt(aliquota_aplicavel.get('aliquota', 0)) / 100
        
        # Aplica fator multiplicador por tipo de imóvel
        if tipo_imovel == "Comercial" and self.fator_multiplicador_comercial:
            valor_base *= flt(self.fator_multiplicador_comercial)
        elif tipo_imovel == "Industrial" and self.fator_multiplicador_industrial:
            valor_base *= flt(self.fator_multiplicador_industrial)
        
        # Ajustes baseados nas características do imóvel
        if self.considerar_testada and testada_principal:
            # Fator baseado na testada (exemplo: +2% para cada 10m de testada)
            fator_testada = 1 + (flt(testada_principal) / 10) * 0.02
            valor_base *= fator_testada
        
        if self.considerar_esquina and imovel_esquina:
            # Imóvel de esquina tem acréscimo de 10%
            valor_base *= 1.10
        
        if self.considerar_pavimentacao and possui_pavimentacao:
            # Imóvel com pavimentação tem acréscimo de 5%
            valor_base *= 1.05
        
        if self.considerar_zona_urbana and not zona_urbana:
            # Imóvel fora da zona urbana tem desconto de 20%
            valor_base *= 0.80
        
        # Garante valor mínimo
        if valor_base < flt(self.valor_minimo_iptu):
            valor_base = flt(self.valor_minimo_iptu)
        
        # Calcula descontos
        total_desconto = 0
        detalhes_desconto = []
        
        if tem_desconto_idoso and self.desconto_idoso:
            desconto_idoso = valor_base * flt(self.desconto_idoso) / 100
            total_desconto += desconto_idoso
            detalhes_desconto.append({
                'tipo': 'Desconto Idoso',
                'percentual': self.desconto_idoso,
                'valor': desconto_idoso
            })
        
        if tem_desconto_deficiente and self.desconto_deficiente:
            desconto_deficiente = valor_base * flt(self.desconto_deficiente) / 100
            total_desconto += desconto_deficiente
            detalhes_desconto.append({
                'tipo': 'Desconto Deficiente',
                'percentual': self.desconto_deficiente,
                'valor': desconto_deficiente
            })
        
        if pagamento_vista and self.desconto_pagamento_vista:
            desconto_vista = valor_base * flt(self.desconto_pagamento_vista) / 100
            total_desconto += desconto_vista
            detalhes_desconto.append({
                'tipo': 'Desconto Pagamento à Vista',
                'percentual': self.desconto_pagamento_vista,
                'valor': desconto_vista
            })
        
        if pagamento_janeiro and self.desconto_pagamento_janeiro:
            desconto_janeiro = valor_base * flt(self.desconto_pagamento_janeiro) / 100
            total_desconto += desconto_janeiro
            detalhes_desconto.append({
                'tipo': 'Desconto Pagamento Janeiro',
                'percentual': self.desconto_pagamento_janeiro,
                'valor': desconto_janeiro
            })
        
        valor_final = valor_base - total_desconto
        
        return {
            'valor_venal': valor_venal,
            'aliquota_aplicada': aliquota_aplicavel.get('aliquota', 0),
            'faixa_valor': f"{aliquota_aplicavel.get('valor_minimo', 0)} a {aliquota_aplicavel.get('valor_maximo', 0)}",
            'valor_base': valor_base,
            'total_desconto': total_desconto,
            'detalhes_desconto': detalhes_desconto,
            'valor_final': valor_final,
            'valor_minimo_aplicado': valor_base == flt(self.valor_minimo_iptu)
        }
    
    def get_aliquota_aplicavel(self, valor_venal):
        """Encontra a alíquota aplicável para o valor venal"""
        valor_venal = flt(valor_venal)
        
        for aliquota in self.aliquotas_progressivas:
            valor_min = flt(aliquota.get('valor_minimo', 0))
            valor_max = flt(aliquota.get('valor_maximo', 999999999))
            
            if valor_min <= valor_venal <= valor_max:
                return aliquota
        
        return None
    
    def calcular_multa_juros(self, valor_original, data_vencimento, data_calculo=None):
        """
        Calcula multa e juros sobre valor em atraso
        
        Args:
            valor_original (float): Valor original do débito
            data_vencimento (str/date): Data de vencimento original
            data_calculo (str/date): Data para cálculo (padrão: hoje)
        
        Returns:
            dict: Detalhes da multa e juros
        """
        if not data_calculo:
            data_calculo = today()
        
        data_vencimento = getdate(data_vencimento)
        data_calculo = getdate(data_calculo)
        
        if data_calculo <= data_vencimento:
            return {
                'valor_original': valor_original,
                'dias_atraso': 0,
                'valor_multa': 0,
                'valor_juros': 0,
                'valor_total': valor_original
            }
        
        dias_atraso = (data_calculo - data_vencimento).days
        
        # Calcula multa se passou do prazo
        valor_multa = 0
        if dias_atraso > flt(self.dias_para_multa):
            valor_multa = flt(valor_original) * flt(self.percentual_multa) / 100
        
        # Calcula juros proporcionais aos meses de atraso
        meses_atraso = dias_atraso / 30.0
        valor_juros = flt(valor_original) * flt(self.percentual_juros_mes) / 100 * meses_atraso
        
        valor_total = flt(valor_original) + valor_multa + valor_juros
        
        return {
            'valor_original': valor_original,
            'dias_atraso': dias_atraso,
            'meses_atraso': meses_atraso,
            'valor_multa': valor_multa,
            'valor_juros': valor_juros,
            'valor_total': valor_total,
            'percentual_multa_aplicado': self.percentual_multa if valor_multa > 0 else 0,
            'percentual_juros_aplicado': self.percentual_juros_mes
        }
    
    def simular_parcelamento(self, valor_total, numero_parcelas=None, valor_entrada=None):
        """
        Simula parcelamento de débito
        
        Args:
            valor_total (float): Valor total a ser parcelado
            numero_parcelas (int): Número de parcelas desejado
            valor_entrada (float): Valor da entrada
        
        Returns:
            dict: Simulação do parcelamento
        """
        if not self.permite_parcelamento:
            frappe.throw("Parcelamento não permitido pela configuração atual")
        
        valor_total = flt(valor_total)
        
        if not numero_parcelas:
            numero_parcelas = self.maximo_parcelas
        
        if numero_parcelas > self.maximo_parcelas:
            frappe.throw(f"Número máximo de parcelas permitido: {self.maximo_parcelas}")
        
        # Calcula entrada mínima
        entrada_minima = valor_total * flt(self.percentual_entrada_minima) / 100
        
        if not valor_entrada:
            valor_entrada = entrada_minima
        
        if valor_entrada < entrada_minima:
            frappe.throw(f"Valor mínimo de entrada: R$ {entrada_minima:.2f}")
        
        # Valor a parcelar
        valor_parcelar = valor_total - flt(valor_entrada)
        
        # Valor da parcela
        valor_parcela = valor_parcelar / numero_parcelas
        
        if valor_parcela < flt(self.valor_minimo_parcela):
            # Recalcula número de parcelas baseado no valor mínimo
            numero_parcelas_max = int(valor_parcelar / flt(self.valor_minimo_parcela))
            if numero_parcelas_max < 1:
                frappe.throw("Valor insuficiente para parcelamento")
            
            numero_parcelas = numero_parcelas_max
            valor_parcela = valor_parcelar / numero_parcelas
        
        # Gera cronograma de parcelas
        parcelas = []
        data_vencimento = add_days(today(), 30)  # Primeira parcela em 30 dias
        
        for i in range(numero_parcelas):
            parcelas.append({
                'numero': i + 1,
                'valor': valor_parcela,
                'data_vencimento': data_vencimento,
                'status': 'Pendente'
            })
            data_vencimento = add_days(data_vencimento, 30)
        
        return {
            'valor_total': valor_total,
            'valor_entrada': valor_entrada,
            'valor_parcelado': valor_parcelar,
            'numero_parcelas': numero_parcelas,
            'valor_parcela': valor_parcela,
            'parcelas': parcelas,
            'entrada_minima_exigida': entrada_minima
        }