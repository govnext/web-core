# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

"""
GovNext API v2.0
================

API REST robusta para integração com sistemas governamentais.

Características:
- Autenticação JWT
- Rate limiting
- Versionamento de API
- Documentação Swagger/OpenAPI
- Cache Redis
- Validação de dados
- Logs estruturados
"""

__version__ = "2.0.0"
__author__ = "GovNext Team"

from .auth.jwt_handler import JWTHandler
from .middleware.rate_limiter import RateLimiter
from .middleware.request_validator import RequestValidator
from .utils.response_formatter import ResponseFormatter
from .utils.cache_manager import CacheManager

__all__ = [
    "JWTHandler",
    "RateLimiter", 
    "RequestValidator",
    "ResponseFormatter",
    "CacheManager"
]