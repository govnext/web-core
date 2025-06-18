# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

"""
Utilitários para API v2.0
=========================

Ferramentas auxiliares para:
- Formatação de respostas
- Cache Redis
- Validação de dados
- Logging estruturado
- Serialização JSON
"""

from .response_formatter import ResponseFormatter
from .cache_manager import CacheManager
from .data_validator import DataValidator
from .json_encoder import JSONEncoder

__all__ = ["ResponseFormatter", "CacheManager", "DataValidator", "JSONEncoder"]