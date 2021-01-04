'''
simple admin based architecture. allows admin users which can edit
the role of others. This is based off persistdb
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = simpleadmin
flask run
'''
from flask import Flask, render_template, redirect, url_for, request
from viauth.persistdb.withadmin import Arch, AuthUser
from flask_login import login_required, current_user
from viauth import userpriv

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'v3rypowerfuls3cret, or not. CHANGE THIS!@'
    app.config['DBURI'] = 'sqlite:///watmp.db'
    app.testing = False
    if test_config:
        app.config.from_mapping(test_config)

    # create table
    try:
        AuthUser.create_table(app.config['DBURI'])
    except Exception as e:
        #print(e)
        pass

    # define a place to find the templates
    # set url_prefix = '/' to have no url_prefix, leaving it empty will prefix with viauth
    # the templates and reroutes may be left empty, in which case they will default
    # if rerouting needs additiona kwarg, use reroutes_kwarg
    #
    # persistdb.Arch
    # templates: login, (register, profile, users, update, update_other)
    # reroutes: login, logout, unauth, (register, update)
    arch = Arch(
        app.config['DBURI'],
        templates = {
            'login':'login.html',
            'register':'signup.html',
            'profile':'profile.html',
            'users': 'ulist.html',
            'update_other': 'admin_edit.html'
        },
        reroutes = {
            'logout':'viauth.login',
            'register':'viauth.login',
            'update_other': 'viauth.users',
            'delete_other': 'viauth.users',
            'register_other': 'viauth.users'
        },
        reroutes_kwarg = {'login': {'test':'1'}},
        route_disabled = ['update']
    )

    arch.init_app(app)

    @app.route('/')
    def root():
        return redirect(url_for('viauth.login'))

    # testing kwargs as well here
    @app.route('/home/<test>')
    @login_required
    def home(test):
        return render_template('home.html')

    @app.route('/set_admin')
    @login_required
    def set_admin():
        current_user.is_admin = True
        arch.session.add(current_user)
        arch.session.commit()
        return 'ok'

    # admin only
    # to add the first admin, edit is_admin directly from database, or insert upon database creation
    @app.route('/admin_secret')
    @userpriv.admin_required
    def admin_secret():
        return 'you are an admin!'

    return app
