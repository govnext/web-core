# -*- coding: utf-8 -*-
# Copyright (c) 2023, GovNext Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def login(usr=None, pwd=None):
    """
    Autenticação de usuários para API
    """
    try:
        if not (usr and pwd):
            frappe.throw(_("Usuário e senha são obrigatórios"))

        frappe.local.login_manager.authenticate(usr, pwd)
        frappe.local.login_manager.post_login()

        # Gerar token de acesso
        api_key = frappe.generate_hash(length=32)
        api_secret = frappe.generate_hash(length=32)

        # Salvar token
        user = frappe.get_doc("User", frappe.session.user)
        user.api_key = api_key
        user.api_secret = api_secret
        user.save(ignore_permissions=True)

        return {
            "message": _("Login realizado com sucesso"),
            "user": frappe.session.user,
            "api_key": api_key,
            "api_secret": api_secret
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Login Error")
        return {"error": str(e)}

@frappe.whitelist()
def logout():
    """
    Encerrar sessão de usuário
    """
    try:
        frappe.local.login_manager.logout()
        return {"message": _("Logout realizado com sucesso")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Logout Error")
        return {"error": str(e)}
