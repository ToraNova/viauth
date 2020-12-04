from flask import Blueprint, flash
from viauth import vial
from collections import namedtuple

AppArch = namedtuple('AppArch', ['bp','login_manager'])

def make_blueprint():
    bp = Blueprint(vial.name, __name__, url_prefix='/%s'%vial.name)

    @bp.route('/about', methods=['GET'])
    def about():
        return '%s %s: %s\n' % (vial.name, vial.version, vial.description)

    return bp

def eflash(exception):
    flash("an exception (%s) has occurred: %s" % (type(exception).__name__, str(exception)), 'err')

def emflash(msg):
    flash(msg, 'err')

def sflash(msg):
    flash(msg, 'ok')

def wflash(msg):
    flash(msg, 'warn')
