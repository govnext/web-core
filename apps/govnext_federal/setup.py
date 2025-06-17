from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

setup(
	name="govnext_federal",
	version="0.0.1",
	description="GovNext Federal - Sistema de Gestão para Governo Federal",
	author="GovNext Team",
	author_email="contato@govnext.com.br",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
