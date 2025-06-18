#!/bin/bash
# Health check script para GovNext

set -e

# Configurações
TIMEOUT=10
RETRIES=3
SITE_NAME=${SITE_NAME:-govnext.localhost}

# Função para logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] HEALTHCHECK: $1"
}

# Função para testar conectividade HTTP
check_http() {
    local url=$1
    local expected_code=${2:-200}
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_code" ]; then
        return 0
    else
        log "HTTP check failed for $url - Response: $response"
        return 1
    fi
}

# Função para testar conectividade TCP
check_tcp() {
    local host=$1
    local port=$2
    
    if timeout $TIMEOUT bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        return 0
    else
        log "TCP check failed for $host:$port"
        return 1
    fi
}

# Função principal de health check
main() {
    local check_count=0
    local failed_checks=0
    
    log "Starting health check for GovNext"
    
    # 1. Verificar se o processo principal está rodando
    if ! pgrep -f "gunicorn" > /dev/null; then
        log "Gunicorn process not found"
        ((failed_checks++))
    fi
    ((check_count++))
    
    # 2. Verificar endpoint de ping da aplicação
    if ! check_http "http://localhost:8000/api/method/ping"; then
        log "Application ping endpoint failed"
        ((failed_checks++))
    fi
    ((check_count++))
    
    # 3. Verificar endpoint de status da aplicação
    if ! check_http "http://localhost:8000/api/method/frappe.utils.get_site_info"; then
        log "Application status endpoint failed"
        ((failed_checks++))
    fi
    ((check_count++))
    
    # 4. Verificar conectividade com MariaDB (se configurado)
    if [ -n "$MYSQL_HOST" ]; then
        if ! check_tcp "$MYSQL_HOST" "${MYSQL_PORT:-3306}"; then
            log "MariaDB connectivity failed"
            ((failed_checks++))
        fi
        ((check_count++))
    fi
    
    # 5. Verificar conectividade com Redis (se configurado)
    if [ -n "$REDIS_HOST" ]; then
        if ! check_tcp "$REDIS_HOST" "${REDIS_PORT:-6379}"; then
            log "Redis connectivity failed"
            ((failed_checks++))
        fi
        ((check_count++))
    fi
    
    # 6. Verificar espaço em disco
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log "Disk usage critical: ${disk_usage}%"
        ((failed_checks++))
    fi
    ((check_count++))
    
    # 7. Verificar uso de memória
    mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -gt 95 ]; then
        log "Memory usage critical: ${mem_usage}%"
        ((failed_checks++))
    fi
    ((check_count++))
    
    # 8. Verificar se existem arquivos críticos
    critical_files=(
        "/home/frappe/frappe-bench/sites/$SITE_NAME/site_config.json"
        "/home/frappe/frappe-bench/sites/common_site_config.json"
    )
    
    for file in "${critical_files[@]}"; do
        if [ ! -f "$file" ]; then
            log "Critical file missing: $file"
            ((failed_checks++))
        fi
        ((check_count++))
    done
    
    # Resultado final
    log "Health check completed: $failed_checks/$check_count checks failed"
    
    if [ $failed_checks -eq 0 ]; then
        log "Health check PASSED"
        exit 0
    elif [ $failed_checks -le 2 ]; then
        log "Health check WARNING - some non-critical checks failed"
        exit 0
    else
        log "Health check FAILED - critical issues detected"
        exit 1
    fi
}

# Executar com retry
for i in $(seq 1 $RETRIES); do
    log "Health check attempt $i/$RETRIES"
    if main; then
        exit 0
    fi
    
    if [ $i -lt $RETRIES ]; then
        log "Retrying in 5 seconds..."
        sleep 5
    fi
done

log "All health check attempts failed"
exit 1