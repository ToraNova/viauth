'''
withadmin.py: extension of persistdb, with admin accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import userpriv
from viauth.persistdb import AuthUserMixin, adminarch, sqlorm, formutil
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr

class AuthUserMixin(AuthUserMixin, adminarch.UserMixin):

    @declared_attr
    def is_admin(cls):
        return Column(Boolean(), nullable=False) # a boolean flag to indicate admin or not

    def __init__(self, reqform):
        super().__init__(reqform)
        self.is_admin = False # cannot be admin by creating account, must be updated

    def admin_create(self, reqform):
        # user is being created by an admin
        # for instance, privilege elevation or role modificaion can occur here
        self.is_admin = formutil.getbool(reqform, "is_admin")

    def admin_update(self, reqform):
        # user is being updated by an admin
        self.update(reqform)
        # false by default, can only be enabled by code/sql
        self.is_admin = formutil.getbool(reqform, "is_admin")

    def admin_delete(self):
        # user being deleted by admin
        pass

class AuthUser(AuthUserMixin, sqlorm.Base):
    __tablename__ = "authuser"
    # This prevents errors,
    # BUT DO NOT USE UNDER NORMAL CIRCUMSTANCES AS IT MAY INDICATE MULTIPLE DEFINITIONS
    __table_args__ = {'extend_existing': True}

    def __init__(self, reqform):
        super().__init__(reqform)

'''
withrole.Arch (adminarch)
templates: login, profile, unauth, register, update, (users, register_other, update_other)
reroutes: login, logout, register, update, (update_other, delete_other, register_other)
'''
class Arch(adminarch.Base):
    def __init__(self, dburi, ormbase = sqlorm.Base, templates = {}, reroutes = {}, reroutes_kwarg = {}, rex_callback = {}, url_prefix=None, authuser_class=AuthUser, routes_disabled = [], login_key = {}):
        assert issubclass(authuser_class, AuthUserMixin)
        super().__init__(dburi, ormbase, templates, reroutes, reroutes_kwarg, rex_callback, url_prefix, authuser_class, routes_disabled, login_key)

    def generate_blueprint(self):
        bp = super().generate_blueprint()

        if 'users' not in self._rdisable:
            @bp.route('/users')
            @userpriv.admin_required
            def users():
                return self._return_users()

        # create other user
        if 'register_other' not in self._rdisable:
            @bp.route('/sudo/register', methods=['GET','POST'])
            @userpriv.admin_required
            def register_other():
                return self._return_register_other()

        # update other user
        if 'update_other' not in self._rdisable:
            @bp.route('/sudo/update/<uid>', methods=['GET','POST'])
            @userpriv.admin_required
            def update_other(uid):
                return self._return_update_other(uid)

        if 'delete_other' not in self._rdisable:
            @bp.route('/sudo/delete/<uid>')
            @userpriv.admin_required
            def delete_other(uid):
                return self._return_delete_other(uid)
        return bp
