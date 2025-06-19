# -*- coding: utf-8 -*-
from . import __version__ as app_version

app_name = "govnext_core"
app_title = "GovNext Core"
app_publisher = "GovNext Team"
app_description = "Sistema de Gestão Governamental"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@govnext.com.br"
app_license = "AGPL"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/govnext_core/css/govnext_core.css",
    "/assets/govnext_core/css/government.css"
]

app_include_js = [
    "/assets/govnext_core/js/govnext_core.js",
    "/assets/govnext_core/js/government_utils.js"
]

# include js, css files in header of web template
web_include_css = [
    "/assets/govnext_core/css/transparencia.css",
    "/assets/govnext_core/css/public_portal.css"
]

web_include_js = [
    "/assets/govnext_core/js/transparencia.js",
    "/assets/govnext_core/js/public_portal.js"
]

# include custom scss in every website theme (without file extension ".scss")
website_theme_scss = "govnext_core/public/scss/government"

# include js, css files in header of web form
webform_include_js = {
    "Government Form": "public/js/government_form.js",
    "Public Request": "public/js/public_request.js"
}

webform_include_css = {
    "Government Form": "public/css/government_form.css"
}

# include js in page
page_js = {
    "transparency-dashboard": "public/js/transparency_dashboard.js",
    "budget-overview": "public/js/budget_overview.js",
    "tender-portal": "public/js/tender_portal.js"
}

# include js in doctype views
doctype_js = {
    "Government Unit": "public/js/government_unit.js",
    "Public Budget": "public/js/public_budget.js",
    "Public Tender": "public/js/public_tender.js",
    "User": "public/js/user_extensions.js"
}

doctype_list_js = {
    "Government Unit": "public/js/government_unit_list.js",
    "Public Budget": "public/js/public_budget_list.js",
    "Public Tender": "public/js/public_tender_list.js"
}

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "government_dashboard"

# website user home page (by Role)
role_home_page = {
    "Federal Administrator": "federal_dashboard",
    "State Administrator": "state_dashboard", 
    "Municipal Administrator": "municipal_dashboard",
    "Public User": "transparency_portal"
}

# Generators
# ----------

# automatically create page for each record of this doctype
website_generators = [
    "Public Budget",
    "Public Tender",
    "Government Unit"
]

# Fixtures
# ----------
fixtures = [
    "Custom Field", 
    "Custom Script",
    "Print Format",
    "Letter Head",
    "Email Template",
    "Role",
    "Permission"
]

# Installation
# ------------

before_install = "govnext_core.setup.install.before_install"
after_install = "govnext_core.setup.install.after_install"

# Uninstallation
# ------------

before_uninstall = "govnext_core.setup.install.before_uninstall"
after_uninstall = "govnext_core.setup.install.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

before_app_install = "govnext_core.setup.install.before_app_install"
after_app_install = "govnext_core.setup.install.after_app_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

notification_config = "govnext_core.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
    "Government Unit": "govnext_core.governo.permissions.get_government_unit_permission_query_conditions",
    "Public Budget": "govnext_core.financeiro.permissions.get_public_budget_permission_query_conditions",
    "Public Tender": "govnext_core.licitacao.permissions.get_public_tender_permission_query_conditions",
}

has_permission = {
    "Government Unit": "govnext_core.governo.permissions.has_government_unit_permission",
    "Public Budget": "govnext_core.financeiro.permissions.has_public_budget_permission",
    "Public Tender": "govnext_core.licitacao.permissions.has_public_tender_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "User": "govnext_core.overrides.CustomUser"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "*": {
        "before_insert": "govnext_core.utils.audit.audit_document_change",
        "after_insert": "govnext_core.utils.audit.audit_document_change",
        "before_save": "govnext_core.utils.audit.audit_document_change",
        "after_save": "govnext_core.utils.audit.audit_document_change",
        "before_cancel": "govnext_core.utils.audit.audit_document_change",
        "after_cancel": "govnext_core.utils.audit.audit_document_change",
        "before_delete": "govnext_core.utils.audit.audit_document_change",
        "after_delete": "govnext_core.utils.audit.audit_document_change",
        "on_update": "govnext_core.hooks_functions.invalidate_cache_on_update"
    },
    "User": {
        "after_insert": "govnext_core.hooks_functions.setup_user_permissions",
        "on_update": "govnext_core.hooks_functions.update_user_cache",
        "validate": "govnext_core.hooks_functions.validate_user_government_data"
    },
    "Government Unit": {
        "on_update": "govnext_core.hooks_functions.invalidate_government_cache",
        "validate": "govnext_core.hooks_functions.validate_government_unit"
    },
    "Public Budget": {
        "on_update": "govnext_core.hooks_functions.invalidate_budget_cache",
        "validate": "govnext_core.hooks_functions.validate_public_budget",
        "on_submit": "govnext_core.hooks_functions.on_budget_submit"
    },
    "Public Tender": {
        "on_update": "govnext_core.hooks_functions.invalidate_tender_cache",
        "validate": "govnext_core.hooks_functions.validate_public_tender",
        "on_submit": "govnext_core.hooks_functions.on_tender_submit"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "all": [
        "govnext_core.tasks.all.ping_external_services",
        "govnext_core.tasks.all.cleanup_expired_sessions"
    ],
    "daily": [
        "govnext_core.tasks.daily.generate_daily_reports",
        "govnext_core.tasks.daily.backup_audit_logs",
        "govnext_core.tasks.daily.cleanup_old_cache",
        "govnext_core.tasks.daily.send_transparency_notifications"
    ],
    "hourly": [
        "govnext_core.tasks.hourly.sync_external_data",
        "govnext_core.tasks.hourly.update_tender_statuses",
        "govnext_core.tasks.hourly.warm_up_cache"
    ],
    "weekly": [
        "govnext_core.tasks.weekly.generate_compliance_reports",
        "govnext_core.tasks.weekly.audit_system_integrity"
    ],
    "monthly": [
        "govnext_core.tasks.monthly.archive_old_data",
        "govnext_core.tasks.monthly.generate_monthly_statistics"
    ]
}

# Testing
# -------

before_tests = "govnext_core.setup.install.before_tests"

# Overriding Methods
# ------------------------------

override_whitelisted_methods = {
    "frappe.auth.get_logged_user": "govnext_core.api.auth.get_logged_user_with_gov_info",
    "frappe.desk.search.search_link": "govnext_core.search.government_search_link",
    "frappe.desk.reportview.get": "govnext_core.reportview.get_with_government_filters"
}

# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
    "Government Unit": "govnext_core.governo.dashboard.get_government_unit_dashboard",
    "Public Budget": "govnext_core.financeiro.dashboard.get_budget_dashboard",
    "Public Tender": "govnext_core.licitacao.dashboard.get_tender_dashboard"
}

# exempt linked doctypes from being automatically cancelled
auto_cancel_exempted_doctypes = [
    "Auto Repeat",
    "Audit Log", 
    "Security Log"
]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = [
    "Communication", 
    "ToDo", 
    "Note", 
    "File",
    "Audit Log",
    "Security Log",
    "Version"
]

# Request Events
# ----------------
before_request = [
    "govnext_core.hooks_functions.before_request",
    "govnext_core.utils.auth.validate_request_security"
]

after_request = [
    "govnext_core.hooks_functions.after_request",
    "govnext_core.utils.audit.log_api_request"
]

# Job Events
# ----------
before_job = ["govnext_core.hooks_functions.before_job"]
after_job = ["govnext_core.hooks_functions.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "User",
        "filter_by": "name",
        "redact_fields": ["phone", "mobile_no", "birth_date"],
        "partial": 1,
    },
    {
        "doctype": "Government Unit",
        "filter_by": "contact_email",
        "redact_fields": ["contact_phone", "address"],
        "partial": 1,
    },
    {
        "doctype": "Audit Log",
        "strict": False,
    }
]

# Portal da Transparência
# ----------------------

website_route_rules = [
    {"from_route": "/transparencia", "to_route": "transparencia_home"},
    {"from_route": "/transparencia/<path:route>", "to_route": "transparencia_route"},
    {"from_route": "/api/v1/<path:route>", "to_route": "api_v1_route"},
    {"from_route": "/orcamento/<name>", "to_route": "public_budget_detail"},
    {"from_route": "/licitacao/<name>", "to_route": "public_tender_detail"}
]

website_context = {
    "favicon": "/assets/govnext_core/images/favicon.ico",
    "splash_image": "/assets/govnext_core/images/govnext_logo.png",
    "app_title": "GovNext - Portal da Transparência",
    "app_name": "GovNext",
    "app_description": "Sistema de Gestão Governamental",
    "footer_address": "Prefeitura Municipal de Exemplo",
    "footer_items": [
        {"label": "Contato", "url": "/contato"},
        {"label": "Ouvidoria", "url": "/ouvidoria"},
        {"label": "Mapa do Site", "url": "/mapa-site"},
        {"label": "Política de Privacidade", "url": "/privacidade"},
        {"label": "Dados Abertos", "url": "/dados-abertos"},
        {"label": "API Documentation", "url": "/api/v1/docs"}
    ]
}

website_route_generators = [
    "govnext_core.transparencia.routes.get_routes",
    "govnext_core.api.routes.get_api_routes"
]

# Global Search
# -------------

global_search_doctypes = {
    "Government Unit": {
        "search_field": "unit_name",
        "route": ["Government Unit", "{name}"]
    },
    "Public Budget": {
        "search_field": "title",
        "route": ["Public Budget", "{name}"]
    },
    "Public Tender": {
        "search_field": "tender_title", 
        "route": ["Public Tender", "{name}"]
    }
}

# Email
# -----

email_brand_image = "/assets/govnext_core/images/govnext_logo.png"

# Boot Session
# ------------

boot_session = "govnext_core.boot.boot_session"

# Leaderboard
# -----------

leaderboards = [
    {
        "doctype": "Public Budget",
        "name": "Budget Management Leaders",
        "condition": "`tabPublic Budget`.`status` = 'Active'",
        "fields": [
            {"fieldname": "government_unit", "fieldtype": "Link"},
            {"fieldname": "total_revenue", "fieldtype": "Currency"}
        ]
    }
]

# Integrations
# ------------

# Webhooks
webhook_events = [
    "Government Unit:on_update",
    "Public Budget:on_submit", 
    "Public Tender:on_submit"
]

# Social Login
# ------------

social_login_providers = [
    {
        "name": "gov_id",
        "provider_name": "Gov.br",
        "auth_url": "https://sso.staging.acesso.gov.br/authorize",
        "redirect_url": "/api/method/govnext_core.api.auth.sso_login"
    }
]

# Error Handling
# --------------

error_report_email = "errors@govnext.com.br"

# Regional Settings
# -----------------

regional_overrides = {
    "Brazil": {
        "date_format": "dd/mm/yyyy",
        "time_format": "HH:mm",
        "number_format": "#.###,##",
        "currency": "BRL"
    }
}

# Background Jobs
# ---------------

background_jobs = [
    "govnext_core.jobs.sync_government_data",
    "govnext_core.jobs.generate_reports",
    "govnext_core.jobs.backup_system"
]

# API Rate Limiting
# -----------------

api_rate_limit = {
    "anonymous": {"limit": 100, "window": 3600},
    "authenticated": {"limit": 1000, "window": 3600},
    "system": {"limit": 10000, "window": 3600}
}
