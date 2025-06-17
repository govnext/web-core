app_name = "govnext_municipal"
app_title = "GovNext Municipal"
app_publisher = "GovNext Team"
app_description = "Sistema de Gestão para Municípios"
app_email = "contato@govnext.com.br"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/govnext_municipal/css/govnext_municipal.css"
app_include_js = "/assets/govnext_municipal/js/govnext_municipal.js"

# include js, css files in header of web template
web_include_css = "/assets/govnext_municipal/css/govnext_municipal_web.css"
web_include_js = "/assets/govnext_municipal/js/govnext_municipal_web.js"

# include custom scss in every website theme (without file extension ".scss")
website_theme_scss = "govnext_municipal/public/scss/website"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Fixtures
# ----------
fixtures = ["Custom Field", "Custom Script"]

# Installation
# ------------

# before_install = "govnext_municipal.install.before_install"
after_install = "govnext_municipal.setup.install.after_install"

# Modules
# -------
# Specific modules from govnext_core related to municipal administration
required_apps = ["govnext_core"]

# DocTypes
# --------
doctype_js = {
    "Item": "public/js/item.js",
    "Customer": "public/js/customer.js",
    "Supplier": "public/js/supplier.js"
}

# Include custom doctypes
# ----------------------
# doctype_list_js = {"doctype": "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype": "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype": "public/js/doctype_calendar.js"}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"govnext_municipal.tasks.daily"
	],
}

# Testing
# -------

# before_tests = "govnext_municipal.install.before_tests"

# Additional modules specific to municipal administration
domains = {
    "Municipal": "govnext_municipal.domains.municipal"
}
