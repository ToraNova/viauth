'''
withroles.py: extension of persistdb and persistdb.withadmin, with role-based accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import userpriv
from viauth.persistdb import AuthUserMixin, adminarch, sqlorm, formutil
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr

# is_admin now is a trait for super_admins
class AuthUserMixin(AuthUserMixin, adminarch.UserMixin):
    # set to null on cascade
    @declared_attr
    def rid(cls):
        return Column(Integer, ForeignKey('authrole.id', ondelete='SET NULL'), nullable=True)

    @declared_attr
    def role(cls):
        return relationship("AuthRole", foreign_keys=[cls.rid])

    def __init__(self, reqform):
        super().__init__(reqform)
        self.rid = None # user start with no role

    def admin_create(self, reqform):
        # user is being created by an admin
        # for instance, privilege elevation or role modificaion can occur here
        self.rid = reqform.get("rid")

    def admin_update(self, reqform):
        # only admin can change a user's role id
        self.rid = reqform.get("rid")

    def admin_delete(self):
        # user being deleted by admin
        pass

class AuthRoleMixin(sqlorm.Core):
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key = True)

    @declared_attr
    def name(cls):
        return Column(String(50),unique=True,nullable=False)

    @declared_attr
    def level(cls):
        return Column(Integer, unique=False, nullable=False) # authority level of role

    @declared_attr
    def is_admin(cls):
        return Column(Boolean(), nullable=False) # boolean flag to indicate admin or not

    def __init__(self, reqform):
        self.name = reqform.get('name')
        self.level = reqform.get('level')
        self.is_admin = formutil.getbool(reqform, "is_admin")

    def update(self, reqform):
        self.name = reqform.get('name')
        self.level = reqform.get('level')
        self.is_admin = formutil.getbool(reqform, "is_admin")

    def delete(self):
        pass

class AuthUser(AuthUserMixin, sqlorm.Base):
    __tablename__ = "authuser"
    # This prevents errors,
    # BUT DO NOT USE UNDER NORMAL CIRCUMSTANCES AS IT MAY INDICATE MULTIPLE DEFINITIONS
    __table_args__ = {'extend_existing': True}

    def form_auxdata_generate(session):
        return AuthRole.query.all()

    def __init__(self, reqform):
        super().__init__(reqform)

class AuthRole(AuthRoleMixin, sqlorm.Base):
    __tablename__ = "authrole"
    # This prevents errors,
    # BUT DO NOT USE UNDER NORMAL CIRCUMSTANCES AS IT MAY INDICATE MULTIPLE DEFINITIONS
    __table_args__ = {'extend_existing': True}

    def __init__(self, reqform):
        super().__init__(reqform)


'''
withrole.Arch (adminarch)
templates: login, profile, unauth, register, update, users, register_other, update_other, (insert_role, roles, update_role)
reroutes: login, logout, register, update, register_other, update_other, delete_other, (insert_role, update_role, delete_role)
'''
class Arch(adminarch.Base):
    def __init__(self, dburi, ormbase = sqlorm.Base, access_priv = {}, templates = {}, reroutes = {}, reroutes_kwarg = {}, rex_callback = {}, url_prefix=None, authuser_class=AuthUser, authrole_class=AuthRole, routes_disabled = [], login_key = {}):
        assert issubclass(authuser_class, AuthUserMixin)
        assert issubclass(authrole_class, AuthRoleMixin)
        super().__init__(dburi, ormbase, templates, reroutes, reroutes_kwarg, rex_callback, url_prefix, authuser_class, routes_disabled, login_key)
        self._arclass = authrole_class
        self._default_tp('roles', 'roles.html')
        self._default_tp('insert_role', 'insert_role.html')
        self._default_tp('update_role', 'update_role.html')
        self._default_rt('insert_role', 'viauth.roles')
        self._default_rt('update_role', 'viauth.roles')
        self._default_rt('delete_role', 'viauth.roles')
        self._accesspriv = access_priv
        # default role access privileges
        self._default_ra('users', userpriv.role_isadmin('admin')) # requires role.name == admin to access 'users'
        self._default_ra('register_other',userpriv.role_isadmin('admin'))
        self._default_ra('delete_other',userpriv.role_isadmin('admin'))
        self._default_ra('update_other',userpriv.role_isadmin('admin'))
        self._default_ra('roles', userpriv.role_isadmin('admin'))
        self._default_ra('insert_role', userpriv.role_isadmin('admin'))
        self._default_ra('update_role', userpriv.role_isadmin('admin'))
        self._default_ra('delete_role', userpriv.role_isadmin('admin'))

    def _default_ra(self, key, value):
        if not self._accesspriv.get(key):
            self._accesspriv[key] = value

    def _insert_role(self):
        rscode = 200
        if request.method == 'POST':
            try:
                r = self._arclass(request.form)
                self.session.add(r)
                self.session.commit()
                self.ok('insert_role', 'user role created.')
                return True, None
            except IntegrityError as e:
                self.err('insert_role', 'role already exists.')
                rscode = 409
            except Exception as e:
                self.ex('insert_role', e)
            self.session.rollback()
        return False, rscode

    def _update_role(self, r):
        rscode = 200
        if request.method == 'POST':
            try:
                r.update(request.form)
                self.session.add(r)
                self.session.commit()
                self.ok('update_role', 'user role updated.')
                return True, None
            except IntegrityError as e:
                self.err('update_role', 'role already exists.')
                rscode = 409
            except Exception as e:
                self.ex('update_role', e)
            self.session.rollback()
        return False, rscode

    def _delete_role(self, r):
        try:
            r.delete()
            self.session.delete(r)
            self.session.commit()
            self.ok('delete_role', 'user role deleted.')
            return True
        except Exception as e:
            self.ex('delete_role', e)
        self.session.rollback()
        return False

    def generate_blueprint(self):
        bp = super().generate_blueprint()

        # this is defined in persistdb/withadmin.py
        if 'users' not in self._rdisable:
            @bp.route('/users')
            @self._accesspriv['users']
            def users():
                return self._return_users()

        # this is defined in persistdb/withadmin.py
        if 'register_other' not in self._rdisable:
            @bp.route('/sudo/register', methods=['GET','POST'])
            @self._accesspriv['register_other']
            def register_other():
                return self._return_register_other()

        # this is defined in persistdb/withadmin.py
        if 'update_other' not in self._rdisable:
            @bp.route('/sudo/update/<uid>', methods=['GET','POST'])
            @self._accesspriv['update_other']
            def update_other(uid):
                return self._return_update_other(uid)

        # this is defined in persistdb/withadmin.py
        if 'delete_other' not in self._rdisable:
            @bp.route('/sudo/delete/<uid>')
            @self._accesspriv['delete_other']
            def delete_other(uid):
                return self._return_delete_other(uid)

        if 'roles' not in self._rdisable:
            @bp.route('/roles')
            @self._accesspriv['roles']
            def roles():
                rlist = self._arclass.query.all()
                return render_template(self._templ['roles'], data = rlist)

        if 'insert_role' not in self._rdisable:
            @bp.route('/role/register', methods=['GET','POST'])
            @self._accesspriv['insert_role']
            def insert_role():
                rbool, rscode = self._insert_role()
                if rbool:
                    return self._reroute('insert_role')
                fauxd = self._arclass.form_auxdata_generate(self.session)
                return render_template(self._templ['insert_role'], form_auxd=fauxd), rscode

        if 'update_role' not in self._rdisable:
            @bp.route('/role/update/<rid>', methods=['GET','POST'])
            @self._accesspriv['update_role']
            def update_role(rid):
                r = self._arclass.query.filter(self._arclass.id == rid).first()
                if not r:
                    abort(400)
                rbool, rscode = self._update_role(r)
                if rbool:
                    return self._reroute('update_role')
                fauxd = self._arclass.form_auxdata_generate(self.session)
                return render_template(self._templ['update_role'], data=r, form_auxd=fauxd), rscode

        if 'delete_role' not in self._rdisable:
            @bp.route('/role/delete/<rid>')
            @self._accesspriv['delete_role']
            def delete_role(rid):
                r = self._arclass.query.filter(self._arclass.id == rid).first()
                if not r:
                    abort(400)
                self._delete_role(r)
                return self._reroute('delete_role')

        return bp
