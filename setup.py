from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in whatsapp_client/__init__.py
from whatsapp_client import __version__ as version

setup(
	name="whatsapp_client",
	version=version,
	description="Whatsapp Integartion",
	author="Ajay",
	author_email="info@dexciss.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
