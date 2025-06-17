import frappe
from frappe import _

def after_install():
    """
    Setup GovNext after installation:
    - Create Custom Roles
    - Set default modules
    """
    create_custom_roles()
    setup_modules()
    frappe.msgprint(_("GovNext Core has been installed successfully!"))

def create_custom_roles():
    """Create custom roles specific to government administration"""
    roles = [
        "Gestor Público",
        "Secretário",
        "Servidor Público",
        "Auditor",
        "Contador Público",
        "Tesoureiro",
        "Gestor de Contratos",
        "Gestor de Licitações",
        "Administrador de Patrimônio",
        "Gestor de Recursos Humanos"
    ]

    for role in roles:
        if not frappe.db.exists("Role", role):
            role_doc = frappe.new_doc("Role")
            role_doc.role_name = role
            role_doc.desk_access = 1
            role_doc.save()

def setup_modules():
    """Configure default modules for GovNext"""
    modules = [
        {
            "module_name": "GovNext",
            "color": "#3498db",
            "icon": "octicon octicon-organization",
            "type": "module",
            "label": _("GovNext")
        },
        {
            "module_name": "Orçamento",
            "color": "#1abc9c",
            "icon": "octicon octicon-graph",
            "type": "module",
            "label": _("Orçamento")
        },
        {
            "module_name": "Contratos",
            "color": "#9b59b6",
            "icon": "octicon octicon-file-submodule",
            "type": "module",
            "label": _("Contratos")
        },
        {
            "module_name": "Licitações",
            "color": "#f39c12",
            "icon": "octicon octicon-checklist",
            "type": "module",
            "label": _("Licitações")
        },
        {
            "module_name": "Patrimônio Público",
            "color": "#2ecc71",
            "icon": "octicon octicon-database",
            "type": "module",
            "label": _("Patrimônio Público")
        },
        {
            "module_name": "Servidores",
            "color": "#e74c3c",
            "icon": "octicon octicon-person",
            "type": "module",
            "label": _("Servidores")
        }
    ]

    for module in modules:
        if not frappe.db.exists("Desktop Icon", {"module_name": module["module_name"]}):
            desk_icon = frappe.new_doc("Desktop Icon")
            desk_icon.update(module)
            desk_icon.insert(ignore_permissions=True)
