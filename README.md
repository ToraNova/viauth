# viauth
[![Build Status](https://travis-ci.org/ToraNova/viauth.svg?branch=master)](https://travis-ci.org/ToraNova/viauth)

A mini flask (vial) project for authentication architecture using [flask-login](https://flask-login.readthedocs.io/en/latest/).

## Installation
Recommend to do this in a virtual environment!
```bash
pip install git+git://github.com/toranova/viauth.git@master
```

## Examples
1. [Minimal Login (No Database)](examples/basic/__init__.py)
2. [With SQLAlchemy](examples/persistdb/__init__.py)
3. [Custom Userclass](examples/cuclass/__init__.py)
