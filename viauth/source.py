from flask import Blueprint, flash
from viauth import vial
from collections import namedtuple

AppArch = namedtuple('AppArch', ['bp','login_manager'])

def make_blueprint(prefix=None):
    prefix = prefix if prefix else '/%s'%vial.name
    bp = Blueprint(vial.name, __name__, url_prefix=prefix)

    @bp.route('/about', methods=['GET'])
    def about():
        return '%s %s: %s, written by toranova\n' % (vial.name, vial.version, vial.description)

    return bp
