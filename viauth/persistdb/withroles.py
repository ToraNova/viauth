'''
withroles.py: extension of persistdb and persistdb.withadmin, with role-based accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import source, sqlorm, userpriv
from viauth.persistdb import withadmin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

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

    def formgen_assist(session):
        return AuthRole.query.all()

    def __init__(self, reqform):
        super().__init__(reqform)
        self.rid = None # user start with no role

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
    def __init__(self, dburi, access_priv = {}, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser, authrole_class=AuthRole):
        assert issubclass(authuser_class, AuthUser)
        assert issubclass(authrole_class, AuthRole)
        super().__init__(dburi, templates, reroutes, reroutes_kwarg, url_prefix, authuser_class)
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
        if request.method == 'POST':
            try:
                r = self.__arclass(request.form)
                self.session.add(r)
                self.session.commit()
                source.sflash('role created')
                return True
            except IntegrityError as e:
                self.session.rollback()
                source.emflash('role already exists')
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
        return False

    def __update_role(self, rid):
        r = self.__arclass.query.filter(self.__arclass.id == rid).first()
        if not r:
            abort(400)
        if request.method == 'POST':
            try:
                r.update(request.form)
                self.session.add(r)
                self.session.commit()
                source.emflash('role updated')
                return True
            except IntegrityError as e:
                self.session.rollback()
                source.emflash('role already exists')
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
        return False

    def __delete_role(self, rid):
        try:
            r = self.__arclass.query.filter(self.__arclass.id == rid).first()
            if not r:
                abort(400)
            r.delete()
            self.session.delete(r)
            self.session.commit()
            source.emflash('role deleted')
            return True
        except Exception as e:
            self.session.rollback()
            source.eflash(e)
            return False

    def __make_bp(self):
        bp = super(withadmin.Arch, self).__make_bp() #calling grandparent function

        # this is defined in persistdb/withadmin.py
        @bp.route('/register_other')
        @userpriv.role_required(self.__accesspriv['register_other'])
        def register_other():
            return super().__register_other()

        # this is defined in persistdb/withadmin.py
        @bp.route('/users')
        @userpriv.role_required(self.__accesspriv['users'])
        def users():
            return super().__users()

        # this is defined in persistdb/withadmin.py
        @bp.route('/update/<uid>', methods=['GET','POST'])
        @userpriv.role_required(self.__accesspriv['update_other'])
        def update_other(uid):
            return super().__update_other(uid)

        # this is defined in persistdb/withadmin.py
        @bp.route('/delete_other/<uid>')
        @userpriv.role_required(self.__accesspriv['delete_other'])
        def delete_other(uid):
            return super().__delete_other(uid)

        @bp.route('/roles')
        @userpriv.role_required(self.__accesspriv['roles'])
        def roles():
            rlist = self.__arclass.query.all()
            return render_template(self.__templ['roles'], data = rlist)

        @bp.route('/insert_role', methods=['GET','POST'])
        @userpriv.role_required(self.__accesspriv['insert_role'])
        def insert_role():
            if self.__insert_role():
                return self.__reroute('insert_role')
            return render_template(self.__templ['insert_role'])

        @bp.route('/update_role/<rid>', methods=['GET','POST'])
        def update_role(rid):
            if self.__update_role(rid):
                return self.__reroute('update_role')
            return render_template(self.__templ['update_role'])

        @bp.route('/delete_role/<rid>')
        def delete_role(rid):
            self.__delete_role(rid)
            self.__reroute('delete_role')

        return bp
