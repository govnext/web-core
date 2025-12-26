"""
Sistema de autenticação para integrações do GovNext.
Suporte a múltiplos métodos de autenticação incluindo OAuth2,
certificados digitais, tokens JWT e autenticação básica.
"""

import jwt
import base64
import hashlib
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cint

from .base import IntegrationError, IntegrationResult


@dataclass
class AuthToken:
    """Representação de um token de autenticação"""
    token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def is_expired(self) -> bool:
        """Verifica se o token está expirado"""
        if not self.expires_at:
            return False
        return now_datetime() >= self.expires_at
    
    def time_to_expiry(self) -> Optional[int]:
        """Retorna segundos até expiração"""
        if not self.expires_at:
            return None
        delta = self.expires_at - now_datetime()
        return max(0, int(delta.total_seconds()))


class BaseAuthProvider(ABC):
    """Classe base para provedores de autenticação"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "")
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    def authenticate(self) -> AuthToken:
        """Executa processo de autenticação"""
        pass
    
    @abstractmethod
    def refresh_token(self, token: AuthToken) -> AuthToken:
        """Renova token de autenticação"""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> bool:
        """Valida se token é válido"""
        pass
    
    def get_auth_headers(self, token: AuthToken) -> Dict[str, str]:
        """Retorna headers de autenticação"""
        return {
            "Authorization": f"{token.token_type} {token.token}"
        }


class OAuth2Provider(BaseAuthProvider):
    """Provedor OAuth2 para APIs governamentais e bancárias"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.token_url = config.get("token_url")
        self.scope = config.get("scope", "")
        self.grant_type = config.get("grant_type", "client_credentials")
    
    def authenticate(self) -> AuthToken:
        """Executa fluxo OAuth2 client_credentials"""
        try:
            import requests
            
            auth_data = {
                "grant_type": self.grant_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            if self.scope:
                auth_data["scope"] = self.scope
            
            response = requests.post(
                self.token_url,
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise IntegrationError(
                    f"Falha na autenticação OAuth2: {response.status_code}",
                    "OAUTH2_AUTH_FAILED"
                )
            
            token_data = response.json()
            
            expires_at = None
            if "expires_in" in token_data:
                expires_at = now_datetime() + timedelta(seconds=token_data["expires_in"])
            
            return AuthToken(
                token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=expires_at,
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope"),
                metadata=token_data
            )
            
        except Exception as e:
            raise IntegrationError(f"Erro na autenticação OAuth2: {str(e)}", "OAUTH2_ERROR")
    
    def refresh_token(self, token: AuthToken) -> AuthToken:
        """Renova token OAuth2"""
        if not token.refresh_token:
            return self.authenticate()  # Re-autentica se não tem refresh token
        
        try:
            import requests
            
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = requests.post(
                self.token_url,
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code != 200:
                return self.authenticate()  # Re-autentica se refresh falhou
            
            token_data = response.json()
            
            expires_at = None
            if "expires_in" in token_data:
                expires_at = now_datetime() + timedelta(seconds=token_data["expires_in"])
            
            return AuthToken(
                token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=expires_at,
                refresh_token=token_data.get("refresh_token", token.refresh_token),
                scope=token_data.get("scope"),
                metadata=token_data
            )
            
        except Exception as e:
            raise IntegrationError(f"Erro no refresh OAuth2: {str(e)}", "OAUTH2_REFRESH_ERROR")
    
    def validate_token(self, token: str) -> bool:
        """Valida token OAuth2 (implementação básica)"""
        return bool(token and len(token) > 10)


class CertificateAuthProvider(BaseAuthProvider):
    """Provedor de autenticação por certificado digital (A1/A3)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cert_path = config.get("cert_path")
        self.key_path = config.get("key_path")
        self.cert_password = config.get("cert_password")
        self.ca_cert_path = config.get("ca_cert_path")
    
    def authenticate(self) -> AuthToken:
        """Cria token baseado em certificado digital"""
        try:
            # Carrega certificado e chave privada
            with open(self.cert_path, 'rb') as cert_file:
                cert_data = cert_file.read()
            
            with open(self.key_path, 'rb') as key_file:
                key_data = key_file.read()
            
            # Cria um token JWT assinado com a chave privada
            payload = {
                "iss": self.name,
                "sub": "certificate_auth",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            }
            
            private_key = load_pem_private_key(
                key_data,
                password=self.cert_password.encode() if self.cert_password else None
            )
            
            token = jwt.encode(payload, private_key, algorithm="RS256")
            
            return AuthToken(
                token=token,
                token_type="Certificate",
                expires_at=now_datetime() + timedelta(hours=1),
                metadata={
                    "auth_type": "certificate",
                    "cert_path": self.cert_path
                }
            )
            
        except Exception as e:
            raise IntegrationError(f"Erro na autenticação por certificado: {str(e)}", "CERT_AUTH_ERROR")
    
    def refresh_token(self, token: AuthToken) -> AuthToken:
        """Gera novo token de certificado"""
        return self.authenticate()
    
    def validate_token(self, token: str) -> bool:
        """Valida token JWT do certificado"""
        try:
            jwt.decode(token, options={"verify_signature": False})
            return True
        except:
            return False
    
    def get_auth_headers(self, token: AuthToken) -> Dict[str, str]:
        """Headers específicos para autenticação por certificado"""
        return {
            "Authorization": f"{token.token_type} {token.token}",
            "X-Certificate-Auth": "true"
        }


class TokenManager:
    """Gerenciador centralizado de tokens de autenticação"""
    
    def __init__(self):
        self.tokens: Dict[str, AuthToken] = {}
        self.providers: Dict[str, BaseAuthProvider] = {}
    
    def register_provider(self, name: str, provider: BaseAuthProvider):
        """Registra um provedor de autenticação"""
        self.providers[name] = provider
    
    def get_token(self, provider_name: str, force_refresh: bool = False) -> AuthToken:
        """Obtém token válido, renovando se necessário"""
        if provider_name not in self.providers:
            raise IntegrationError(f"Provedor não encontrado: {provider_name}", "PROVIDER_NOT_FOUND")
        
        provider = self.providers[provider_name]
        existing_token = self.tokens.get(provider_name)
        
        # Se não tem token ou forçou refresh ou token expirado
        if not existing_token or force_refresh or existing_token.is_expired():
            if existing_token and not existing_token.is_expired() and not force_refresh:
                return existing_token
            
            # Tenta renovar token existente primeiro
            if existing_token and existing_token.refresh_token and not force_refresh:
                try:
                    new_token = provider.refresh_token(existing_token)
                    self.tokens[provider_name] = new_token
                    return new_token
                except:
                    pass  # Se falhou, vai autenticar do zero
            
            # Autentica do zero
            new_token = provider.authenticate()
            self.tokens[provider_name] = new_token
            
            # Salva token de forma segura no cache do Frappe
            self._cache_token(provider_name, new_token)
            
            return new_token
        
        return existing_token
    
    def invalidate_token(self, provider_name: str):
        """Invalida token de um provedor"""
        if provider_name in self.tokens:
            del self.tokens[provider_name]
        
        # Remove do cache
        frappe.cache().delete_key(f"auth_token_{provider_name}")
    
    def get_auth_headers(self, provider_name: str) -> Dict[str, str]:
        """Obtém headers de autenticação para um provedor"""
        token = self.get_token(provider_name)
        provider = self.providers[provider_name]
        return provider.get_auth_headers(token)
    
    def _cache_token(self, provider_name: str, token: AuthToken):
        """Armazena token no cache de forma segura"""
        # Só salva no cache se não for sensível demais
        if token.metadata and token.metadata.get("cache_enabled", True):
            cache_data = {
                "token": token.token,
                "token_type": token.token_type,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                "scope": token.scope
            }
            
            # Cache por tempo menor que expiração do token
            ttl = token.time_to_expiry()
            if ttl:
                ttl = min(ttl, 1800)  # Máximo 30 minutos
            else:
                ttl = 1800
            
            frappe.cache().set_value(
                f"auth_token_{provider_name}",
                cache_data,
                expires_in_sec=ttl
            )


class AuthenticationManager:
    """Gerenciador principal do sistema de autenticação"""
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.setup_default_providers()
    
    def setup_default_providers(self):
        """Configura provedores padrão baseado nas configurações do sistema"""
        # OAuth2 para Open Banking
        if frappe.get_conf().get("open_banking_enabled"):
            oauth_config = frappe.get_conf().get("open_banking_oauth", {})
            if oauth_config:
                provider = OAuth2Provider(oauth_config)
                self.token_manager.register_provider("open_banking", provider)
        
        # Certificado A1/A3 para sistemas governamentais
        if frappe.get_conf().get("certificate_auth_enabled"):
            cert_config = frappe.get_conf().get("certificate_auth", {})
            if cert_config:
                provider = CertificateAuthProvider(cert_config)
                self.token_manager.register_provider("government_cert", provider)
    
    def authenticate(self, provider_name: str) -> IntegrationResult:
        """Executa autenticação para um provedor"""
        try:
            token = self.token_manager.get_token(provider_name)
            
            return IntegrationResult(
                success=True,
                data={
                    "provider": provider_name,
                    "token_type": token.token_type,
                    "expires_at": token.expires_at,
                    "scope": token.scope
                }
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="AUTH_FAILED"
            )
    
    def get_auth_headers(self, provider_name: str) -> Dict[str, str]:
        """Obtém headers de autenticação"""
        return self.token_manager.get_auth_headers(provider_name)
    
    def test_authentication(self, provider_name: str) -> IntegrationResult:
        """Testa autenticação de um provedor"""
        try:
            token = self.token_manager.get_token(provider_name, force_refresh=True)
            
            return IntegrationResult(
                success=True,
                data={
                    "provider": provider_name,
                    "authenticated": True,
                    "token_valid": not token.is_expired(),
                    "expires_in": token.time_to_expiry()
                }
            )
            
        except Exception as e:
            return IntegrationResult(
                success=False,
                error_message=str(e),
                error_code="AUTH_TEST_FAILED"
            )


# Instância global do gerenciador de autenticação
auth_manager = AuthenticationManager()