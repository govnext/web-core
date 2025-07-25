from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

setup(
	name="govnext_core",
	version="0.0.1",
	description="GovNext Core - Government Management System based on ERPNext",
	author="GovNext Team",
	author_email="contato@govnext.com.br",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
