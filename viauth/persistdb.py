'''
persistdb.py: sqlalchemy extension for basic.py
expect database system (interact with sqlalchemy)
'''
import datetime
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from viauth import source, basic, sqlorm
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

    def create_table(dburi):
        engine = sqlorm.make_engine(dburi)
        AuthUser.__table__.create(engine)
        engine.dispose() #house keeping
        #sqlorm.Base.metadata.create_all(engine) #creates all the metadata

    def __init__(self, reqform):
        if len(reqform["username"]) < 1 or len(reqform["password"]) < 1:
            raise ValueError("invalid input length")
        super().__init__(reqform["username"], reqform["password"])
        self.created_on = datetime.datetime.now()
        self.emailaddr = reqform.get("emailaddr")

    def create_user(name, email, password, form):
        '''this function should be overridden if using custom authuser class'''
        return AuthUser(name, email, password)

class Arch:
    def __init__(self, templates = {'login':'login.html'}, reroutes = {'login':'home','logout':'viauth.login'} ):
        '''
        initialize the architecture for the vial
        templ is a dictionary that returns user specified templates to user on given routes
        reroutes is a dictionary that reroutes the user after certain actions on given routes
        '''
        self.__templ = templates
        self.__route = reroutes
        self.__auclass = AuthUser

    def configure_db(self, dburi):
        self.session = sqlorm.connect(dburi)

    def set_authuserclass(self, auclass):
        assert issubclass(auclass, AuthUser)
        self.__auclass = auclass

    def init_app(self, app):
        apparch = self.generate()
        apparch.login_manager.init_app(app)
        app.register_blueprint(apparch.bp)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            self.session.remove()
        return app

    def generate(self):
        bp = source.make_blueprint()

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
                    return redirect(url_for(self.__route['login']))
                source.emflash('invalid credentials')
            return render_template(self.__templ['login'])
        lman = LoginManager()

        @bp.route('/register', methods=['GET','POST'])
        def register():
            if request.method == 'POST':
                try:
                    newuser = self.__auclass(request.form)
                    self.session.add(newuser)
                    self.session.commit()
                    source.sflash('successfully registered')
                    return redirect(url_for(self.__route['register']))
                except IntegrityError as e:
                    self.session.rollback()
                    source.emflash('username/email-address is taken')
                except Exception as e:
                    source.eflash(e)
            return render_template(self.__templ['register'])

        @bp.route('/profile')
        @login_required
        def profile():
            return render_template(self.__templ['profile'])

        @bp.route('/logout')
        def logout():
            logout_user()
            return redirect(url_for(self.__route['logout']))

        @lman.user_loader
        def loader(uid):
            u = self.__auclass.query.filter(self.__auclass.id == uid).first()
            if u:
                u.is_authenticated = True
                return u
            return None

        @lman.unauthorized_handler
        def unauth():
            source.emflash('please login first')
            return redirect(url_for('viauth.login'))

        return source.AppArch(bp, lman)
