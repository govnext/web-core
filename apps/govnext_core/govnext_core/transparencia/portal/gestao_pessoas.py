# -*- coding: utf-8 -*-
"""
Módulo Gestão de Pessoas - Portal da Transparência
Compliance com LAI/LRF - Remuneração anonimizada e estrutura organizacional
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, date_diff, nowdate
import hashlib
import json

def get_context(context):
    """
    Retorna o contexto para a página de Gestão de Pessoas
    Inclui dados anonimizados conforme LGPD
    """
    context.title = _("Gestão de Pessoas")
    context.description = _("Informações sobre remuneração de servidores, estrutura organizacional e quadro de pessoal")
    
    # Filtros disponíveis
    context.filtros = {
        'orgaos': get_orgaos_ativos(),
        'cargos': get_cargos_ativos(),
        'anos': get_anos_disponiveis(),
        'meses': get_meses_disponiveis()
    }
    
    # Dados agregados para dashboard
    context.dashboard = get_dashboard_pessoas()
    
    # Estrutura organizacional
    context.estrutura_organizacional = get_estrutura_organizacional()
    
    # Quadro de pessoal resumido
    context.quadro_pessoal = get_quadro_pessoal_resumido()
    
    # Remuneração por faixa (anonimizada)
    context.remuneracao_faixas = get_remuneracao_por_faixas()
    
    # Configurações de acessibilidade eMAG
    context.emag_config = {
        'skip_links': True,
        'high_contrast': True,
        'keyboard_navigation': True,
        'screen_reader_support': True
    }
    
    return context

def get_orgaos_ativos():
    """Retorna lista de órgãos ativos para filtro"""
    return frappe.db.sql("""
        SELECT DISTINCT orgao_codigo, orgao_nome
        FROM `tabTransparencia Servidor`
        WHERE status = 'Ativo'
        ORDER BY orgao_nome
    """, as_dict=True)

def get_cargos_ativos():
    """Retorna lista de cargos ativos para filtro"""
    return frappe.db.sql("""
        SELECT DISTINCT cargo, COUNT(*) as quantidade
        FROM `tabTransparencia Servidor`
        WHERE status = 'Ativo'
        GROUP BY cargo
        ORDER BY quantidade DESC, cargo
    """, as_dict=True)

def get_anos_disponiveis():
    """Retorna anos disponíveis para consulta"""
    return frappe.db.sql("""
        SELECT DISTINCT YEAR(data_referencia) as ano
        FROM `tabTransparencia Remuneracao`
        ORDER BY ano DESC
    """, as_dict=True)

def get_meses_disponiveis():
    """Retorna meses disponíveis para consulta"""
    meses = [
        {'numero': 1, 'nome': 'Janeiro'},
        {'numero': 2, 'nome': 'Fevereiro'},
        {'numero': 3, 'nome': 'Março'},
        {'numero': 4, 'nome': 'Abril'},
        {'numero': 5, 'nome': 'Maio'},
        {'numero': 6, 'nome': 'Junho'},
        {'numero': 7, 'nome': 'Julho'},
        {'numero': 8, 'nome': 'Agosto'},
        {'numero': 9, 'nome': 'Setembro'},
        {'numero': 10, 'nome': 'Outubro'},
        {'numero': 11, 'nome': 'Novembro'},
        {'numero': 12, 'nome': 'Dezembro'}
    ]
    return meses

def get_dashboard_pessoas():
    """Retorna dados do dashboard de gestão de pessoas"""
    
    # Total de servidores ativos
    total_servidores = frappe.db.count('Transparencia Servidor', {'status': 'Ativo'})
    
    # Total de servidores por tipo
    servidores_por_tipo = frappe.db.sql("""
        SELECT tipo_servidor, COUNT(*) as quantidade
        FROM `tabTransparencia Servidor`
        WHERE status = 'Ativo'
        GROUP BY tipo_servidor
    """, as_dict=True)
    
    # Massa salarial total (último mês)
    massa_salarial = frappe.db.sql("""
        SELECT SUM(valor_bruto) as total
        FROM `tabTransparencia Remuneracao`
        WHERE MONTH(data_referencia) = MONTH(CURDATE())
        AND YEAR(data_referencia) = YEAR(CURDATE())
    """, as_dict=True)
    
    # Média salarial por categoria
    media_por_categoria = frappe.db.sql("""
        SELECT 
            s.categoria,
            AVG(r.valor_bruto) as media_salarial,
            COUNT(DISTINCT s.name) as quantidade_servidores
        FROM `tabTransparencia Servidor` s
        LEFT JOIN `tabTransparencia Remuneracao` r ON s.name = r.servidor
        WHERE s.status = 'Ativo'
        AND MONTH(r.data_referencia) = MONTH(CURDATE())
        AND YEAR(r.data_referencia) = YEAR(CURDATE())
        GROUP BY s.categoria
    """, as_dict=True)
    
    return {
        'total_servidores': total_servidores,
        'servidores_por_tipo': servidores_por_tipo,
        'massa_salarial': massa_salarial[0]['total'] if massa_salarial else 0,
        'media_por_categoria': media_por_categoria
    }

def get_estrutura_organizacional():
    """Retorna estrutura organizacional hierárquica"""
    return frappe.db.sql("""
        SELECT 
            orgao_codigo,
            orgao_nome,
            orgao_superior,
            nivel_hierarquico,
            COUNT(DISTINCT servidor) as total_servidores,
            responsavel_nome,
            responsavel_cargo
        FROM `tabTransparencia Orgao`
        WHERE status = 'Ativo'
        GROUP BY orgao_codigo
        ORDER BY nivel_hierarquico, orgao_nome
    """, as_dict=True)

def get_quadro_pessoal_resumido():
    """Retorna quadro de pessoal resumido por categoria"""
    return frappe.db.sql("""
        SELECT 
            categoria,
            cargo,
            COUNT(*) as quantidade_atual,
            SUM(CASE WHEN genero = 'Feminino' THEN 1 ELSE 0 END) as feminino,
            SUM(CASE WHEN genero = 'Masculino' THEN 1 ELSE 0 END) as masculino,
            AVG(YEAR(CURDATE()) - YEAR(data_nascimento)) as idade_media,
            MIN(data_admissao) as mais_antigo,
            MAX(data_admissao) as mais_recente
        FROM `tabTransparencia Servidor`
        WHERE status = 'Ativo'
        GROUP BY categoria, cargo
        ORDER BY categoria, quantidade_atual DESC
    """, as_dict=True)

def get_remuneracao_por_faixas():
    """
    Retorna remuneração agrupada por faixas salariais
    Dados anonimizados conforme LGPD
    """
    faixas_salariais = [
        {'min': 0, 'max': 2000, 'label': 'Até R$ 2.000'},
        {'min': 2000, 'max': 4000, 'label': 'R$ 2.001 a R$ 4.000'},
        {'min': 4000, 'max': 6000, 'label': 'R$ 4.001 a R$ 6.000'},
        {'min': 6000, 'max': 8000, 'label': 'R$ 6.001 a R$ 8.000'},
        {'min': 8000, 'max': 10000, 'label': 'R$ 8.001 a R$ 10.000'},
        {'min': 10000, 'max': 15000, 'label': 'R$ 10.001 a R$ 15.000'},
        {'min': 15000, 'max': 20000, 'label': 'R$ 15.001 a R$ 20.000'},
        {'min': 20000, 'max': 999999, 'label': 'Acima de R$ 20.000'}
    ]
    
    resultado = []
    for faixa in faixas_salariais:
        dados = frappe.db.sql("""
            SELECT 
                COUNT(*) as quantidade_servidores,
                AVG(r.valor_bruto) as media_bruta,
                AVG(r.valor_liquido) as media_liquida,
                SUM(r.valor_bruto) as total_bruto
            FROM `tabTransparencia Remuneracao` r
            JOIN `tabTransparencia Servidor` s ON r.servidor = s.name
            WHERE r.valor_bruto >= %(min_valor)s 
            AND r.valor_bruto < %(max_valor)s
            AND s.status = 'Ativo'
            AND MONTH(r.data_referencia) = MONTH(CURDATE())
            AND YEAR(r.data_referencia) = YEAR(CURDATE())
        """, {
            'min_valor': faixa['min'],
            'max_valor': faixa['max']
        }, as_dict=True)
        
        if dados and dados[0]['quantidade_servidores'] > 0:
            resultado.append({
                'faixa': faixa['label'],
                'quantidade': dados[0]['quantidade_servidores'],
                'media_bruta': dados[0]['media_bruta'],
                'media_liquida': dados[0]['media_liquida'],
                'total_bruto': dados[0]['total_bruto']
            })
    
    return resultado

@frappe.whitelist()
def get_remuneracao_detalhada(filters=None):
    """
    API para busca detalhada de remuneração
    Retorna dados anonimizados conforme LGPD
    """
    if not filters:
        filters = {}
    
    # Constrói query com filtros
    conditions = ["s.status = 'Ativo'"]
    values = {}
    
    if filters.get('orgao'):
        conditions.append("s.orgao_codigo = %(orgao)s")
        values['orgao'] = filters['orgao']
    
    if filters.get('cargo'):
        conditions.append("s.cargo = %(cargo)s")
        values['cargo'] = filters['cargo']
    
    if filters.get('ano'):
        conditions.append("YEAR(r.data_referencia) = %(ano)s")
        values['ano'] = cint(filters['ano'])
    
    if filters.get('mes'):
        conditions.append("MONTH(r.data_referencia) = %(mes)s")
        values['mes'] = cint(filters['mes'])
    
    where_clause = " AND ".join(conditions)
    
    # Query principal com dados anonimizados
    query = f"""
        SELECT 
            MD5(CONCAT(s.name, s.cpf)) as servidor_hash,
            s.cargo,
            s.categoria,
            s.orgao_nome,
            r.data_referencia,
            r.valor_bruto,
            r.valor_liquido,
            r.valor_descontos,
            r.valor_vantagens,
            CASE 
                WHEN r.valor_bruto <= 2000 THEN 'Faixa 1'
                WHEN r.valor_bruto <= 4000 THEN 'Faixa 2'
                WHEN r.valor_bruto <= 6000 THEN 'Faixa 3'
                WHEN r.valor_bruto <= 8000 THEN 'Faixa 4'
                WHEN r.valor_bruto <= 10000 THEN 'Faixa 5'
                WHEN r.valor_bruto <= 15000 THEN 'Faixa 6'
                WHEN r.valor_bruto <= 20000 THEN 'Faixa 7'
                ELSE 'Faixa 8'
            END as faixa_salarial
        FROM `tabTransparencia Servidor` s
        LEFT JOIN `tabTransparencia Remuneracao` r ON s.name = r.servidor
        WHERE {where_clause}
        ORDER BY r.data_referencia DESC, r.valor_bruto DESC
        LIMIT 1000
    """
    
    return frappe.db.sql(query, values, as_dict=True)

@frappe.whitelist()
def export_dados_pessoas(format_type="csv", filters=None):
    """
    Exporta dados de gestão de pessoas em formato aberto
    Formatos: CSV, JSON, XML, Excel
    """
    if not filters:
        filters = {}
    
    dados = get_remuneracao_detalhada(filters)
    
    if format_type == "json":
        return json.dumps(dados, indent=2, ensure_ascii=False)
    elif format_type == "csv":
        return convert_to_csv(dados)
    elif format_type == "xml":
        return convert_to_xml(dados)
    else:
        return dados

def convert_to_csv(dados):
    """Converte dados para formato CSV"""
    import csv
    import io
    
    output = io.StringIO()
    if dados:
        writer = csv.DictWriter(output, fieldnames=dados[0].keys())
        writer.writeheader()
        writer.writerows(dados)
    
    return output.getvalue()

def convert_to_xml(dados):
    """Converte dados para formato XML"""
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<gestao_pessoas>\n'
    
    for item in dados:
        xml_content += '  <servidor>\n'
        for key, value in item.items():
            xml_content += f'    <{key}>{value}</{key}>\n'
        xml_content += '  </servidor>\n'
    
    xml_content += '</gestao_pessoas>'
    return xml_content

def anonimizar_dados_pessoais(dados):
    """
    Aplica anonimização LGPD aos dados pessoais
    Remove/mascara informações identificáveis
    """
    dados_anonimizados = []
    
    for item in dados:
        item_anonimo = item.copy()
        
        # Remove identificadores diretos
        if 'cpf' in item_anonimo:
            del item_anonimo['cpf']
        if 'nome' in item_anonimo:
            del item_anonimo['nome']
        if 'matricula' in item_anonimo:
            del item_anonimo['matricula']
        
        # Cria hash para identificação não-pessoal
        if 'servidor_id' in item_anonimo:
            item_anonimo['servidor_hash'] = hashlib.md5(
                str(item_anonimo['servidor_id']).encode()
            ).hexdigest()
            del item_anonimo['servidor_id']
        
        dados_anonimizados.append(item_anonimo)
    
    return dados_anonimizados