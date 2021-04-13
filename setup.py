from setuptools import find_packages, setup

_version = '0.2.2'

setup(
    name='viauth',
    version=_version,
    description='vial-auth (viauth), a flask mini login/auth module for development bootstrapping',
    packages=find_packages(),
    author='Chia Jason',
    author_email='chia_jason96@live.com',
    url='https://github.com/toranova/viauth/',
    download_url='https://github.com/ToraNova/viauth/archive/refs/tags/v%s.tar.gz' % _version,
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    keywords = ['Flask', 'Authentication'],
    install_requires=[
        'flask',
        'vicore',
        'flask-login',
        'sqlalchemy',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
