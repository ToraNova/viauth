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

class AuthUser(basic.AuthUser, sqlorm.Base):
    '''A basic user authentication account following flask-login
    extended with sqlalchemy ORM object classes'''
    __tablename__ = "authuser"
    id = Column(Integer, primary_key = True)
    name = Column(String(50),unique=True,nullable=False)
    passhash = Column(String(160),unique=False,nullable=False)
    is_active = Column(Boolean(),nullable=False) #used to disable accounts
    created_on = Column(DateTime()) #date of user account creation
    emailaddr = Column(String(254),unique=True,nullable=True)
    is_authenticated = False # default is false, unless the app sets to true

    @classmethod
    def create_table(cls, dburi):
        engine = sqlorm.make_engine(dburi)
        cls.__table__.create(engine, checkfirst=True)
        engine.dispose() #house keeping
        #sqlorm.Base.metadata.create_all(engine) #creates all the metadata

    def __init__(self, reqform):
        if len(reqform["username"]) < 1 or len(reqform["password"]) < 1:
            raise ValueError("invalid input length")
        super().__init__(reqform["username"], reqform["password"])
        self.created_on = datetime.datetime.now()
        self.update(reqform)

    def update(self, reqform):
        self.emailaddr = reqform.get("emailaddr")

'''
persistdb.Arch
templates: login, (register, profile, update)
reroutes: login, logout, unauth, (register, update)
'''
class Arch(basic.Arch):
    def __init__(self, dburi, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix=None, authuser_class=AuthUser):
        super().__init__(templates, reroutes, reroutes_kwarg, url_prefix)
        self.__default_tp('register', 'register.html')
        self.__default_tp('profile', 'profile.html')
        self.__default_tp('update', 'update.html')
        self.__default_rt('register', 'viauth.login') # go to login after registration
        self.__default_rt('update', 'viauth.profile') # go to profile after profile update
        assert self.__templ['register'] and self.__templ['profile'] and self.__templ['update']
        assert self.__route['register'] and self.__route['update']
        assert issubclass(authuser_class, AuthUser)
        self.__auclass = authuser_class
        self.session = sqlorm.connect(dburi)

    def init_app(self, app):
        apparch = self.generate()
        apparch.login_manager.init_app(app)
        app.register_blueprint(apparch.bp)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            self.session.remove()
        return app

    def __make_bp_lman(self):
        bp = source.make_blueprint(self.__urlprefix)
        lman = LoginManager()

        if(not hasattr(self, 'session')):
            raise AttributeError("db session unconfigured.")
        @bp.route('/login', methods=['GET','POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                if not username or not password:
                    abort(400)
                u = self.__auclass.query.filter(self.__auclass.name == username).first()
                if u and u.check_password(password):
                    login_user(u)
                    return self.__reroute('login')
                source.emflash('invalid credentials')
            return render_template(self.__templ['login'])

        @bp.route('/register', methods=['GET','POST'])
        def register():
            if request.method == 'POST':
                try:
                    newuser = self.__auclass(request.form)
                    self.session.add(newuser)
                    self.session.commit()
                    source.sflash('successfully registered')
                    return self.__reroute('register')
                except IntegrityError as e:
                    self.session.rollback()
                    source.emflash('username/email-address is taken')
                except Exception as e:
                    source.eflash(e)
            return render_template(self.__templ['register'])

        # update self
        @bp.route('/update', methods=['GET','POST'])
        @login_required
        def update():
            if request.method == 'POST':
                if request.form.get('is_admin'):
                    # normal user can't elevate themselves
                    abort(403) # no permission
                u = AuthUser.query.filter(AuthUser.id == current_user.id).first()
                try:
                    u.update(request.form)
                    self.session.add(u)
                    self.session.commit()
                    source.emflash('profile updated')
                    return self.__reroute('update')
                except Exception as e:
                    self.session.rollback()
                    source.eflash(e)
            return render_template(self.__templ['update'])

        @bp.route('/delete')
        @login_required
        def delete():
            try:
                tar = AuthUser.query.filter(AuthUser.id == current_user.id).first()
                if not tar:
                    abort(400)
                self.session.delete(tar)
                self.session.commit()
                source.emflash('account deleted')
                return redirect(url_for('viauth.logout'))
            except Exception as e:
                self.session.rollback()
                source.eflash(e)
                return redirect(url_for('viauth.profile'))

        @bp.route('/profile')
        @login_required
        def profile():
            return render_template(self.__templ['profile'])

        @bp.route('/logout')
        def logout():
            logout_user()
            source.sflash('logged out')
            return self.__reroute('logout')

        @lman.user_loader
        def loader(uid):
            u = self.__auclass.query.filter(self.__auclass.id == uid).first()
            if u:
                u.is_authenticated = True
                return u
            return None

        @lman.unauthorized_handler
        def unauth():
            source.emflash('unauthorized access')
            return self.__reroute('unauth')

        return bp, lman
