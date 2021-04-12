'''
basic example using the default AuthUser from the persistdb type
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = persistdb
flask run
'''
from flask import Flask, render_template, redirect, url_for, request, flash
from viauth.persistdb import Arch, AuthUser
from flask_login import login_required, current_user

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'v3rypowerfuls3cret, or not. CHANGE THIS!@'
    app.config['DBURI'] = 'sqlite:///pdtmp.db'
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
        # use 'signup.html' instead of 'register.html' for registration template
        # likewise for 'update' route
        templates = {
            'register':'signup.html',
            'update':'edit.html',
            },
        # when login success, reroute to 'home'
        reroutes= {
            'login':'home',
            },
        # run custom user callback when 'logout' is successful.
        # flashses off you GO! instead of the usual 'logout success'
        rex_callback = {
            'logout':{'ok':lambda *args, **kwargs: flash('off you GO!','ok')},
            },
    )

    # example of setting a callback for 'exception' event
    arch.init_app(app)

    @app.route('/')
    def root():
        return redirect(url_for('viauth.login'))

    @app.route('/home')
    @login_required
    def home():
        return render_template('home.html')

    @app.route('/users')
    @login_required
    def users():
        ulist = AuthUser.query.all()
        return render_template('users.html', data=ulist)

    # obtain session using arch.session

    return app
