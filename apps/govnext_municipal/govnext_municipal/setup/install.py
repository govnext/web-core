import frappe
from frappe import _

def after_install():
    """
    Setup GovNext Municipal after installation:
    - Create custom municipal roles
    - Setup municipal doctypes
    - Configure municipal modules
    """
    create_municipal_roles()
    setup_municipal_modules()
    create_municipal_doctypes()
    frappe.msgprint(_("GovNext Municipal has been installed successfully!"))

def create_municipal_roles():
    """Create custom roles specific to municipal administration"""
    roles = [
        "Prefeito",
        "Vice-Prefeito",
        "Secretário Municipal",
        "Vereador",
        "Procurador Municipal",
        "Auditor Municipal",
        "Contador Municipal",
        "Fiscal Municipal",
        "Agente Administrativo"
    ]

    for role in roles:
        if not frappe.db.exists("Role", role):
            role_doc = frappe.new_doc("Role")
            role_doc.role_name = role
            role_doc.desk_access = 1
            role_doc.save()

def setup_municipal_modules():
    """Configure modules specific to municipal government"""
    modules = [
        {
            "module_name": "IPTU",
            "color": "#1abc9c",
            "icon": "octicon octicon-home",
            "type": "module",
            "label": _("IPTU")
        },
        {
            "module_name": "ISS",
            "color": "#3498db",
            "icon": "octicon octicon-server",
            "type": "module",
            "label": _("ISS")
        },
        {
            "module_name": "Obras Municipais",
            "color": "#f39c12",
            "icon": "octicon octicon-tools",
            "type": "module",
            "label": _("Obras Municipais")
        },
        {
            "module_name": "Serviços Municipais",
            "color": "#2ecc71",
            "icon": "octicon octicon-pulse",
            "type": "module",
            "label": _("Serviços Municipais")
        },
        {
            "module_name": "Saúde Municipal",
            "color": "#e74c3c",
            "icon": "octicon octicon-heart",
            "type": "module",
            "label": _("Saúde Municipal")
        },
        {
            "module_name": "Educação Municipal",
            "color": "#9b59b6",
            "icon": "octicon octicon-mortar-board",
            "type": "module",
            "label": _("Educação Municipal")
        }
    ]

    for module in modules:
        if not frappe.db.exists("Desktop Icon", {"module_name": module["module_name"]}):
            desk_icon = frappe.new_doc("Desktop Icon")
            desk_icon.update(module)
            desk_icon.insert(ignore_permissions=True)

def create_municipal_doctypes():
    """Create custom doctypes for municipal management"""
    # This is a placeholder for the actual creation of custom doctypes
    # In a real implementation, you would create or import custom doctypes here
    pass
