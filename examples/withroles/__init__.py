'''
simple admin based architecture. allows admin users which can edit
the role of others. This is based off persistdb
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = simpleadmin
flask run
'''
from flask import Flask, render_template, redirect, url_for, request
from viauth.persistdb.withroles import Arch, AuthUser, AuthRole
from flask_login import login_required, current_user
from viauth import userpriv

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'v3rypowerfuls3cret, or not. CHANGE THIS!@'
    app.config['DBURI'] = 'sqlite:///wrtmp.db'
    app.testing = False
    if test_config:
        app.config.from_mapping(test_config)

    addflag = not AuthRole.table_exists(app.config['DBURI'])

    # create table
    try:
        AuthUser.create_table(app.config['DBURI'])
        AuthRole.create_table(app.config['DBURI'])
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
            'roles': 'roles.html',
            'insert_role': 'new_role.html',
            'update_role': 'edit_role.html',
            'register_other': 'register.html',
            'update_other': 'update.html',
        },
        reroutes = {
            'login': 'viauth.profile'
        }
    )

    arch.init_app(app)

    if addflag:
        for r in [{"name":"admin","level":0,"is_admin":True}, {"name":"peasant","level":4,"is_admin":False}, {"name":"premium","level":3,"is_admin":False}, {"name":"testdel","level":5,"is_admin":False}]:
            nr = AuthRole(r)
            arch.session.add(nr)
        arch.session.commit()

    @app.route('/')
    def root():
        return redirect(url_for('viauth.login'))

    @app.route('/content')
    @userpriv.role_required('premium')
    def content():
        return 'premium content.'

    @app.route('/nopay')
    @login_required
    def unpay():
        current_user.rid = None
        arch.session.add(current_user)
        arch.session.commit()
        return 'premium account deactivated.'

    @app.route('/elevate')
    @userpriv.level_atmost(3) # same as requiring premium user
    def set_admin():
        current_user.rid = 1
        arch.session.add(current_user)
        arch.session.commit()
        return 'elevated.'

    @app.route('/pay')
    @login_required
    def pay():
        pr = AuthRole.query.filter(AuthRole.name == "premium").first()
        if not pr:
            abort(500)
        current_user.rid = pr.id
        arch.session.add(current_user)
        arch.session.commit()
        return 'premium account activated.'

    return app
