'''
basic authentication (username, password)
no database systems, users defined by python scripts
'''

from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2.exceptions import TemplateNotFound
from vicore import BaseArch, AppArchExt

class AuthUser:
    '''A basic user authentication account following flask-login'''

    def __init__(self, name, password):
        self.set_password(password)
        self.name = name
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)

    def set_password(self, password, method ='pbkdf2:sha512', saltlen = 16 ):
        self.passhash=generate_password_hash(password, method=method, salt_length=saltlen)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

'''
basic.Arch
templates: login, profile, unauth
reroutes: login, logout
'''
class Arch(BaseArch):
    def __init__(self, templates = {}, reroutes = {}, reroutes_kwarg = {}, rex_callback = {}, url_prefix = None):
        '''
        initialize the architecture for the vial
        templ is a dictionary that returns user specified templates to user on given routes
        reroutes is a dictionary that reroutes the user after certain actions on given routes
        '''
        super().__init__('viauth', templates, reroutes, reroutes_kwarg, rex_callback, url_prefix)
        self.__userdict = {} # only for basic
        self._default_tp('login', 'login.html')
        self._default_tp('profile', 'profile.html')
        self._default_tp('unauth','unauth.html')
        self._default_rt('login', 'viauth.profile')
        self._default_rt('logout','viauth.login')

    def update_users(self, ulist):
        '''
        a primitive way of updating users. this is non-dynamic (i.e., init_app or generate
        is called, the user list is STATIC!
        '''
        for i, u in enumerate(ulist):
            u.id = i
            self.__userdict[u.name] = u

    def _find_byid(self, uid):
        for u in self.__userdict.values():
            if uid == u.get_id():
                return u

    def init_app(self, app):
        apparch = self.generate_apparch()
        apparch.ext.init_app(app)
        app.register_blueprint(apparch.bp)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            pass

        return app

    def __unauth(self):
        try:
            tpl = render_template(self._templ['unauth'])
            return tpl, 401
        except TemplateNotFound:
            return 'login required. please login at %s' % url_for('viauth.login', _external=True), 401

    def generate_apparch(self):
        bp = self.generate_blueprint()
        lman = self.generate_lman()
        return AppArchExt(bp, lman)

    def generate_lman(self):
        lman = LoginManager()

        @lman.unauthorized_handler
        def unauth():
            return self.__unauth()

        @lman.user_loader
        def loader(uid):
            u = self._find_byid(uid)
            u.is_authenticated = True
            return u

        return lman

    def generate_blueprint(self):
        bp = self._init_bp()

        @bp.route('/login', methods=['GET','POST'])
        def login():
            rscode = 200
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                if not username or not password:
                    abort(400)
                if username in self.__userdict and\
                    self.__userdict[username].check_password(password):
                    login_user(self.__userdict[username])
                    self.ok('login', 'login success')
                    return self._reroute('login')
                self.err('login', 'invalid credentials')
                rscode = 401
            return render_template(self._templ['login']), rscode

        @bp.route('/profile')
        @login_required
        def profile():
            return render_template(self._templ['profile'])

        @bp.route('/logout')
        def logout():
            logout_user()
            self.ok('logout', 'logout success')
            return self._reroute('logout')

        return bp
