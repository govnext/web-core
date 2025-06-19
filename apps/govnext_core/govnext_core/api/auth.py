# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
import jwt
import qrcode
from io import BytesIO
import base64
import pyotp
import hashlib
import time
from datetime import datetime, timedelta
import requests
import ldap3
from functools import wraps

class GovNextAuth:
    """
    Sistema de Autenticação Governamental Avançado
    """
    
    def __init__(self):
        self.secret_key = frappe.conf.get('jwt_secret_key', frappe.generate_hash(length=64))
        self.token_expiry = frappe.conf.get('jwt_token_expiry', 24 * 60 * 60)  # 24 horas
        
    def validate_jwt_token(self, token):
        """Valida token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            frappe.throw(_("Token expirado"))
        except jwt.InvalidTokenError:
            frappe.throw(_("Token inválido"))
    
    def create_jwt_token(self, user, permissions=None):
        """Cria token JWT com permissões"""
        now = datetime.utcnow()
        payload = {
            'user': user,
            'iat': now,
            'exp': now + timedelta(seconds=self.token_expiry),
            'permissions': permissions or [],
            'gov_level': self.get_user_government_level(user)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def get_user_government_level(self, user):
        """Determina nível governamental do usuário"""
        user_doc = frappe.get_doc("User", user)
        
        # Verifica roles para determinar nível
        roles = [r.role for r in user_doc.roles]
        
        if "Federal Administrator" in roles:
            return "federal"
        elif "State Administrator" in roles:
            return "estadual"
        elif "Municipal Administrator" in roles:
            return "municipal"
        else:
            return "basic"

gov_auth = GovNextAuth()

def require_auth(f):
    """Decorator para exigir autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = frappe.request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            frappe.throw(_("Token de autenticação necessário"))
        
        payload = gov_auth.validate_jwt_token(token)
        frappe.local.current_user = payload['user']
        frappe.local.user_permissions = payload.get('permissions', [])
        
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission):
    """Decorator para exigir permissão específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if permission not in frappe.local.get('user_permissions', []):
                frappe.throw(_("Permissão insuficiente: {0}").format(permission))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@frappe.whitelist(allow_guest=True)
def login(usr=None, pwd=None, mfa_token=None):
    """
    Autenticação de usuários para API com MFA
    """
    try:
        # Log da tentativa de login
        log_security_event("LOGIN_ATTEMPT", usr, {"ip": frappe.local.request_ip})
        
        if not (usr and pwd):
            frappe.throw(_("Usuário e senha são obrigatórios"))

        # Verificar se usuário existe e está ativo
        user_doc = frappe.get_doc("User", usr)
        if not user_doc.enabled:
            frappe.throw(_("Usuário desabilitado"))
        
        # Verificar tentativas de login falhas
        if is_user_locked(usr):
            frappe.throw(_("Usuário bloqueado por muitas tentativas inválidas"))

        # Autenticação principal
        frappe.local.login_manager.authenticate(usr, pwd)
        
        # Verificar se MFA está habilitado
        if user_doc.get("mfa_enabled") and not mfa_token:
            return {
                "message": _("MFA necessário"),
                "mfa_required": True,
                "temp_token": create_temp_token(usr)
            }
        
        # Validar MFA se fornecido
        if user_doc.get("mfa_enabled") and mfa_token:
            if not validate_mfa_token(usr, mfa_token):
                increment_failed_attempts(usr)
                frappe.throw(_("Token MFA inválido"))
        
        frappe.local.login_manager.post_login()
        
        # Obter permissões do usuário
        permissions = get_user_permissions(usr)
        
        # Gerar tokens JWT
        access_token = gov_auth.create_jwt_token(usr, permissions)
        refresh_token = create_refresh_token(usr)
        
        # Salvar sessão
        save_user_session(usr, access_token, refresh_token)
        
        # Reset failed attempts
        reset_failed_attempts(usr)
        
        # Log de sucesso
        log_security_event("LOGIN_SUCCESS", usr, {"ip": frappe.local.request_ip})
        
        return {
            "message": _("Login realizado com sucesso"),
            "user": usr,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "permissions": permissions,
            "expires_in": gov_auth.token_expiry
        }
        
    except Exception as e:
        increment_failed_attempts(usr)
        log_security_event("LOGIN_FAILED", usr, {"error": str(e), "ip": frappe.local.request_ip})
        frappe.log_error(frappe.get_traceback(), "API Login Error")
        return {"error": str(e)}

@frappe.whitelist()
def logout():
    """
    Encerrar sessão de usuário
    """
    try:
        user = frappe.session.user
        token = frappe.request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Invalidar tokens
        invalidate_user_tokens(user, token)
        
        frappe.local.login_manager.logout()
        
        # Log de logout
        log_security_event("LOGOUT", user, {"ip": frappe.local.request_ip})
        
        return {"message": _("Logout realizado com sucesso")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Logout Error")
        return {"error": str(e)}

@frappe.whitelist(allow_guest=True)
def sso_login(provider=None, token=None):
    """
    Login via Single Sign-On
    """
    try:
        if not provider:
            frappe.throw(_("Provedor SSO necessário"))
        
        # Validar token SSO baseado no provedor
        user_info = validate_sso_token(provider, token)
        
        if not user_info:
            frappe.throw(_("Token SSO inválido"))
        
        # Criar ou atualizar usuário
        user = create_or_update_sso_user(user_info, provider)
        
        # Gerar tokens
        permissions = get_user_permissions(user)
        access_token = gov_auth.create_jwt_token(user, permissions)
        refresh_token = create_refresh_token(user)
        
        # Log de SSO
        log_security_event("SSO_LOGIN", user, {"provider": provider, "ip": frappe.local.request_ip})
        
        return {
            "message": _("Login SSO realizado com sucesso"),
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "permissions": permissions
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "SSO Login Error")
        return {"error": str(e)}

@frappe.whitelist()
def setup_mfa():
    """
    Configurar MFA para usuário
    """
    try:
        user = frappe.session.user
        secret = pyotp.random_base32()
        
        # Salvar secret temporário
        frappe.db.set_value("User", user, "mfa_secret_temp", secret)
        
        # Gerar QR Code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user,
            issuer_name="GovNext"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer)
        qr_code = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "manual_entry_key": secret
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MFA Setup Error")
        return {"error": str(e)}

@frappe.whitelist()
def verify_mfa_setup(token):
    """
    Verificar configuração MFA
    """
    try:
        user = frappe.session.user
        secret = frappe.db.get_value("User", user, "mfa_secret_temp")
        
        if not secret:
            frappe.throw(_("Setup MFA não iniciado"))
        
        totp = pyotp.TOTP(secret)
        if totp.verify(token):
            # Confirmar MFA
            frappe.db.set_value("User", user, {
                "mfa_enabled": 1,
                "mfa_secret": secret,
                "mfa_secret_temp": ""
            })
            
            log_security_event("MFA_ENABLED", user, {"ip": frappe.local.request_ip})
            
            return {"message": _("MFA configurado com sucesso")}
        else:
            frappe.throw(_("Token MFA inválido"))
            
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MFA Verification Error")
        return {"error": str(e)}

@frappe.whitelist(allow_guest=True)
def ldap_login(username, password, domain=None):
    """
    Autenticação via AD/LDAP
    """
    try:
        ldap_settings = get_ldap_settings(domain)
        
        # Conectar ao servidor LDAP
        server = ldap3.Server(ldap_settings['server'], get_info=ldap3.ALL)
        conn = ldap3.Connection(
            server,
            user=f"{ldap_settings['domain']}\\{username}",
            password=password,
            auto_bind=True
        )
        
        # Buscar informações do usuário
        search_filter = f"(sAMAccountName={username})"
        conn.search(ldap_settings['base_dn'], search_filter, attributes=['*'])
        
        if not conn.entries:
            frappe.throw(_("Usuário não encontrado no AD/LDAP"))
        
        user_info = conn.entries[0]
        
        # Criar ou atualizar usuário no sistema
        user = create_or_update_ldap_user(user_info, domain)
        
        # Gerar tokens
        permissions = get_user_permissions(user)
        access_token = gov_auth.create_jwt_token(user, permissions)
        
        log_security_event("LDAP_LOGIN", user, {"domain": domain, "ip": frappe.local.request_ip})
        
        return {
            "message": _("Login LDAP realizado com sucesso"),
            "user": user,
            "access_token": access_token,
            "permissions": permissions
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "LDAP Login Error")
        return {"error": str(e)}

# Funções auxiliares
def log_security_event(event_type, user, details=None):
    """Log de eventos de segurança"""
    try:
        frappe.get_doc({
            "doctype": "Security Log",
            "event_type": event_type,
            "user": user,
            "timestamp": frappe.utils.now(),
            "ip_address": frappe.local.request_ip,
            "details": json.dumps(details or {})
        }).insert(ignore_permissions=True)
    except:
        pass

def is_user_locked(user):
    """Verifica se usuário está bloqueado"""
    failed_attempts = frappe.cache().get(f"failed_attempts_{user}", 0)
    return failed_attempts >= 5

def increment_failed_attempts(user):
    """Incrementa tentativas de login falhadas"""
    key = f"failed_attempts_{user}"
    attempts = frappe.cache().get(key, 0) + 1
    frappe.cache().set(key, attempts, expires_in_sec=3600)  # 1 hora

def reset_failed_attempts(user):
    """Reset tentativas de login falhadas"""
    frappe.cache().delete(f"failed_attempts_{user}")

def validate_mfa_token(user, token):
    """Valida token MFA"""
    secret = frappe.db.get_value("User", user, "mfa_secret")
    if not secret:
        return False
    
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

def create_temp_token(user):
    """Cria token temporário para MFA"""
    payload = {
        'user': user,
        'temp': True,
        'exp': datetime.utcnow() + timedelta(minutes=5)
    }
    return jwt.encode(payload, gov_auth.secret_key, algorithm='HS256')

def create_refresh_token(user):
    """Cria refresh token"""
    payload = {
        'user': user,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, gov_auth.secret_key, algorithm='HS256')

def get_user_permissions(user):
    """Obter todas as permissões do usuário"""
    roles = frappe.get_roles(user)
    permissions = []
    
    for role in roles:
        role_permissions = frappe.get_all(
            "Role Permission",
            filters={"role": role},
            fields=["document_type", "read", "write", "create", "delete"]
        )
        permissions.extend(role_permissions)
    
    return permissions

def save_user_session(user, access_token, refresh_token):
    """Salvar sessão do usuário"""
    session_data = {
        "user": user,
        "access_token": hashlib.sha256(access_token.encode()).hexdigest(),
        "refresh_token": hashlib.sha256(refresh_token.encode()).hexdigest(),
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(seconds=gov_auth.token_expiry)
    }
    
    frappe.cache().set(f"session_{user}", session_data, expires_in_sec=gov_auth.token_expiry)

def invalidate_user_tokens(user, token=None):
    """Invalidar tokens do usuário"""
    frappe.cache().delete(f"session_{user}")
    if token:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        frappe.cache().set(f"blacklist_{token_hash}", True, expires_in_sec=gov_auth.token_expiry)

def validate_sso_token(provider, token):
    """Validar token SSO"""
    # Implementar validação específica por provedor
    if provider == "google":
        return validate_google_token(token)
    elif provider == "azure":
        return validate_azure_token(token)
    elif provider == "saml":
        return validate_saml_token(token)
    
    return None

def validate_google_token(token):
    """Validar token Google"""
    try:
        response = requests.get(f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={token}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def validate_azure_token(token):
    """Validar token Azure AD"""
    # Implementar validação Azure AD
    pass

def validate_saml_token(token):
    """Validar token SAML"""
    # Implementar validação SAML
    pass

def create_or_update_sso_user(user_info, provider):
    """Criar ou atualizar usuário SSO"""
    email = user_info.get('email')
    if not email:
        frappe.throw(_("Email não fornecido pelo provedor SSO"))
    
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        user.sso_provider = provider
        user.save(ignore_permissions=True)
    else:
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": user_info.get('given_name', ''),
            "last_name": user_info.get('family_name', ''),
            "sso_provider": provider,
            "enabled": 1
        })
        user.insert(ignore_permissions=True)
    
    return user.name

def create_or_update_ldap_user(user_info, domain):
    """Criar ou atualizar usuário LDAP"""
    username = str(user_info.sAMAccountName)
    email = str(user_info.mail) if user_info.mail else f"{username}@{domain}"
    
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
        user.ldap_domain = domain
        user.save(ignore_permissions=True)
    else:
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "username": username,
            "first_name": str(user_info.givenName) if user_info.givenName else username,
            "last_name": str(user_info.sn) if user_info.sn else "",
            "ldap_domain": domain,
            "enabled": 1
        })
        user.insert(ignore_permissions=True)
    
    return user.name

def get_ldap_settings(domain):
    """Obter configurações LDAP"""
    # Buscar configurações do domínio específico
    settings = frappe.get_single("LDAP Settings")
    
    return {
        "server": settings.get("ldap_server"),
        "domain": domain or settings.get("default_domain"),
        "base_dn": settings.get("base_dn")
    }
