from flask import render_template, redirect, url_for, request, abort
from flask_login import current_user
from functools import wraps

'''
current_user needs to have the attribute is_admin
equivalent to role_required('admin')
'''
def admin_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            # not logged in
            abort(401)
        if not current_user.is_admin:
            # not admin
            abort(403)
        return fn(*args, **kwargs)
    return decorated_view

'''
similar like admin_required, except the is_admin attribute is on the role of the user
rather than the user itself
'''
def role_isadmin(name):
    def outer_dec(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                # not logged in
                abort(401)
            if not hasattr(current_user, 'role') or not hasattr(current_user.role, 'is_admin'):
                # no role
                abort(403)
            if not current_user.role.is_admin:
                # not the role
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return outer_dec

'''
if using role-based access model, current_user.role.name must be exactly 'name'
THIS IS CASE SENSITIVE!
'''
def role_required(name):
    def outer_dec(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                # not logged in
                abort(401)
            if not hasattr(current_user, 'role') or not hasattr(current_user.role, 'name'):
                # no role
                abort(403)
            if current_user.role.name != name:
                # not the role
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return outer_dec

'''
if using role-based access model, current_user.role.name must not be 'name'
THIS IS CASE SENSITIVE!
'''
def role_banned(name):
    def outer_dec(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                #not logged in
                abort(401)
            if not hasattr(current_user, 'role') or not hasattr(current_user.role, 'name'):
                # no role
                abort(403)
            if current_user.role.name == name:
                # not the role
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return outer_dec

'''
if using privilege level model, current_user.role.level cannot exceed 'level'
suppose level 0 is highest privilege, using atmost(0) means only highest privilege can access
atmost(2) means 0, 1 and 2 can access.
'''
def level_atmost(level):
    def outer_dec(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                #not logged in
                abort(401)
            if not hasattr(current_user, 'role') or not hasattr(current_user.role, 'level'):
                # no role
                abort(403)
            if current_user.role.level > level:
                # exceeded privilege level
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return outer_dec

'''
if using privilege level model, current_user.role.level cannot be less than 'level'
suppose level 0 is lowest privilege, using atleast(0) means everyone can access
atleast(2) means 2, 3, 4 ... can access.
recommend to use atmost instead of this!
'''
def level_atleast(level):
    def outer_dec(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                #not logged in
                abort(401)
            if not hasattr(current_user, 'role') or not hasattr(current_user.role, 'level'):
                # no role
                abort(403)
            if current_user.role.level < level:
                # insufficient privilege level
                abort(403)
            return fn(*args, **kwargs)
        return decorated_view
    return outer_dec
