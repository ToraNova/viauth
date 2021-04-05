from setuptools import find_packages, setup
from viauth.vial import name, description, version

setup(
    name=name,
    version=version,
    description=description,
    packages=find_packages(),
    author='Chia Jason',
    author_email='chia_jason96@live.com',
    url='https://github.com/toranova/viauth/',
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    keywords = ['Flask', 'Authentication']
    install_requires=[
        'flask','flask-login','sqlalchemy'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
