app_name = "govnext_estadual"
app_title = "GovNext Estadual"
app_publisher = "GovNext Team"
app_description = "Sistema de Gestão para Governos Estaduais"
app_email = "contato@govnext.com.br"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/govnext_estadual/css/govnext_estadual.css"
app_include_js = "/assets/govnext_estadual/js/govnext_estadual.js"

# include js, css files in header of web template
web_include_css = "/assets/govnext_estadual/css/govnext_estadual_web.css"
web_include_js = "/assets/govnext_estadual/js/govnext_estadual_web.js"

# include custom scss in every website theme (without file extension ".scss")
website_theme_scss = "govnext_estadual/public/scss/website"

# Fixtures
# ----------
fixtures = ["Custom Field", "Custom Script"]

# Installation
# ------------

# before_install = "govnext_estadual.install.before_install"
after_install = "govnext_estadual.setup.install.after_install"

# Modules
# -------
# Specific modules from govnext_core related to state administration
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
		"govnext_estadual.tasks.daily"
	],
}

# Additional modules specific to state administration
domains = {
    "Estadual": "govnext_estadual.domains.estadual"
}
