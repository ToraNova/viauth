'''
withadmin.py: extension of persistdb, with admin accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import sqlorm, userpriv, formutil
from viauth.persistdb import persistdb
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.exc import IntegrityError

class AuthUser(persistdb.AuthUser):
    is_admin = Column(Boolean(), nullable=False) #only admins can list/delete users

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
        # user is being deleted by an admin
        pass

'''
templates: login, profile, unauth, register, update, (users, register_other, update_other)
reroutes: login, logout, register, update, (update_other, delete_other, register_other)
'''
class Arch(persistdb.Arch):
    def __init__(self, dburi, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser, route_disabled = []):
        assert issubclass(authuser_class, AuthUser)
        super().__init__(dburi, templates, reroutes, reroutes_kwarg, url_prefix, authuser_class, route_disabled)
        self.__default_tp('users', 'users.html')
        self.__default_tp('register_other', 'register_other.html')
        self.__default_tp('update_other', 'update_other.html')
        self.__default_rt('delete_other', 'viauth.users') # go to userlist after delete
        self.__default_rt('update_other', 'viauth.users') # go to userlist after update
        self.__default_rt('register_other', 'viauth.users') # go to userlist after update

    def __register_other(self):
        rscode = 200
        if request.method == 'POST':
            try:
                u = self.__auclass(request.form) # create the user
                u.admin_create(request.form)
                self.session.add(u)
                self.session.commit()
                self.ok('user account created')
                return True, None # success
            except IntegrityError as e:
                self.error('sql integrity error')
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
                self.ok('profile updated')
                return True, None # success
            except IntegrityError as e:
                self.error('sql integrity error')
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
            self.ok('account deleted')
            return True # success
        except Exception as e:
            self.ex(e)
        self.session.rollback()
        return False

    def __return_users(self):
        ulist = self.__auclass.query.all()
        return render_template(self.__templ['users'], data = ulist)

    def __return_register_other(self):
        rbool, rscode = self.__register_other()
        if rbool:
            return self.__reroute('register_other')
        form = self.__auclass._formgen_assist(self.session)
        # use the same form as 'register'
        return render_template(self.__templ['register_other'], form = form), rscode

    def __return_update_other(self, uid):
        u = self.__auclass.query.filter(self.__auclass.id == uid).first()
        if not u:
            abort(400)
        rbool, rscode = self.__update_other(u)
        if rbool:
            return self.__reroute('update_other')
        form = self.__auclass._formgen_assist(self.session)
        return render_template(self.__templ['update_other'], data = u, form=form), rscode

    def __return_delete_other(self, uid):
        u = self.__auclass.query.filter(self.__auclass.id == uid).first()
        if not u:
            abort(400)
        self.__delete_other(u)
        return self.__reroute('delete_other')

    def __make_bp(self):
        bp = super().__make_bp()

        if 'users' not in self.__rdisable:
            @bp.route('/users')
            @userpriv.admin_required
            def users():
                return self.__return_users()

        # create other user
        if 'register_other' not in self.__rdisable:
            @bp.route('/sudo/register', methods=['GET','POST'])
            @userpriv.admin_required
            def register_other():
                return self.__return_register_other()

        # update other user
        if 'update_other' not in self.__rdisable:
            @bp.route('/sudo/update/<uid>', methods=['GET','POST'])
            @userpriv.admin_required
            def update_other(uid):
                return self.__return_update_other(uid)

        if 'delete_other' not in self.__rdisable:
            @bp.route('/sudo/delete/<uid>')
            @userpriv.admin_required
            def delete_other(uid):
                return self.__return_delete_other(uid)

        return bp
