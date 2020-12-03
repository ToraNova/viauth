from flask import Blueprint, flash
from viauth import vial
from collections import namedtuple

bp = Blueprint(vial.name, __name__, url_prefix='/%s'%vial.name)

@bp.route('/about', methods=['GET'])
def about():
    return '%s %s: %s\n' % (vial.name, vial.version, vial.description)

AppArch = namedtuple('AppArch', ['bp','login_manager'])

def eflash(exception):
    flash("an exception has occurred: %s" % type(exception).__name__, 'err')

def eflash(exception):
    flash("an exception has occurred: %s" % type(exception).__name__, 'err')

def emflash(msg):
    flash(msg, 'err')

def sflash(msg):
    flash(msg, 'ok')

def wflash(msg):
    flash(msg, 'warn')
