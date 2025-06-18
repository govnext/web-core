# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

"""
Módulo de Autenticação API v2.0
===============================

Implementa autenticação JWT robusta com:
- Tokens de acesso e refresh
- Validação de permissões
- Controle de expiração
- Blacklist de tokens
"""

from .jwt_handler import JWTHandler
from .permissions import PermissionChecker
from .token_manager import TokenManager

__all__ = ["JWTHandler", "PermissionChecker", "TokenManager"]