"""
GovNext - Sistema de Integra��es Governamentais
Sistema robusto de integra��es para �rg�os p�blicos com foco em interoperabilidade,
seguran�a e toler�ncia a falhas.

Caracter�sticas principais:
- Conectores para ERPNext
- Integra��es banc�rias (Open Banking Brasil)
- APIs governamentais (SIAPE, SIAFI, IBGE, etc.)
- Sistemas de pagamento (PIX, Boleto, Cart�o)
- ETL e sincroniza��o de dados
- Monitoramento e auditoria completa
"""

from .base import (
    BaseIntegration,
    IntegrationConfig,
    IntegrationResult,
    IntegrationError,
    IntegrationManager
)

from .auth import (
    AuthenticationManager,
    OAuth2Provider,
    CertificateAuthProvider,
    TokenManager
)

from .utils import (
    DataTransformer,
    ValidationUtils,
    CryptoUtils,
    RetryUtils,
    LoggerUtils
)

__version__ = "1.0.0"
__author__ = "GovNext Integration Team"

# Configura��es globais das integra��es
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

# Status codes padronizados
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
STATUS_PENDING = "pending"
STATUS_RETRY = "retry"

# Tipos de integra��o suportados
INTEGRATION_TYPES = {
    "erpnext": "ERPNext Integration",
    "banking": "Banking Integration", 
    "government": "Government API Integration",
    "payment": "Payment System Integration",
    "etl": "ETL Integration"
}

# Configura��es de seguran�a
SECURITY_SETTINGS = {
    "encryption_algorithm": "AES-256-GCM",
    "hash_algorithm": "SHA-256",
    "token_expiry": 3600,  # 1 hora
    "max_auth_attempts": 3,
    "audit_level": "full"
}