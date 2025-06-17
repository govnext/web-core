FROM python:3.10-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    mariadb-client \
    mariadb-server \
    redis-server \
    nodejs \
    npm \
    yarn \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-venv \
    libmariadb-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /home/frappe/frappe-bench

# Instalar bench
RUN pip3 install frappe-bench

# Inicializar bench
RUN bench init --frappe-branch version-14 govnext

# Configurar variáveis de ambiente
ENV FRAPPE_VERSION=14.0.0
ENV ERPNEXT_VERSION=14.0.0
ENV SITE_NAME=site1.localhost
ENV MYSQL_ROOT_PASSWORD=123
ENV ADMIN_PASSWORD=admin

# Instalar ERPNext
RUN bench get-app erpnext --branch version-14

# Instalar GovNext Core
RUN bench get-app govnext_core https://github.com/seu-usuario/govnext_core

# Configurar site
RUN bench new-site $SITE_NAME \
    --mariadb-root-password $MYSQL_ROOT_PASSWORD \
    --admin-password $ADMIN_PASSWORD \
    --install-app erpnext \
    --install-app govnext_core

# Configurar produção
RUN bench set-config -g developer_mode 0
RUN bench set-config -g maintenance_mode 0
RUN bench set-config -g pause_scheduler 0

# Expor portas
EXPOSE 8000
EXPOSE 9000

# Script de inicialização
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"] 