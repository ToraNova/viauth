from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
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

class Arch:
    def __init__(self, templates = {'login':'login.html'}, reroutes = {'login':'home','logout':'viauth.login'} ):
        '''
        initialize the architecture for the vial
        templ is a dictionary that returns user specified templates to user on given routes
        reroutes is a dictionary that reroutes the user after certain actions on given routes
        '''
        self.__templ = templates
        self.__route = reroutes
        self.__userdict = {}

    def update_users(self, *uargs):
        '''
        a primitive way of updating users. this is non-dynamic (i.e., init_app or generate
        is called, the user list is STATIC!
        '''
        if len(uargs) == 1:
            if type(uargs[0]) == list:
                for i, u in enumerate(uargs[0]):
                    u.id = i
                    self.__userdict[u.name] = u
            else:
                u = uargs[0]
                u.id = i
                self.__userdict[u.name] = u
        else:
            for i, u in enumerate(uargs):
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
        return app

    def generate(self):
        @source.bp.route('/login', methods=['GET','POST'])
        def login():
            if(request.method == 'POST'):
                username = request.form.get('username')
                password = request.form.get('password')
                if not username or not password:
                    abort(400)
                if username in self.__userdict and\
                    self.__userdict[username].check_password(password):
                    login_user(self.__userdict[username])
                    return redirect(url_for(self.__route.get('login')))
                flash('invalid credentials','err')
            return render_template(self.__templ['login'])
        lman = LoginManager()

        @source.bp.route('/logout')
        def logout():
            logout_user()
            return redirect(url_for(self.__route['logout']))

        @lman.user_loader
        def loader(uid):
            u = self._find_byid(uid)
            u.is_authenticated = True
            return u

        @lman.unauthorized_handler
        def unauth():
            flash('please login first', 'err')
            return redirect(url_for('viauth.login'))

        return source.AppArch(source.bp, lman)
