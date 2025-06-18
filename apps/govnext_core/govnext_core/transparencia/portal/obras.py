# -*- coding: utf-8 -*-
"""
Módulo Obras Públicas - Portal da Transparência
Compliance com LAI/LRF - Cronograma físico-financeiro e georreferenciamento
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, date_diff, nowdate, get_datetime
import json
import math

def get_context(context):
    """
    Retorna o contexto para a página de Obras Públicas
    Inclui cronograma físico-financeiro e dados georreferenciados
    """
    context.title = _("Obras Públicas")
    context.description = _("Acompanhe obras públicas em andamento com cronograma físico-financeiro e localização georreferenciada")
    
    # Filtros disponíveis
    context.filtros = {
        'situacoes': get_situacoes_obras(),
        'tipos_obra': get_tipos_obra(),
        'secretarias': get_secretarias_responsaveis(),
        'anos': get_anos_execucao(),
        'faixas_valor': get_faixas_valor_obras()
    }
    
    # Dashboard de obras
    context.dashboard = get_dashboard_obras()
    
    # Obras em destaque (maior valor ou impacto)
    context.obras_destaque = get_obras_destaque()
    
    # Obras por região/bairro
    context.obras_por_regiao = get_obras_por_regiao()
    
    # Indicadores de execução
    context.indicadores_execucao = get_indicadores_execucao()
    
    # Mapa de obras (dados georreferenciados)
    context.mapa_obras = get_dados_mapa_obras()
    
    # Configurações de acessibilidade eMAG
    context.emag_config = {
        'skip_links': True,
        'high_contrast': True,
        'keyboard_navigation': True,
        'screen_reader_support': True,
        'alt_text_maps': True
    }
    
    return context

def get_situacoes_obras():
    """Retorna situações possíveis das obras"""
    return [
        {'codigo': 'planejamento', 'nome': 'Em Planejamento'},
        {'codigo': 'licitacao', 'nome': 'Em Licitação'},
        {'codigo': 'contratacao', 'nome': 'Em Contratação'},
        {'codigo': 'execucao', 'nome': 'Em Execução'},
        {'codigo': 'paralisada', 'nome': 'Paralisada'},
        {'codigo': 'concluida', 'nome': 'Concluída'},
        {'codigo': 'cancelada', 'nome': 'Cancelada'}
    ]

def get_tipos_obra():
    """Retorna tipos de obras disponíveis"""
    return frappe.db.sql("""
        SELECT DISTINCT tipo_obra, COUNT(*) as quantidade
        FROM `tabTransparencia Obra`
        GROUP BY tipo_obra
        ORDER BY quantidade DESC, tipo_obra
    """, as_dict=True)

def get_secretarias_responsaveis():
    """Retorna secretarias responsáveis pelas obras"""
    return frappe.db.sql("""
        SELECT DISTINCT secretaria_responsavel, COUNT(*) as total_obras
        FROM `tabTransparencia Obra`
        GROUP BY secretaria_responsavel
        ORDER BY total_obras DESC, secretaria_responsavel
    """, as_dict=True)

def get_anos_execucao():
    """Retorna anos de execução disponíveis"""
    return frappe.db.sql("""
        SELECT DISTINCT YEAR(data_inicio) as ano
        FROM `tabTransparencia Obra`
        WHERE data_inicio IS NOT NULL
        UNION
        SELECT DISTINCT YEAR(data_previsao_conclusao) as ano
        FROM `tabTransparencia Obra`
        WHERE data_previsao_conclusao IS NOT NULL
        ORDER BY ano DESC
    """, as_dict=True)

def get_faixas_valor_obras():
    """Retorna faixas de valor das obras"""
    return [
        {'min': 0, 'max': 100000, 'label': 'Até R$ 100 mil'},
        {'min': 100000, 'max': 500000, 'label': 'R$ 100 mil a R$ 500 mil'},
        {'min': 500000, 'max': 1000000, 'label': 'R$ 500 mil a R$ 1 milhão'},
        {'min': 1000000, 'max': 5000000, 'label': 'R$ 1 milhão a R$ 5 milhões'},
        {'min': 5000000, 'max': 10000000, 'label': 'R$ 5 milhões a R$ 10 milhões'},
        {'min': 10000000, 'max': 999999999, 'label': 'Acima de R$ 10 milhões'}
    ]

def get_dashboard_obras():
    """Retorna dados do dashboard de obras"""
    
    # Total de obras por situação
    obras_por_situacao = frappe.db.sql("""
        SELECT situacao, COUNT(*) as quantidade
        FROM `tabTransparencia Obra`
        GROUP BY situacao
    """, as_dict=True)
    
    # Valor total investido
    valor_total = frappe.db.sql("""
        SELECT 
            SUM(valor_contratado) as total_contratado,
            SUM(valor_executado) as total_executado,
            COUNT(*) as total_obras
        FROM `tabTransparencia Obra`
    """, as_dict=True)
    
    # Obras em execução
    em_execucao = frappe.db.sql("""
        SELECT COUNT(*) as quantidade
        FROM `tabTransparencia Obra`
        WHERE situacao = 'execucao'
    """, as_dict=True)
    
    # Percentual médio de execução
    percentual_medio = frappe.db.sql("""
        SELECT AVG(percentual_executado) as media_execucao
        FROM `tabTransparencia Obra`
        WHERE situacao IN ('execucao', 'concluida')
    """, as_dict=True)
    
    # Obras com atraso
    obras_atrasadas = frappe.db.sql("""
        SELECT COUNT(*) as quantidade
        FROM `tabTransparencia Obra`
        WHERE situacao = 'execucao'
        AND data_previsao_conclusao < CURDATE()
    """, as_dict=True)
    
    return {
        'obras_por_situacao': obras_por_situacao,
        'valor_total_contratado': valor_total[0]['total_contratado'] if valor_total else 0,
        'valor_total_executado': valor_total[0]['total_executado'] if valor_total else 0,
        'total_obras': valor_total[0]['total_obras'] if valor_total else 0,
        'em_execucao': em_execucao[0]['quantidade'] if em_execucao else 0,
        'percentual_medio': percentual_medio[0]['media_execucao'] if percentual_medio else 0,
        'obras_atrasadas': obras_atrasadas[0]['quantidade'] if obras_atrasadas else 0
    }

def get_obras_destaque():
    """Retorna obras em destaque (maior valor ou impacto)"""
    return frappe.db.sql("""
        SELECT 
            codigo_obra,
            nome_obra,
            descricao,
            tipo_obra,
            situacao,
            valor_contratado,
            valor_executado,
            percentual_executado,
            data_inicio,
            data_previsao_conclusao,
            secretaria_responsavel,
            empresa_contratada,
            latitude,
            longitude,
            endereco_completo,
            bairro,
            impacto_social,
            beneficiarios_estimados
        FROM `tabTransparencia Obra`
        WHERE situacao IN ('execucao', 'concluida')
        ORDER BY valor_contratado DESC, impacto_social DESC
        LIMIT 6
    """, as_dict=True)

def get_obras_por_regiao():
    """Retorna distribuição de obras por região/bairro"""
    return frappe.db.sql("""
        SELECT 
            bairro,
            regiao,
            COUNT(*) as total_obras,
            SUM(valor_contratado) as valor_total,
            AVG(percentual_executado) as percentual_medio,
            COUNT(CASE WHEN situacao = 'concluida' THEN 1 END) as concluidas,
            COUNT(CASE WHEN situacao = 'execucao' THEN 1 END) as em_execucao
        FROM `tabTransparencia Obra`
        WHERE bairro IS NOT NULL
        GROUP BY bairro, regiao
        ORDER BY valor_total DESC, total_obras DESC
    """, as_dict=True)

def get_indicadores_execucao():
    """Retorna indicadores de execução das obras"""
    
    # Obras dentro do prazo vs atrasadas
    prazo_execucao = frappe.db.sql("""
        SELECT 
            COUNT(CASE WHEN data_previsao_conclusao >= CURDATE() OR situacao = 'concluida' THEN 1 END) as no_prazo,
            COUNT(CASE WHEN data_previsao_conclusao < CURDATE() AND situacao != 'concluida' THEN 1 END) as atrasadas,
            COUNT(*) as total
        FROM `tabTransparencia Obra`
        WHERE situacao IN ('execucao', 'concluida')
    """, as_dict=True)
    
    # Execução financeira vs física
    execucao_comparativa = frappe.db.sql("""
        SELECT 
            AVG(percentual_executado) as media_fisica,
            AVG((valor_executado / valor_contratado) * 100) as media_financeira,
            COUNT(CASE WHEN percentual_executado > (valor_executado / valor_contratado) * 100 THEN 1 END) as fisica_maior,
            COUNT(CASE WHEN percentual_executado < (valor_executado / valor_contratado) * 100 THEN 1 END) as financeira_maior
        FROM `tabTransparencia Obra`
        WHERE valor_contratado > 0 AND situacao IN ('execucao', 'concluida')
    """, as_dict=True)
    
    # Distribuição por faixa de execução
    faixas_execucao = frappe.db.sql("""
        SELECT 
            CASE 
                WHEN percentual_executado < 25 THEN '0-25%'
                WHEN percentual_executado < 50 THEN '25-50%'
                WHEN percentual_executado < 75 THEN '50-75%'
                WHEN percentual_executado < 100 THEN '75-99%'
                ELSE '100%'
            END as faixa_execucao,
            COUNT(*) as quantidade
        FROM `tabTransparencia Obra`
        WHERE situacao IN ('execucao', 'concluida')
        GROUP BY faixa_execucao
        ORDER BY faixa_execucao
    """, as_dict=True)
    
    return {
        'prazo_execucao': prazo_execucao[0] if prazo_execucao else None,
        'execucao_comparativa': execucao_comparativa[0] if execucao_comparativa else None,
        'faixas_execucao': faixas_execucao
    }

def get_dados_mapa_obras():
    """Retorna dados georreferenciados para o mapa de obras"""
    obras_geolocalizadas = frappe.db.sql("""
        SELECT 
            codigo_obra,
            nome_obra,
            tipo_obra,
            situacao,
            valor_contratado,
            percentual_executado,
            latitude,
            longitude,
            endereco_completo,
            bairro,
            data_inicio,
            data_previsao_conclusao,
            secretaria_responsavel,
            CASE 
                WHEN situacao = 'concluida' THEN '#28a745'
                WHEN situacao = 'execucao' THEN '#007bff'
                WHEN situacao = 'paralisada' THEN '#dc3545'
                WHEN situacao = 'licitacao' THEN '#ffc107'
                ELSE '#6c757d'
            END as cor_marcador
        FROM `tabTransparencia Obra`
        WHERE latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND latitude != 0 
        AND longitude != 0
        ORDER BY valor_contratado DESC
    """, as_dict=True)
    
    # Calcular centro do mapa baseado nas obras
    if obras_geolocalizadas:
        lat_media = sum(float(obra['latitude']) for obra in obras_geolocalizadas) / len(obras_geolocalizadas)
        lng_media = sum(float(obra['longitude']) for obra in obras_geolocalizadas) / len(obras_geolocalizadas)
    else:
        lat_media, lng_media = -15.7942, -47.8822  # Brasília como padrão
    
    return {
        'obras': obras_geolocalizadas,
        'centro_mapa': {'lat': lat_media, 'lng': lng_media},
        'total_georreferenciadas': len(obras_geolocalizadas)
    }

@frappe.whitelist()
def get_cronograma_obra(codigo_obra):
    """Retorna cronograma físico-financeiro detalhado de uma obra"""
    
    # Dados básicos da obra
    obra = frappe.db.get_value('Transparencia Obra', 
        {'codigo_obra': codigo_obra}, 
        ['*'], as_dict=True)
    
    if not obra:
        return None
    
    # Cronograma físico-financeiro
    cronograma = frappe.db.sql("""
        SELECT 
            etapa,
            descricao_etapa,
            data_inicio_prevista,
            data_fim_prevista,
            data_inicio_real,
            data_fim_real,
            percentual_previsto,
            percentual_executado,
            valor_previsto,
            valor_executado,
            situacao_etapa,
            responsavel_etapa,
            observacoes
        FROM `tabTransparencia Obra Cronograma`
        WHERE obra = %(obra)s
        ORDER BY etapa
    """, {'obra': codigo_obra}, as_dict=True)
    
    # Medições realizadas
    medicoes = frappe.db.sql("""
        SELECT 
            data_medicao,
            percentual_fisico,
            valor_medido,
            valor_aprovado,
            observacoes_medicao,
            responsavel_medicao
        FROM `tabTransparencia Obra Medicao`
        WHERE obra = %(obra)s
        ORDER BY data_medicao DESC
    """, {'obra': codigo_obra}, as_dict=True)
    
    # Aditivos contratuais
    aditivos = frappe.db.sql("""
        SELECT 
            numero_aditivo,
            tipo_aditivo,
            data_aditivo,
            valor_aditivo,
            prazo_adicional_dias,
            justificativa,
            situacao_aditivo
        FROM `tabTransparencia Obra Aditivo`
        WHERE obra = %(obra)s
        ORDER BY data_aditivo DESC
    """, {'obra': codigo_obra}, as_dict=True)
    
    # Fotos da obra (para acompanhamento visual)
    fotos = frappe.db.sql("""
        SELECT 
            data_foto,
            descricao_foto,
            arquivo_foto,
            etapa_obra
        FROM `tabTransparencia Obra Foto`
        WHERE obra = %(obra)s
        ORDER BY data_foto DESC
        LIMIT 20
    """, {'obra': codigo_obra}, as_dict=True)
    
    return {
        'obra': obra,
        'cronograma': cronograma,
        'medicoes': medicoes,
        'aditivos': aditivos,
        'fotos': fotos
    }

@frappe.whitelist()
def get_obras_filtradas(filters=None):
    """
    API para busca filtrada de obras
    Retorna obras conforme filtros aplicados
    """
    if not filters:
        filters = {}
    
    # Constrói query com filtros
    conditions = ["1=1"]
    values = {}
    
    if filters.get('situacao'):
        conditions.append("situacao = %(situacao)s")
        values['situacao'] = filters['situacao']
    
    if filters.get('tipo_obra'):
        conditions.append("tipo_obra = %(tipo_obra)s")
        values['tipo_obra'] = filters['tipo_obra']
    
    if filters.get('secretaria'):
        conditions.append("secretaria_responsavel = %(secretaria)s")
        values['secretaria'] = filters['secretaria']
    
    if filters.get('ano'):
        conditions.append("YEAR(data_inicio) = %(ano)s OR YEAR(data_previsao_conclusao) = %(ano)s")
        values['ano'] = cint(filters['ano'])
    
    if filters.get('valor_min') and filters.get('valor_max'):
        conditions.append("valor_contratado BETWEEN %(valor_min)s AND %(valor_max)s")
        values['valor_min'] = flt(filters['valor_min'])
        values['valor_max'] = flt(filters['valor_max'])
    
    if filters.get('bairro'):
        conditions.append("bairro LIKE %(bairro)s")
        values['bairro'] = f"%{filters['bairro']}%"
    
    where_clause = " AND ".join(conditions)
    
    # Query principal
    query = f"""
        SELECT 
            codigo_obra,
            nome_obra,
            descricao,
            tipo_obra,
            situacao,
            valor_contratado,
            valor_executado,
            percentual_executado,
            data_inicio,
            data_previsao_conclusao,
            data_conclusao_real,
            secretaria_responsavel,
            empresa_contratada,
            endereco_completo,
            bairro,
            regiao,
            latitude,
            longitude,
            impacto_social,
            beneficiarios_estimados,
            CASE 
                WHEN data_previsao_conclusao < CURDATE() AND situacao != 'concluida' THEN 'Atrasada'
                ELSE 'No Prazo'
            END as status_prazo,
            DATEDIFF(COALESCE(data_conclusao_real, data_previsao_conclusao), data_inicio) as prazo_total_dias,
            (valor_executado / valor_contratado) * 100 as percentual_financeiro
        FROM `tabTransparencia Obra`
        WHERE {where_clause}
        ORDER BY valor_contratado DESC, data_inicio DESC
        LIMIT 500
    """
    
    return frappe.db.sql(query, values, as_dict=True)

@frappe.whitelist()
def export_dados_obras(format_type="csv", filters=None):
    """
    Exporta dados de obras em formato aberto
    Formatos: CSV, JSON, XML, Excel, KML (para dados geográficos)
    """
    if not filters:
        filters = {}
    
    dados = get_obras_filtradas(filters)
    
    if format_type == "json":
        return json.dumps(dados, indent=2, ensure_ascii=False, default=str)
    elif format_type == "csv":
        return convert_to_csv(dados)
    elif format_type == "xml":
        return convert_to_xml(dados)
    elif format_type == "kml":
        return convert_to_kml(dados)
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
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<obras_publicas>\n'
    
    for obra in dados:
        xml_content += '  <obra>\n'
        for key, value in obra.items():
            xml_content += f'    <{key}>{value}</{key}>\n'
        xml_content += '  </obra>\n'
    
    xml_content += '</obras_publicas>'
    return xml_content

def convert_to_kml(dados):
    """Converte dados para formato KML (Google Earth)"""
    kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Obras Públicas</name>
    <description>Localização das obras públicas municipais</description>
    
    <Style id="obra-execucao">
      <IconStyle>
        <color>ffff0000</color>
        <scale>1.0</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/construction.png</href>
        </Icon>
      </IconStyle>
    </Style>
    
    <Style id="obra-concluida">
      <IconStyle>
        <color>ff00ff00</color>
        <scale>1.0</scale>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/check-circle.png</href>
        </Icon>
      </IconStyle>
    </Style>
'''
    
    for obra in dados:
        if obra.get('latitude') and obra.get('longitude'):
            style_id = "obra-concluida" if obra['situacao'] == 'concluida' else "obra-execucao"
            
            kml_content += f'''
    <Placemark>
      <name>{obra['nome_obra']}</name>
      <description><![CDATA[
        <b>Tipo:</b> {obra['tipo_obra']}<br/>
        <b>Situação:</b> {obra['situacao']}<br/>
        <b>Valor:</b> R$ {obra['valor_contratado']:,.2f}<br/>
        <b>Execução:</b> {obra['percentual_executado']:.1f}%<br/>
        <b>Endereço:</b> {obra['endereco_completo']}<br/>
        <b>Responsável:</b> {obra['secretaria_responsavel']}
      ]]></description>
      <styleUrl>#{style_id}</styleUrl>
      <Point>
        <coordinates>{obra['longitude']},{obra['latitude']},0</coordinates>
      </Point>
    </Placemark>'''
    
    kml_content += '''
  </Document>
</kml>'''
    
    return kml_content

def calcular_distancia_obras(lat1, lon1, lat2, lon2):
    """
    Calcula distância entre duas coordenadas usando fórmula de Haversine
    Útil para agrupar obras por proximidade
    """
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c