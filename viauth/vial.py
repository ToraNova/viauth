'''
vial.py:
this file contains the implementation description/version that should be changed
upon every build
'''
from flask import Blueprint, flash
from collections import namedtuple

name = 'viauth'
version = '0.1.7'
description = 'vial-auth (viauth), a flask mini login/auth module'
AppArch = namedtuple('AppArch', ['bp','login_manager'])

def make_blueprint(prefix=None):
    prefix = prefix if prefix else '/%s'%name
    bp = Blueprint(name, __name__, url_prefix=prefix)

    @bp.route('/about', methods=['GET'])
    def about():
        return '%s %s: %s, written by toranova\n' % (name, version, description)

    return bp
