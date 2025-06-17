#!/bin/bash

# Iniciar serviços
service mariadb start
service redis-server start

# Configurar bench
cd /home/frappe/frappe-bench

# Iniciar bench
bench start 