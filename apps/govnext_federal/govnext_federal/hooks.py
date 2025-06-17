app_name = "govnext_federal"
app_title = "GovNext Federal"
app_publisher = "GovNext Team"
app_description = "Sistema de Gestão para Governo Federal"
app_email = "contato@govnext.com.br"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/govnext_federal/css/govnext_federal.css"
app_include_js = "/assets/govnext_federal/js/govnext_federal.js"

# include js, css files in header of web template
web_include_css = "/assets/govnext_federal/css/govnext_federal_web.css"
web_include_js = "/assets/govnext_federal/js/govnext_federal_web.js"

# include custom scss in every website theme (without file extension ".scss")
website_theme_scss = "govnext_federal/public/scss/website"

# Fixtures
# ----------
fixtures = ["Custom Field", "Custom Script"]

# Installation
# ------------

# before_install = "govnext_federal.install.before_install"
after_install = "govnext_federal.setup.install.after_install"

# Modules
# -------
# Specific modules from govnext_core related to federal administration
required_apps = ["govnext_core"]

# DocTypes
# --------
doctype_js = {
    "Item": "public/js/item.js",
    "Customer": "public/js/customer.js",
    "Supplier": "public/js/supplier.js"
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"govnext_federal.tasks.daily"
	],
}

# Additional modules specific to federal administration
domains = {
    "Federal": "govnext_federal.domains.federal"
}
