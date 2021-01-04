'''
basic authentication (username, password)
no database systems, users defined by python scripts
'''

from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2.exceptions import TemplateNotFound
from viauth import source

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
class Arch:
    def __init__(self, templates = {}, reroutes = {}, reroutes_kwarg = {}, url_prefix = None):
        '''
        initialize the architecture for the vial
        templ is a dictionary that returns user specified templates to user on given routes
        reroutes is a dictionary that reroutes the user after certain actions on given routes
        '''
        self.__templ = templates
        self.__route = reroutes
        self.__rkarg = reroutes_kwarg
        self.__default_tp('login', 'login.html')
        self.__default_tp('profile', 'profile.html')
        self.__default_tp('unauth','unauth.html')
        self.__default_rt('login', 'viauth.profile')
        self.__default_rt('logout','viauth.login')
        self.__urlprefix = url_prefix
        self.__userdict = {}

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
        apparch = self.generate()
        apparch.login_manager.init_app(app)
        app.register_blueprint(apparch.bp)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            pass

        return app

    def __reroute(self, fromkey):
        if self.__rkarg.get(fromkey):
            return redirect(url_for(self.__route[fromkey], **self.__rkarg.get(fromkey)))
        else:
            return redirect(url_for(self.__route[fromkey]))

    def __default_tp(self, key, value):
        if not self.__templ.get(key):
            self.__templ[key] = value

    def __default_rt(self, key, value):
        if not self.__route.get(key):
            self.__route[key] = value

    def __unauth(self):
        try:
            tpl = render_template(self.__templ['unauth'])
            return tpl
        except TemplateNotFound:
            return 'login required.'

    def generate(self):
        bp = self.__make_bp()
        lman = self.__make_lman()
        return source.AppArch(bp, lman)

    def __make_lman(self):
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

    def __make_bp(self):
        bp = source.make_blueprint(self.__urlprefix)

        @bp.route('/login', methods=['GET','POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                if not username or not password:
                    abort(400)
                if username in self.__userdict and\
                    self.__userdict[username].check_password(password):
                    login_user(self.__userdict[username])
                    return self.__reroute('login')
                source.emflash('invalid credentials')
            return render_template(self.__templ['login'])

        @bp.route('/profile')
        @login_required
        def profile():
            return render_template(self.__templ['profile'])

        @bp.route('/logout')
        def logout():
            logout_user()
            return self.__reroute('logout')

        return bp
