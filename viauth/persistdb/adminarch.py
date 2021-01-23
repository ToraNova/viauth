# this is shared between withadmin/ withroles, both using different userclasses
from flask import render_template, request, redirect, abort, flash, url_for
from viauth.persistdb import persistdb
from viauth import sqlorm
from sqlalchemy.exc import IntegrityError

class UserMixin:
    def admin_create(self, reqform):
        pass

    def admin_update(self, reqform):
        pass

    def admin_delete(self):
        pass

'''
adminarch Template
templates: login, profile, unauth, register, update, (users, register_other, update_other)
reroutes: login, logout, register, update, (update_other, delete_other, register_other)
'''
class Base(persistdb.Arch):
    def __init__(self, dburi, ormbase = sqlorm.Base,  templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=None, routes_disabled = [], login_key = {}):
        assert issubclass(authuser_class, UserMixin)
        super().__init__(dburi, ormbase, templates, reroutes, reroutes_kwarg, url_prefix, authuser_class, routes_disabled, login_key)
        self._default_tp('users', 'users.html')
        self._default_tp('register_other', 'register_other.html')
        self._default_tp('update_other', 'update_other.html')
        self._default_rt('delete_other', 'viauth.users') # go to userlist after delete
        self._default_rt('update_other', 'viauth.users') # go to userlist after update
        self._default_rt('register_other', 'viauth.users') # go to userlist after update

    def __register_other(self):
        rscode = 200
        if request.method == 'POST':
            try:
                u = self._auclass(request.form) # create the user
                u.admin_create(request.form)
                self.session.add(u)
                self.session.commit()
                self.ok('user account created.')
                return True, None # success
            except IntegrityError as e:
                self.error('sql integrity error.')
                rscode = 409
            except Exception as e:
                self.ex(e)
            self.session.rollback()
        return False, rscode # fail

    def __update_other(self, u):
        rscode = 200
        if request.method == 'POST':
            try:
                u.admin_update(request.form) # runs the admin update callback
                self.session.add(u)
                self.session.commit()
                self.ok('profile updated.')
                return True, None # success
            except IntegrityError as e:
                self.error('sql integrity error.')
                rscode = 409
            except Exception as e:
                self.ex(e)
            self.session.rollback()
        return False, rscode

    def __delete_other(self, u):
        try:
            u.admin_delete() # runs the admin_delete callback
            self.session.delete(u)
            self.session.commit()
            self.ok('account deleted.')
            return True # success
        except Exception as e:
            self.ex(e)
        self.session.rollback()
        return False

    def _return_users(self):
        ulist = self._auclass.query.all()
        return render_template(self._templ['users'], data = ulist)

    def _return_register_other(self):
        rbool, rscode = self.__register_other()
        if rbool:
            return self._reroute('register_other')
        form = self._auclass._formgen_assist(self.session)
        # use the same form as 'register'
        return render_template(self._templ['register_other'], form = form), rscode

    def _return_update_other(self, uid):
        u = self._auclass.query.filter(self._auclass.id == uid).first()
        if not u:
            abort(400)
        rbool, rscode = self.__update_other(u)
        if rbool:
            return self._reroute('update_other')
        form = self._auclass._formgen_assist(self.session)
        return render_template(self._templ['update_other'], data = u, form=form), rscode

    def _return_delete_other(self, uid):
        u = self._auclass.query.filter(self._auclass.id == uid).first()
        if not u:
            abort(400)
        self.__delete_other(u)
        return self._reroute('delete_other')
