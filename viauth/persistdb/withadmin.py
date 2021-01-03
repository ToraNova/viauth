'''
withadmin.py: extension of persistdb, with admin accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import source, sqlorm, userpriv
from viauth.persistdb import persistdb
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.exc import IntegrityError

class AuthUser(persistdb.AuthUser):
    is_admin = Column(Boolean(), nullable=False) #only admins can list/delete users

    def __init__(self, reqform):
        super().__init__(reqform)
        self.update(reqform)
        self.is_admin = False # cannot be admin by creating account, must be updated

    def update(self, reqform):
        self.emailaddr = reqform.get("emailaddr")
        # false by default, can only be enabled by code/sql
        self.is_admin = reqform.get("is_admin") == "on" if reqform.get("is_admin") else False

'''
withadmin.Arch
templates: login, register, profile, update, (users, update_other)
reroutes: login, logout, unauth, register, update, (update_other, delete_other)
'''
class Arch(persistdb.Arch):
    def __init__(self, dburi, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser):
        assert issubclass(authuser_class, AuthUser)
        super().__init__(dburi, templates, reroutes, reroutes_kwarg, url_prefix, authuser_class)
        self.__default_tp('users', 'users.html')
        self.__default_tp('update_other', 'update_other.html')
        self.__default_rt('delete_other', 'viauth.users') # go to userlist after edit
        self.__default_rt('update_other', 'viauth.users') # go to userlist after delete
        assert self.__templ['users'] and self.__templ['update_other']
        assert self.__route['delete_other'] and self.__route['update_other']

    def __make_bp_lman(self):
        bp, lman = super().__make_bp_lman()

        @bp.route('/users')
        @userpriv.admin_required
        def users():
            ulist = self.__auclass.query.all()
            return render_template(self.__templ['users'], data = ulist)

        # update other user
        @bp.route('/update/<uid>', methods=['GET','POST'])
        @userpriv.admin_required
        def update_other(uid):
            u = AuthUser.query.filter(AuthUser.id == uid).first()
            if request.method == 'POST':
                try:
                    u.update(request.form)
                    self.session.add(u)
                    self.session.commit()
                    source.emflash('profile updated')
                    return self.__reroute('update_other')
                except Exception as e:
                    self.session.rollback()
                    source.eflash(e)
            return render_template(self.__templ['update_other'], data = u)

        @bp.route('/delete_other/<uid>')
        @userpriv.admin_required
        def delete_other(uid):
            try:
                tar = AuthUser.query.filter(AuthUser.id == uid).first()
                if not tar:
                    abort(400)
                self.session.delete(tar)
                self.session.commit()
                source.emflash('account deleted')
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
            return self.__reroute('delete_other')

        return source.AppArch(bp, lman)
