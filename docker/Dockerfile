# Multi-stage build para otimização de produção
FROM node:18-alpine AS node-builder

# Instalar dependências frontend
WORKDIR /tmp/frontend
COPY apps/govnext_core/govnext_core/public ./public/
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Stage de build Python
FROM python:3.10-slim AS python-builder

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libmariadb-dev \
    libssl-dev \
    libffi-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências Python
COPY apps/govnext_core/requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Instalar Frappe
RUN pip install --no-cache-dir frappe-bench

# Stage de produção
FROM python:3.10-slim AS production

# Criar usuário não-root
RUN groupadd -g 1000 frappe && \
    useradd -u 1000 -g frappe -m -s /bin/bash frappe

# Instalar dependências runtime apenas
RUN apt-get update && apt-get install -y \
    mariadb-client \
    curl \
    nginx \
    supervisor \
    redis-tools \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar ambiente virtual
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar assets do frontend
COPY --from=node-builder /tmp/frontend/public /home/frappe/frappe-bench/sites/assets/

# Configurar diretório de trabalho
WORKDIR /home/frappe/frappe-bench

# Copiar aplicação
COPY --chown=frappe:frappe apps/ ./apps/
COPY --chown=frappe:frappe sites/ ./sites/

# Copiar configurações
COPY --chown=frappe:frappe config/nginx/ /etc/nginx/conf.d/
COPY --chown=frappe:frappe config/supervisor/ /etc/supervisor/conf.d/

# Scripts e configurações
COPY docker/entrypoint.sh /usr/local/bin/
COPY docker/healthcheck.sh /usr/local/bin/
COPY docker/setup-site.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/healthcheck.sh \
    && chmod +x /usr/local/bin/setup-site.sh

# Configurar variáveis de ambiente
ENV FRAPPE_VERSION=14.0.0 \
    PYTHONPATH=/home/frappe/frappe-bench/apps \
    PATH="/opt/venv/bin:$PATH" \
    FRAPPE_USER=frappe \
    BENCH_PATH=/home/frappe/frappe-bench

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Expor portas
EXPOSE 8000 9000 80

# Mudar para usuário não-root
USER frappe

# Ponto de entrada
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]