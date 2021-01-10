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
        rscode = 200
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                abort(400)
            u = self.__auclass.query.filter(self.__auclass.name == username).first()
            if u and u.check_password(password):
                try:
                    u.login() # runs the login callback
                    self.session.add(u)
                    self.session.commit()
                    login_user(u) # flask-login do the rest
                    self.ok('login successful')
                    return True, None
                except Exception as e:
                    self.ex(e)
                self.session.rollback()
            else:
                self.error('invalid credentials')
                rscode = 401
        return False, rscode

    def __logout(self):
        try:
            current_user.logout() # runs the logout callback
            self.session.add(current_user)
            self.session.commit()
            logout_user()
            self.ok('logout successful')
            return True # success
        except Exception as e:
            self.ex(e)
        self.session.rollback()
        return False # fail

    def __register(self):
        rscode = 200
        if request.method == 'POST':
            try:
                u = self.__auclass(request.form) # create the user
                self.session.add(u)
                self.session.commit()
                self.ok('successfully registered')
                return True, None # success
            except IntegrityError as e:
                self.error('registration unavailable')
                rscode = 409
            except Exception as e:
                self.ex(e)

            self.session.rollback()
        return False, rscode # fail

    def __update(self):
        rscode = 200
        if request.method == 'POST':
            try:
                current_user.update(request.form) # runs the update callback
                self.session.add(current_user)
                self.session.commit()
                self.ok('user profile updated')
                return True, None # success
            except IntegrityError as e:
                self.error('integrity error')
                rscode = 409
            except Exception as e:
                self.ex(e)
            self.session.rollback()
        return False, rscode # fail

    def __delete(self):
        try:
            current_user.delete() # runs the delete callback
            self.session.delete(current_user)
            self.session.commit()
            self.ok('account deleted')
            return True # success
        except Exception as e:
            self.ex(e)
        self.session.rollback()
        return False # fail

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
                rbool, rscode = self.__register()
                if rbool:
                    return self.__reroute('register')
                form = self.__auclass._formgen_assist(self.session)
                return render_template(self.__templ['register'], form = form), rscode

        # update self
        if 'update' not in self.__rdisable:
            @bp.route('/update', methods=['GET','POST'])
            @login_required
            def update():
                rbool, rscode = self.__update()
                if rbool:
                    return self.__reroute('update')
                form = self.__auclass._formgen_assist(self.session)
                return render_template(self.__templ['update'], form = form), rscode

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
            rbool, rscode = self.__login()
            if rbool:
                return self.__reroute('login')
            return render_template(self.__templ['login']), rscode

        @bp.route('/logout')
        def logout():
            if self.__logout():
                return self.__reroute('logout')
            return redirect(url_for('viauth.profile'))

        return bp
