# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

"""
Middleware para API v2.0
========================

Camada de middleware para processamento de requisições:
- Rate limiting
- Validação de dados
- Logs de auditoria
- Controle de CORS
- Compressão de respostas
"""

from .rate_limiter import RateLimiter
from .request_validator import RequestValidator
from .cors_handler import CORSHandler
from .audit_logger import AuditLogger

__all__ = ["RateLimiter", "RequestValidator", "CORSHandler", "AuditLogger"]