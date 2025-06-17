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
# app_include_css = "/assets/govnext_core/css/govnext_core.css"
# app_include_js = "/assets/govnext_core/js/govnext_core.js"

# include js, css files in header of web template
# web_include_css = "/assets/govnext_core/css/govnext_core.css"
# web_include_js = "/assets/govnext_core/js/govnext_core.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "govnext_core/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Fixtures
# ----------
fixtures = ["Custom Field", "Custom Script"]

# Installation
# ------------

# before_install = "govnext_core.install.before_install"
# after_install = "govnext_core.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "govnext_core.uninstall.before_uninstall"
# after_uninstall = "govnext_core.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "govnext_core.setup.install.before_app_install"
# after_app_install = "govnext_core.setup.install.after_app_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "govnext_core.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"govnext_core.tasks.all"
# 	],
# 	"daily": [
# 		"govnext_core.tasks.daily"
# 	],
# 	"hourly": [
# 		"govnext_core.tasks.hourly"
# 	],
# 	"weekly": [
# 		"govnext_core.tasks.weekly"
# 	],
# 	"monthly": [
# 		"govnext_core.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "govnext_core.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "govnext_core.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "govnext_core.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo", "Note", "File"]

# Request Events
# ----------------
# before_request = ["govnext_core.utils.before_request"]
# after_request = ["govnext_core.utils.after_request"]

# Job Events
# ----------
# before_job = ["govnext_core.utils.before_job"]
# after_job = ["govnext_core.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Portal da Transparência
# ----------------------

website_route_rules = [
    {"from_route": "/transparencia", "to_route": "transparencia_home"},
    {"from_route": "/transparencia/<path:route>", "to_route": "transparencia_route"},
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
        {"label": "Política de Privacidade", "url": "/privacidade"}
    ]
}

website_route_generators = ["govnext_core.transparencia.routes.get_routes"]

web_include_css = [
    "/assets/govnext_core/css/transparencia.css"
]

web_include_js = [
    "/assets/govnext_core/js/transparencia.js"
]
