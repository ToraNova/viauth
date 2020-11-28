from flask import Blueprint
from viauth import vial

bp = Blueprint(vial.name, __name__, url_prefix='/%s'%vial.name)

@bp.route('/about', methods=['GET'])
def about():
    return '%s %s: %s\n' % (vial.name, vial.version, vial.description)
