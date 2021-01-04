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
        self.is_admin = False # cannot be admin by creating account, must be updated

    def admin_update(self, reqform):
        self.self_update(reqform)
        # false by default, can only be enabled by code/sql
        self.is_admin = self.getform_tf(reqform, "is_admin")

'''
templates: login, profile, unauth, register, update, (users, update_other)
reroutes: login, logout, register, update, (update_other, delete_other, register_other)
'''
class Arch(persistdb.Arch):
    def __init__(self, dburi, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser):
        assert issubclass(authuser_class, AuthUser)
        super().__init__(dburi, templates, reroutes, reroutes_kwarg, url_prefix, authuser_class)
        self.__default_tp('users', 'users.html')
        self.__default_tp('update_other', 'update_other.html')
        self.__default_rt('delete_other', 'viauth.users') # go to userlist after delete
        self.__default_rt('update_other', 'viauth.users') # go to userlist after update
        self.__default_rt('register_other', 'viauth.users') # go to userlist after update

    def __users(self):
        ulist = self.__auclass.query.all()
        return render_template(self.__templ['users'], data = ulist)

    def __update_other(self, uid):
        u = self.__auclass.query.filter(self.__auclass.id == uid).first()
        if not u:
            abort(400)
        if request.method == 'POST':
            try:
                u.admin_update(request.form)
                self.session.add(u)
                self.session.commit()
                source.emflash('profile updated')
                return True
            except IntegrityError as e:
                self.session.rollback()
                source.emflash('sql integrity errror')
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
            return False

    def __delete_other(self, uid):
        u = self.__auclass.query.filter(self.__auclass.id == uid).first()
        if not u:
            abort(400)
        try:
            u.delete()
            self.session.delete(u)
            self.session.commit()
            source.emflash('account deleted')
            return True
        except Exception as e:
            self.session.rollback()
            source.eflash(e)
        return False

    def __make_bp(self):
        bp = super().__make_bp()

        @bp.route('/register_other')
        @userpriv.admin_required
        def register_other():
            if self.__register():
                return self.__reroute('register_other')
            form = self.__auclass.formgen_assist(self.session)
            # use the same form as 'register'
            return render_template(self.__templ['register'], form = form)

        @bp.route('/users')
        @userpriv.admin_required
        def users():
            return self.__users()

        # update other user
        @bp.route('/update/<uid>', methods=['GET','POST'])
        @userpriv.admin_required
        def update_other(uid):
            if self.__update_other(uid):
                return self.__reroute('update_other')
            form = self.__auclass.formgen_assist(self.session)
            return render_template(self.__templ['update_other'], data = u, form=form)

        @bp.route('/delete/<uid>')
        @userpriv.admin_required
        def delete_other(uid):
            self.__delete_other(uid)
            return self.__reroute('delete_other')

        return bp
