#!/bin/bash
# Entrypoint script para GovNext Production

set -e

# Configurações
FRAPPE_USER=${FRAPPE_USER:-frappe}
BENCH_PATH=${BENCH_PATH:-/home/frappe/frappe-bench}
SITE_NAME=${SITE_NAME:-govnext.localhost}

# Função para logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ENTRYPOINT: $1"
}

# Função para aguardar serviços
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_wait=${4:-60}
    
    log "Waiting for $service_name at $host:$port..."
    
    for i in $(seq 1 $max_wait); do
        if nc -z "$host" "$port" 2>/dev/null; then
            log "$service_name is ready!"
            return 0
        fi
        
        log "Waiting for $service_name... ($i/$max_wait)"
        sleep 1
    done
    
    log "ERROR: $service_name is not available after ${max_wait}s"
    return 1
}

# Função para setup inicial
setup_environment() {
    log "Setting up GovNext environment..."
    
    # Criar diretórios necessários
    mkdir -p "$BENCH_PATH/logs"
    mkdir -p "$BENCH_PATH/sites/$SITE_NAME"
    mkdir -p "$BENCH_PATH/sites/assets"
    
    # Definir permissões
    chown -R $FRAPPE_USER:$FRAPPE_USER "$BENCH_PATH"
    
    # Configurar variáveis de ambiente
    export PYTHONPATH="$BENCH_PATH/apps:$PYTHONPATH"
    export PATH="$BENCH_PATH/env/bin:$PATH"
    
    cd "$BENCH_PATH"
}

# Função para aguardar dependências
wait_for_dependencies() {
    log "Checking dependencies..."
    
    # Aguardar MariaDB
    if [ -n "$MYSQL_HOST" ]; then
        wait_for_service "$MYSQL_HOST" "${MYSQL_PORT:-3306}" "MariaDB" 120
    fi
    
    # Aguardar Redis
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis" 60
    fi
}

# Função para inicializar site
initialize_site() {
    log "Initializing site: $SITE_NAME"
    
    cd "$BENCH_PATH"
    
    # Verificar se o site já existe
    if [ ! -f "sites/$SITE_NAME/site_config.json" ]; then
        log "Creating new site: $SITE_NAME"
        
        # Criar site
        bench new-site "$SITE_NAME" \
            --admin-password "${ADMIN_PASSWORD:-admin}" \
            --mariadb-root-password "${MYSQL_ROOT_PASSWORD}" \
            --install-app erpnext \
            --install-app govnext_core \
            --force
            
        # Configurar site para produção
        bench --site "$SITE_NAME" set-config developer_mode 0
        bench --site "$SITE_NAME" set-config maintenance_mode 0
        bench --site "$SITE_NAME" set-config pause_scheduler 0
        
        # Configurar cache
        if [ -n "$REDIS_HOST" ]; then
            bench --site "$SITE_NAME" set-config redis_cache "redis://$REDIS_HOST:${REDIS_PORT:-6379}"
            bench --site "$SITE_NAME" set-config redis_queue "redis://$REDIS_HOST:${REDIS_PORT:-6379}"
            bench --site "$SITE_NAME" set-config redis_socketio "redis://$REDIS_HOST:${REDIS_PORT:-6379}"
        fi
        
        # Configurar chaves de segurança
        if [ -n "$SECRET_KEY" ]; then
            bench --site "$SITE_NAME" set-config encryption_key "$SECRET_KEY"
        fi
        
        if [ -n "$JWT_SECRET_KEY" ]; then
            bench --site "$SITE_NAME" set-config jwt_secret_key "$JWT_SECRET_KEY"
        fi
        
        log "Site $SITE_NAME created successfully"
    else
        log "Site $SITE_NAME already exists, running migrations..."
        
        # Executar migrações
        bench --site "$SITE_NAME" migrate
        
        # Limpar cache
        bench --site "$SITE_NAME" clear-cache
        bench --site "$SITE_NAME" clear-website-cache
    fi
}

# Função para configurar SSL
setup_ssl() {
    if [ -f "/etc/nginx/ssl/govnext.crt" ] && [ -f "/etc/nginx/ssl/govnext.key" ]; then
        log "SSL certificates found, enabling HTTPS"
        # SSL já configurado no nginx
    else
        log "No SSL certificates found, running HTTP only"
    fi
}

# Função para iniciar serviços
start_services() {
    log "Starting GovNext services..."
    
    cd "$BENCH_PATH"
    
    # Configurar supervisor
    if [ -f "/etc/supervisor/conf.d/frappe-bench.conf" ]; then
        log "Starting with supervisor..."
        supervisord -c /etc/supervisor/supervisord.conf
    else
        # Determinar tipo de processo baseado em variáveis de ambiente
        case "${WORKER_TYPE:-app}" in
            "worker")
                log "Starting as background worker..."
                exec gosu $FRAPPE_USER bench worker --queue default,short,long
                ;;
            "scheduler")
                log "Starting as scheduler..."
                exec gosu $FRAPPE_USER bench schedule
                ;;
            "app"|*)
                log "Starting as web application..."
                
                # Construir assets se necessário
                if [ ! -d "sites/assets/js" ] || [ ! -d "sites/assets/css" ]; then
                    log "Building assets..."
                    bench build --apps govnext_core
                fi
                
                # Iniciar aplicação
                exec gosu $FRAPPE_USER bench start \
                    --bind 0.0.0.0 \
                    --port 8000 \
                    --workers 4 \
                    --timeout 120 \
                    --keep-alive 2 \
                    --max-requests 1000 \
                    --max-requests-jitter 100 \
                    --preload
                ;;
        esac
    fi
}

# Função para limpeza antes de sair
cleanup() {
    log "Performing cleanup..."
    
    # Parar processos do bench
    if pgrep -f "bench" > /dev/null; then
        pkill -f "bench" || true
    fi
    
    # Parar supervisor
    if pgrep supervisord > /dev/null; then
        supervisorctl shutdown || true
    fi
    
    log "Cleanup completed"
}

# Configurar trap para limpeza
trap cleanup SIGTERM SIGINT

# Função principal
main() {
    log "Starting GovNext container..."
    log "Environment: ${INSTANCE_TYPE:-production}"
    log "Site: $SITE_NAME"
    log "Worker type: ${WORKER_TYPE:-app}"
    
    # Executar setup
    setup_environment
    wait_for_dependencies
    
    # Inicializar apenas se for o container principal
    if [ "${WORKER_TYPE:-app}" = "app" ]; then
        initialize_site
        setup_ssl
    fi
    
    # Iniciar serviços
    start_services
}

# Verificar se está executando como root
if [ "$(id -u)" = "0" ]; then
    log "Running as root, installing gosu..."
    
    # Instalar gosu se não existir
    if ! command -v gosu >/dev/null 2>&1; then
        apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*
    fi
    
    # Executar como usuário frappe
    exec gosu $FRAPPE_USER "$0" "$@"
fi

# Executar função principal
main "$@"