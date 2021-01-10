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

    arch = Arch(
        app.config['DBURI'],
        templates = {
            'users': 'ulist.html',
            'register_other': 'register.html',
            'update_other': 'update.html',
        },
        reroutes = {
            'login': 'home',
            'update_other': 'viauth.users',
            'delete_other': 'viauth.users',
            'register_other': 'viauth.users',
        },
        routes_disabled = ['delete']
    )

    arch.init_app(app)

    @app.route('/')
    def root():
        return redirect(url_for('viauth.login'))

    @app.route('/home')
    def home():
        return render_template('home.html')

    @app.route('/elevate')
    @login_required
    def set_admin():
        current_user.is_admin = True
        arch.session.add(current_user)
        arch.session.commit()
        return 'elevated.'

    # admin only
    @app.route('/treasure')
    @userpriv.admin_required
    def treasure():
        return 'you are an admin!'

    return app
