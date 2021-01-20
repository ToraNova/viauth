'''
basic authentication (username, password)
no database systems, users defined by python scripts
'''

from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2.exceptions import TemplateNotFound
from viauth import vial

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
        self.__userdict = {} # only for basic
        self._urlprefix = url_prefix # typically not required by child classes

        self._templ = templates
        self._route = reroutes
        self._rkarg = reroutes_kwarg
        self._default_tp('login', 'login.html')
        self._default_tp('profile', 'profile.html')
        self._default_tp('unauth','unauth.html')
        self._default_rt('login', 'viauth.profile')
        self._default_rt('logout','viauth.login')
        self._callbacks = {
                'err': lambda msg : flash(msg, 'err'),
                'ok': lambda msg : flash(msg, 'ok'),
                'warn': lambda msg : flash(msg, 'warn'),
                'ex': lambda ex : flash("an exception (%s) has occurred: %s" % (type(ex).__name__, str(ex)), 'err'),
        }

    def set_callback(self, event, cbfunc):
        if not callable(cbfunc):
            raise TypeError("callback function should be callable")
        self._callbacks[event] = cbfunc

    def callback(self, event, *args):
        return self._callbacks[event](*args)

    # convenience functions
    def error(self, msg):
        self.callback('err', msg)

    def ok(self, msg):
        self.callback('ok', msg)

    def ex(self, e):
        self.callback('ex', e)

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

    def _reroute(self, fromkey):
        if self._rkarg.get(fromkey):
            return redirect(url_for(self._route[fromkey], **self._rkarg.get(fromkey)))
        else:
            return redirect(url_for(self._route[fromkey]))

    def _default_tp(self, key, value):
        if not self._templ.get(key):
            self._templ[key] = value

    def _default_rt(self, key, value):
        if not self._route.get(key):
            self._route[key] = value

    def __unauth(self):
        try:
            tpl = render_template(self._templ['unauth'])
            return tpl, 401
        except TemplateNotFound:
            return 'login required. please login at %s' % url_for('viauth.login', _external=True), 401

    def generate(self):
        bp = self._make_bp()
        lman = self._make_lman()
        return vial.AppArch(bp, lman)

    def _make_lman(self):
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

    def _make_bp(self):
        bp = vial.make_blueprint(self._urlprefix)

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
                    return self._reroute('login')
                self.error('invalid credentials')
                rscode = 401
            return render_template(self._templ['login']), rscode

        @bp.route('/profile')
        @login_required
        def profile():
            return render_template(self._templ['profile'])

        @bp.route('/logout')
        def logout():
            logout_user()
            return self._reroute('logout')

        return bp
