'''
persistdb.py: sqlalchemy extension for basic.py
expect database system (interact with sqlalchemy)
'''

import datetime
from flask import render_template, request, redirect, abort, flash, url_for, Blueprint
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from vicore import AppArchExt, sqlorm, formutil
from viauth import basic, userpriv
from sqlalchemy import Column, Integer, String, Boolean, DateTime, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr

class AuthUserMixin(basic.AuthUser, sqlorm.Core):
    '''A basic user authentication account following flask-login
    extended with sqlalchemy ORM object classes'''

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key = True)

    @declared_attr
    def name(cls):
        return Column(String(50),unique=True,nullable=False)

    @declared_attr
    def passhash(cls):
        return Column(String(160),unique=False,nullable=False)

    @declared_attr
    def is_active(cls):
        return Column(Boolean(),nullable=False) #used to disable accounts

    @declared_attr
    def created_on(cls):
        return Column(DateTime()) #date of user account creation

    @declared_attr
    def updated_on(cls):
        return Column(DateTime()) #updated time

    is_authenticated = False # default is false, unless the app sets to true

    def __init__(self, reqform):
        if len(reqform["username"]) < 1 or len(reqform["password"]) < 1:
            raise ValueError("invalid input length")
        super().__init__(reqform["username"], reqform["password"])
        self.created_on = datetime.datetime.now()
        self.updated_on = self.created_on

    # login callback
    def login(self):
        pass

    # logout callback
    def logout(self):
        pass

    # user self update
    def update(self, reqform):
        self.updated_on = datetime.datetime.now()

    # user self delete callback
    def delete(self):
        pass

class AuthUser(AuthUserMixin, sqlorm.Base):
    __tablename__ = "authuser"
    # This prevents errors,
    # BUT DO NOT USE UNDER NORMAL CIRCUMSTANCES AS IT MAY INDICATE MULTIPLE DEFINITIONS
    __table_args__ = {'extend_existing': True}

    def __init__(self, reqform):
        super().__init__(reqform)

'''
persistdb.Arch
templates: login, profile, unauth, (register, update)
reroutes: login, logout, (register, update)
'''
class Arch(basic.Arch):
    def __init__(self, dburi, ormbase = sqlorm.Base, templates = {}, reroutes = {}, reroutes_kwarg = {}, rex_callback={}, url_prefix=None, authuser_class=AuthUser, routes_disabled = [], login_key = {}):
        assert issubclass(authuser_class, AuthUserMixin)
        super().__init__(templates, reroutes, reroutes_kwarg, rex_callback, url_prefix)
        self._default_tp('register', 'register.html')
        self._default_tp('update', 'update.html')
        self._default_rt('register', 'viauth.login') # go to login after registration
        self._default_rt('update', 'viauth.profile') # go to profile after profile update
        self._auclass = authuser_class
        self._rdisable = routes_disabled
        self.session = sqlorm.connect(dburi, ormbase)
        self.set_loginkey(login_key)

    def set_loginkey(self, login_key):
        if not login_key.get('match'):
            login_key['match'] = {'attr': 'name', 'form':'username'}
        if login_key['match'].get('type') == 'multi_attr':
            t = type(login_key['match']['attr'])
            if t is not list and t is not tuple:
                raise TypeError('matching type multi_attr on login_key requires attr to be either list or tuple. type: %s' % t)
            if len(login_key['match']['attr']) < 2:
                raise AttributeError('matching type multi_attr on login_key should have at least 2 attribute.')
        self._loginkey = login_key

    def init_app(self, app):
        apparch = self.generate_apparch()
        apparch.ext.init_app(app)
        app.register_blueprint(apparch.bp)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            self.session.remove()
        return app

    # override basic's generate with session check
    def generate_apparch(self):
        bp = self.generate_blueprint()
        lman = self.generate_lman()
        if(not hasattr(self, 'session')):
            raise AttributeError("sql session unconfigured.")
        return AppArchExt(bp, lman)

    def __login(self):
        rscode = 200
        if request.method == 'POST':
            match = request.form.get(self._loginkey['match']['form'])
            password = request.form.get('password')
            if not match or not password:
                abort(400)

            if self._loginkey['match'].get('type') == 'multi_attr':
                # single form value to match with multiple attribute
                # use case include smth like, login with email OR username
                for a in self._loginkey['match']['attr']:
                    u = self._auclass.query.filter(getattr(self._auclass, a) == match).first()
                    if u:
                        break
            else:
                # single type matching. default to self._auclass.name == form['username']
                a = self._loginkey['match']['attr']
                if type(a) == list or type(a) == tuple:
                    a = a[0]
                u = self._auclass.query.filter(getattr(self._auclass, a)  == match).first()

            if u and u.check_password(password):
                try:
                    u.login() # runs the login callback
                    self.session.add(u)
                    self.session.commit()
                    login_user(u) # flask-login do the rest
                    self.ok('login', 'login success.')
                    return True, None
                except Exception as e:
                    self.ex('login', e)
                self.session.rollback()
            else:
                self.err('login', 'invalid credentials.')
                rscode = 401
        return False, rscode

    def __logout(self):
        try:
            current_user.logout() # runs the logout callback
            self.session.add(current_user)
            self.session.commit()
            logout_user()
            self.ok('logout', 'logout success.')
            return True # success
        except Exception as e:
            self.ex('logout', e)
        self.session.rollback()
        return False # fail

    def __register(self):
        rscode = 200
        if request.method == 'POST':
            try:
                u = self._auclass(request.form) # create the user
                self.session.add(u)
                self.session.commit()
                self.ok('register', 'successfully registered user account.')
                return True, None # success
            except IntegrityError as e:
                self.err('register', 'registration unavailable.')
                rscode = 409
            except Exception as e:
                self.ex('register', e)
            self.session.rollback()
        return False, rscode # fail

    def __update(self):
        rscode = 200
        if request.method == 'POST':
            try:
                current_user.update(request.form) # runs the update callback
                self.session.add(current_user)
                self.session.commit()
                self.ok('update', 'successfully updated user account.')
                return True, None # success
            except IntegrityError as e:
                self.err('update', 'integrity error.')
                rscode = 409
            except Exception as e:
                self.ex('update', e)
            self.session.rollback()
        return False, rscode # fail

    def __delete(self):
        try:
            current_user.delete() # runs the delete callback
            self.session.delete(current_user)
            self.session.commit()
            self.ok('delete', 'successfully deleted user account.')
            return True # success
        except Exception as e:
            self.ex('delete', e)
        self.session.rollback()
        return False # fail

    def generate_lman(self):
        lman = LoginManager()

        @lman.user_loader
        def loader(uid):
            u = self._auclass.query.filter(self._auclass.id == uid).first()
            if u:
                u.is_authenticated = True
                return u
            return None

        @lman.unauthorized_handler
        def unauth():
            return self.__unauth()

        return lman

    def generate_blueprint(self):
        bp = self._init_bp()

        # register self
        if 'register' not in self._rdisable:
            @bp.route('/register', methods=['GET','POST'])
            def register():
                rbool, rscode = self.__register()
                if rbool:
                    return self._reroute('register')
                fauxd = self._auclass.form_auxdata_generate(self.session)
                return render_template(self._templ['register'], form_auxd = fauxd ), rscode

        # update self
        if 'update' not in self._rdisable:
            @bp.route('/update', methods=['GET','POST'])
            @login_required
            def update():
                rbool, rscode = self.__update()
                if rbool:
                    return self._reroute('update')
                fauxd = self._auclass.form_auxdata_generate(self.session)
                return render_template(self._templ['update'], form_auxd = fauxd ), rscode

        if 'delete' not in self._rdisable:
            @bp.route('/delete')
            @login_required
            def delete():
                if self.__delete():
                    return redirect(url_for('viauth.logout'))
                return redirect(url_for('viauth.profile'))

        if 'profile' not in self._rdisable:
            @bp.route('/profile')
            @login_required
            def profile():
                return render_template(self._templ['profile'])

        # the login route cannot be disabled
        @bp.route('/login', methods=['GET','POST'])
        def login():
            rbool, rscode = self.__login()
            if rbool:
                return self._reroute('login')
            return render_template(self._templ['login']), rscode

        @bp.route('/logout')
        def logout():
            if current_user.is_authenticated:
                if self.__logout():
                    return self._reroute('logout')
                return redirect(url_for('viauth.profile')) # logout failure LOL
            self.err('logout', 'not logged in.')
            return redirect(url_for('viauth.login'))

        return bp
