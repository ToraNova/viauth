from flask import Blueprint
from viauth import vial

@bp.route('/about', methods=['GET'])
def about():
    return '%s %s: %s\n' % (vial.name, vial.version, vial.description)
