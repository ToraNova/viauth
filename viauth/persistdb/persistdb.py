'''
persistdb.py: sqlalchemy extension for basic.py
expect database system (interact with sqlalchemy)
'''
import datetime
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import source, basic, sqlorm, userpriv
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.exc import IntegrityError

class AuthUser(basic.AuthUser, sqlorm.ViAuthBase, sqlorm.Base):
    '''A basic user authentication account following flask-login
    extended with sqlalchemy ORM object classes'''
    __tablename__ = "authuser"
    id = Column(Integer, primary_key = True)
    name = Column(String(50),unique=True,nullable=False)
    passhash = Column(String(160),unique=False,nullable=False)
    is_active = Column(Boolean(),nullable=False) #used to disable accounts
    created_on = Column(DateTime()) #date of user account creation
    updated_on = Column(DateTime()) #updated time
    emailaddr = Column(String(254),unique=True,nullable=True)
    is_authenticated = False # default is false, unless the app sets to true

    def elevation_policy_check(self, orig):
        if not self.is_active == orig.is_active:
            # self activation/deactivation not permitted
            source.emflash("self activation/deactivation not permitted")
            return False
        return True

    def __init__(self, reqform):
        if len(reqform["username"]) < 1 or len(reqform["password"]) < 1:
            raise ValueError("invalid input length")
        super().__init__(reqform["username"], reqform["password"])
        self.created_on = datetime.datetime.now()
        self.updated_on = self.created_on
        self.emailaddr = reqform.get("emailaddr")

    # user self update (beware, no privilege or role changing here)
    def self_update(self, reqform):
        self.updated_on = datetime.datetime.now()
        self.emailaddr = reqform.get("emailaddr")

'''
persistdb.Arch
templates: login, profile, unauth, (register, update)
reroutes: login, logout, (register, update)
'''
class Arch(basic.Arch):
    def __init__(self, dburi, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser, route_disabled = []):
        assert issubclass(authuser_class, AuthUser)
        super().__init__(templates, reroutes, reroutes_kwarg, url_prefix)
        self.__default_tp('register', 'register.html')
        self.__default_tp('update', 'update.html')
        self.__default_rt('register', 'viauth.login') # go to login after registration
        self.__default_rt('update', 'viauth.profile') # go to profile after profile update
        self.__auclass = authuser_class
        self.__rdisable = route_disabled
        self.session = sqlorm.connect(dburi)

    def init_app(self, app):
        apparch = self.generate()
        apparch.login_manager.init_app(app)
        app.register_blueprint(apparch.bp)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            self.session.remove()
        return app

    # override basic's generate with session check
    def generate(self):
        bp = self.__make_bp()
        lman = self.__make_lman()
        if(not hasattr(self, 'session')):
            raise AttributeError("sql session unconfigured.")
        return source.AppArch(bp, lman)

    def __login(self):
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                abort(400)
            u = self.__auclass.query.filter(self.__auclass.name == username).first()
            if u and u.check_password(password):
                login_user(u)
                return True
            source.emflash('invalid credentials')
        return False

    def __register(self):
        if request.method == 'POST':
            try:
                u = self.__auclass(request.form)
                self.session.add(u)
                self.session.commit()
                source.sflash('successfully registered')
                return True
            except IntegrityError as e:
                self.session.rollback()
                source.emflash('username/email-address is taken')
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
        return False

    def __update(self):
        if request.method == 'POST':
            try:
                orig = self.__auclass.query.filter(self.__auclass.id == current_user.id).first()
                current_user.self_update(request.form)
                self.session.add(current_user)
                self.session.commit()
                source.emflash('user profile updated')
                return True
            except IntegrityError as e:
                self.session.rollback()
                source.emflash('integrity error')
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
        return False

    def __delete(self):
        try:
            current_user.delete()
            self.session.delete(current_user)
            self.session.commit()
            source.emflash('account deleted')
            return True
        except Exception as e:
            self.session.rollback()
            source.eflash(e)
        return False

    def __make_lman(self):
        lman = LoginManager()

        @lman.user_loader
        def loader(uid):
            u = self.__auclass.query.filter(self.__auclass.id == uid).first()
            if u:
                u.is_authenticated = True
                return u
            return None

        @lman.unauthorized_handler
        def unauth():
            return self.__unauth()

        return lman

    def __make_bp(self):
        bp = source.make_blueprint(self.__urlprefix)

        # register self
        if 'register' not in self.__rdisable:
            @bp.route('/register', methods=['GET','POST'])
            def register():
                if self.__register():
                    return self.__reroute('register')
                form = self.__auclass.formgen_assist(self.session)
                return render_template(self.__templ['register'], form = form)

        # update self
        if 'update' not in self.__rdisable:
            @bp.route('/update', methods=['GET','POST'])
            @login_required
            def update():
                if self.__update():
                    return self.__reroute('update')
                form = self.__auclass.formgen_assist(self.session)
                return render_template(self.__templ['update'], form = form)

        if 'delete' not in self.__rdisable:
            @bp.route('/delete')
            @login_required
            def delete():
                if self.__delete():
                    return redirect(url_for('viauth.logout'))
                return redirect(url_for('viauth.profile'))

        if 'profile' not in self.__rdisable:
            @bp.route('/profile')
            @login_required
            def profile():
                return render_template(self.__templ['profile'])

        # the login route cannot be disabled
        @bp.route('/login', methods=['GET','POST'])
        def login():
            if self.__login():
                return self.__reroute('login')
            return render_template(self.__templ['login'])

        @bp.route('/logout')
        def logout():
            logout_user()
            return self.__reroute('logout')

        return bp
