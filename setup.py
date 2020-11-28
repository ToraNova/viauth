from setuptools import find_packages, setup
from viauth.vial import name, description, version

setup(
    name='viauth',
    version=version,
    description=description,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask','flask-login'
    ],
)
