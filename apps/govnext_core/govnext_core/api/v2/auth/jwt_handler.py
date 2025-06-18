# -*- coding: utf-8 -*-
# Copyright (c) 2024, GovNext Team and contributors
# For license information, please see license.txt

import jwt
import frappe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import hashlib
from frappe import _
from frappe.utils import cint, get_datetime


class JWTHandler:
    """
    Gerenciador de tokens JWT para API v2.0
    
    Funcionalidades:
    - Geração de tokens de acesso e refresh
    - Validação e decodificação de tokens
    - Controle de expiração
    - Blacklist de tokens revogados
    - Refresh automático de tokens
    """
    
    def __init__(self):
        self.secret_key = self._get_secret_key()
        self.algorithm = "HS256"
        self.access_token_expiry = timedelta(hours=1)  # 1 hora
        self.refresh_token_expiry = timedelta(days=30)  # 30 dias
        
    def _get_secret_key(self) -> str:
        """Obtém a chave secreta para assinatura dos tokens"""
        settings = frappe.get_single("System Settings")
        if not settings.jwt_secret_key:
            # Gerar nova chave secreta
            secret = frappe.generate_hash(length=64)
            frappe.db.set_value("System Settings", None, "jwt_secret_key", secret)
            frappe.db.commit()
            return secret
        return settings.jwt_secret_key
    
    def generate_tokens(self, user: str, roles: list = None, permissions: dict = None) -> Dict[str, Any]:
        """
        Gera tokens de acesso e refresh para um usuário
        
        Args:
            user: Email/ID do usuário
            roles: Lista de roles do usuário
            permissions: Dicionário de permissões específicas
            
        Returns:
            Dict contendo access_token, refresh_token e metadados
        """
        try:
            now = datetime.utcnow()
            user_doc = frappe.get_doc("User", user)
            
            if not roles:
                roles = frappe.get_roles(user)
                
            if not permissions:
                permissions = self._get_user_permissions(user)
            
            # Payload do token de acesso
            access_payload = {
                "user": user,
                "user_id": user_doc.name,
                "full_name": user_doc.full_name,
                "roles": roles,
                "permissions": permissions,
                "iat": now,
                "exp": now + self.access_token_expiry,
                "type": "access",
                "jti": frappe.generate_hash(length=16)  # JWT ID único
            }
            
            # Payload do token de refresh
            refresh_payload = {
                "user": user,
                "user_id": user_doc.name,
                "iat": now,
                "exp": now + self.refresh_token_expiry,
                "type": "refresh",
                "jti": frappe.generate_hash(length=16)
            }
            
            # Gerar tokens
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
            
            # Salvar refresh token no banco
            self._store_refresh_token(user, refresh_payload["jti"], refresh_payload["exp"])
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": int(self.access_token_expiry.total_seconds()),
                "expires_at": (now + self.access_token_expiry).isoformat(),
                "user": user,
                "roles": roles
            }
            
        except Exception as e:
            frappe.log_error(f"Erro ao gerar tokens JWT: {str(e)}", "JWT Token Generation Error")
            frappe.throw(_("Erro interno ao gerar tokens de autenticação"))
    
    def validate_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        Valida e decodifica um token JWT
        
        Args:
            token: Token JWT a ser validado
            token_type: Tipo do token (access ou refresh)
            
        Returns:
            Payload decodificado ou None se inválido
        """
        try:
            # Remover prefixo Bearer se presente
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Decodificar token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verificar tipo do token
            if payload.get("type") != token_type:
                frappe.log_error(f"Tipo de token inválido: esperado {token_type}, recebido {payload.get('type')}")
                return None
            
            # Verificar se token está na blacklist
            if self._is_token_blacklisted(payload.get("jti")):
                frappe.log_error(f"Token na blacklist: {payload.get('jti')}")
                return None
            
            # Verificar se refresh token ainda existe no banco
            if token_type == "refresh":
                if not self._is_refresh_token_valid(payload.get("user"), payload.get("jti")):
                    frappe.log_error(f"Refresh token não encontrado no banco: {payload.get('jti')}")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            frappe.log_error("Token JWT expirado", "JWT Validation Error")
            return None
        except jwt.InvalidTokenError as e:
            frappe.log_error(f"Token JWT inválido: {str(e)}", "JWT Validation Error")
            return None
        except Exception as e:
            frappe.log_error(f"Erro ao validar token JWT: {str(e)}", "JWT Validation Error")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Gera novo token de acesso usando refresh token
        
        Args:
            refresh_token: Token de refresh válido
            
        Returns:
            Novo token de acesso ou None se inválido
        """
        try:
            # Validar refresh token
            payload = self.validate_token(refresh_token, "refresh")
            if not payload:
                return None
            
            user = payload.get("user")
            roles = frappe.get_roles(user)
            permissions = self._get_user_permissions(user)
            
            # Gerar apenas novo access token
            now = datetime.utcnow()
            access_payload = {
                "user": user,
                "user_id": payload.get("user_id"),
                "full_name": frappe.get_value("User", user, "full_name"),
                "roles": roles,
                "permissions": permissions,
                "iat": now,
                "exp": now + self.access_token_expiry,
                "type": "access",
                "jti": frappe.generate_hash(length=16)
            }
            
            access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
            
            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": int(self.access_token_expiry.total_seconds()),
                "expires_at": (now + self.access_token_expiry).isoformat(),
                "user": user,
                "roles": roles
            }
            
        except Exception as e:
            frappe.log_error(f"Erro ao renovar token: {str(e)}", "JWT Refresh Error")
            return None
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoga um token adicionando-o à blacklist
        
        Args:
            token: Token a ser revogado
            
        Returns:
            True se revogado com sucesso
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti:
                self._add_to_blacklist(jti, exp)
                
                # Se for refresh token, remover do banco
                if payload.get("type") == "refresh":
                    self._remove_refresh_token(payload.get("user"), jti)
                
                return True
                
        except Exception as e:
            frappe.log_error(f"Erro ao revogar token: {str(e)}", "JWT Revoke Error")
            
        return False
    
    def _get_user_permissions(self, user: str) -> Dict[str, Any]:
        """Obtém permissões específicas do usuário"""
        try:
            permissions = {}
            
            # Permissões de doctypes
            for doctype in ["User", "Company", "Accounts Settings", "System Settings"]:
                perms = frappe.get_user_permissions(user).get(doctype, [])
                if perms:
                    permissions[doctype] = [p.get("doc") for p in perms]
            
            # Permissões personalizadas para módulos governamentais
            gov_permissions = frappe.get_all(
                "User Permission",
                filters={"user": user, "allow": ["in", ["Transparencia", "Financeiro", "Licitacao"]]},
                fields=["allow", "for_value"]
            )
            
            for perm in gov_permissions:
                if perm.allow not in permissions:
                    permissions[perm.allow] = []
                permissions[perm.allow].append(perm.for_value)
            
            return permissions
            
        except Exception:
            return {}
    
    def _store_refresh_token(self, user: str, jti: str, exp: datetime):
        """Armazena refresh token no banco"""
        try:
            # Remover tokens expirados do usuário
            frappe.db.delete("JWT Refresh Token", {"user": user, "expires_at": ["<", get_datetime()]})
            
            # Inserir novo refresh token
            frappe.get_doc({
                "doctype": "JWT Refresh Token",
                "user": user,
                "jti": jti,
                "expires_at": exp,
                "created_at": datetime.utcnow()
            }).insert(ignore_permissions=True)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Erro ao armazenar refresh token: {str(e)}")
    
    def _is_refresh_token_valid(self, user: str, jti: str) -> bool:
        """Verifica se refresh token existe e é válido"""
        try:
            return frappe.db.exists("JWT Refresh Token", {
                "user": user,
                "jti": jti,
                "expires_at": [">", get_datetime()]
            })
        except Exception:
            return False
    
    def _remove_refresh_token(self, user: str, jti: str):
        """Remove refresh token do banco"""
        try:
            frappe.db.delete("JWT Refresh Token", {"user": user, "jti": jti})
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Erro ao remover refresh token: {str(e)}")
    
    def _add_to_blacklist(self, jti: str, exp: int):
        """Adiciona token à blacklist"""
        try:
            exp_datetime = datetime.fromtimestamp(exp)
            
            frappe.get_doc({
                "doctype": "JWT Blacklist",
                "jti": jti,
                "expires_at": exp_datetime,
                "blacklisted_at": datetime.utcnow()
            }).insert(ignore_permissions=True)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Erro ao adicionar à blacklist: {str(e)}")
    
    def _is_token_blacklisted(self, jti: str) -> bool:
        """Verifica se token está na blacklist"""
        try:
            return frappe.db.exists("JWT Blacklist", {
                "jti": jti,
                "expires_at": [">", get_datetime()]
            })
        except Exception:
            return False
    
    def cleanup_expired_tokens(self):
        """Remove tokens expirados do banco"""
        try:
            now = get_datetime()
            
            # Remover refresh tokens expirados
            frappe.db.delete("JWT Refresh Token", {"expires_at": ["<", now]})
            
            # Remover tokens da blacklist expirados
            frappe.db.delete("JWT Blacklist", {"expires_at": ["<", now]})
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Erro na limpeza de tokens: {str(e)}")


# Instância global do handler JWT
jwt_handler = JWTHandler()