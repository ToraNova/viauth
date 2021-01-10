'''
withroles.py: extension of persistdb and persistdb.withadmin, with role-based accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import sqlorm, userpriv
from viauth.persistdb import withadmin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

class AuthRole(sqlorm.ViAuthBase, sqlorm.Base):
    __tablename__ = "authrole"
    id = Column(Integer, primary_key = True)
    name = Column(String(50),unique=True,nullable=False)
    level = Column(Integer, unique=False, nullable=False)

    def __init__(self, reqform):
        self.name = reqform.get('name')
        self.level = reqform.get('level')

    def update(self, reqform):
        self.name = reqform.get('name')
        self.level = reqform.get('level')

    def delete(self):
        pass

# is_admin now is a trait for super_admins
class AuthUser(withadmin.AuthUser):
    # set to null on cascade
    rid = Column(Integer, ForeignKey('authrole.id', ondelete='SET NULL'), nullable=True)
    role = relationship("AuthRole", foreign_keys=[rid])

    def _formgen_assist(session):
        return AuthRole.query.all()

    def __init__(self, reqform):
        super().__init__(reqform)
        self.rid = None # user start with no role

    def admin_create(self, reqform):
        super().admin_create(reqform)
        # user is being created by an admin
        # for instance, privilege elevation or role modificaion can occur here
        self.rid = reqform.get("rid")

    def admin_update(self, reqform):
        super().admin_update(reqform)
        # only admin can change a user's role id
        self.rid = reqform.get("rid")

'''
withadmin.Arch
templates: login, profile, unauth, register, update, users, register_other, update_other, (insert_role, roles, update_role)
reroutes: login, logout, register, update, register_other, update_other, delete_other, (insert_role, update_role, delete_role)
'''
class Arch(withadmin.Arch):
    def __init__(self, dburi, access_priv = {}, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser, authrole_class=AuthRole, routes_disabled = []):
        assert issubclass(authuser_class, AuthUser)
        assert issubclass(authrole_class, AuthRole)
        super().__init__(dburi, templates, reroutes, reroutes_kwarg, url_prefix, authuser_class, routes_disabled)
        self.__arclass = AuthRole
        self.__default_tp('roles', 'roles.html')
        self.__default_tp('insert_role', 'insert_role.html')
        self.__default_tp('update_role', 'update_role.html')
        self.__default_rt('insert_role', 'viauth.roles')
        self.__default_rt('update_role', 'viauth.roles')
        self.__default_rt('delete_role', 'viauth.roles')
        self.__accesspriv = access_priv
        # default role access privileges
        self.__default_ra('users','admin') # requires role.name == admin to access 'users'
        self.__default_ra('register_other','admin')
        self.__default_ra('delete_other','admin')
        self.__default_ra('update_other','admin')
        self.__default_ra('roles', 'admin')
        self.__default_ra('insert_role', 'admin')
        self.__default_ra('update_role', 'admin')
        self.__default_ra('delete_role', 'admin')

    def __default_ra(self, key, value):
        if not self.__accesspriv.get(key):
            self.__accesspriv[key] = value

    def __insert_role(self):
        rscode = 200
        if request.method == 'POST':
            try:
                r = self.__arclass(request.form)
                self.session.add(r)
                self.session.commit()
                self.ok('role created')
                return True, None
            except IntegrityError as e:
                self.error('role already exists')
                rscode = 409
            except Exception as e:
                self.ex(e)
            self.session.rollback()
        return False, rscode

    def __update_role(self, r):
        rscode = 200
        if request.method == 'POST':
            try:
                r.update(request.form)
                self.session.add(r)
                self.session.commit()
                self.ok('role updated')
                return True, None
            except IntegrityError as e:
                self.error('role already exists')
                rscode = 409
            except Exception as e:
                self.ex(e)
            self.session.rollback()
        return False, rscode

    def __delete_role(self, r):
        try:
            r = self.__arclass.query.filter(self.__arclass.id == rid).first()
            if not r:
                abort(400)
            r.delete()
            self.session.delete(r)
            self.session.commit()
            self.error('role deleted')
            return True
        except Exception as e:
            self.ex(e)
        self.session.rollback()
        return False

    def __make_bp(self):
        bp = super(withadmin.Arch, self).__make_bp() #calling grandparent function

        # this is defined in persistdb/withadmin.py
        if 'users' not in self.__rdisable:
            @bp.route('/users')
            @userpriv.role_required(self.__accesspriv['users'])
            def users():
                return self.__return_users()

        # this is defined in persistdb/withadmin.py
        if 'register_other' not in self.__rdisable:
            @bp.route('/sudo/register', methods=['GET','POST'])
            @userpriv.role_required(self.__accesspriv['register_other'])
            def register_other():
                return self.__return_register_other()

        # this is defined in persistdb/withadmin.py
        if 'update_other' not in self.__rdisable:
            @bp.route('/sudo/update/<uid>', methods=['GET','POST'])
            @userpriv.role_required(self.__accesspriv['update_other'])
            def update_other(uid):
                return self.__return_update_other(uid)

        # this is defined in persistdb/withadmin.py
        if 'delete_other' not in self.__rdisable:
            @bp.route('/sudo/delete/<uid>')
            @userpriv.role_required(self.__accesspriv['delete_other'])
            def delete_other(uid):
                return self.__return_delete_other(uid)

        if 'roles' not in self.__rdisable:
            @bp.route('/roles')
            @userpriv.role_required(self.__accesspriv['roles'])
            def roles():
                rlist = self.__arclass.query.all()
                return render_template(self.__templ['roles'], data = rlist)

        if 'insert_role' not in self.__rdisable:
            @bp.route('/role/register', methods=['GET','POST'])
            @userpriv.role_required(self.__accesspriv['insert_role'])
            def insert_role():
                rbool, rscode = self.__insert_role()
                if rbool:
                    return self.__reroute('insert_role')
                form = self.__arclass._formgen_assist(self.session)
                return render_template(self.__templ['insert_role'], form=form), rscode

        if 'update_role' not in self.__rdisable:
            @bp.route('/role/update/<rid>', methods=['GET','POST'])
            @userpriv.role_required(self.__accesspriv['update_role'])
            def update_role(rid):
                r = self.__arclass.query.filter(self.__arclass.id == rid).first()
                if not r:
                    abort(400)
                rbool, rscode = self.__update_role(r)
                if rbool:
                    return self.__reroute('update_role')
                form = self.__arclass._formgen_assist(self.session)
                return render_template(self.__templ['update_role'], data=r, form=form), rscode

        if 'delete_role' not in self.__rdisable:
            @bp.route('/role/delete/<rid>')
            @userpriv.role_required(self.__accesspriv['delete_role'])
            def delete_role(rid):
                r = self.__arclass.query.filter(self.__arclass.id == rid).first()
                if not r:
                    abort(400)
                self.__delete_role(r)
                self.__reroute('delete_role')

        return bp
