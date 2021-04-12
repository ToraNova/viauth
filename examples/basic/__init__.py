'''
an absolute basic auth architecture
to run:
(in virtualenv @ examples/)
export FLASK_APP=basic
flask run
'''
from flask import Flask, render_template, redirect, url_for, flash
from viauth.basic import Arch, AuthUser
from flask_login import login_required

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'v3rypowerfuls3cret, or not. CHANGE THIS!@'
    app.testing = False
    if test_config:
        app.config.from_mapping(test_config)

    arch = Arch(
        # load login.html for login, home.html for profile and nope.html if unauthenticated
        templates = {
            'login':'login.html',
            'profile':'home.html',
            'unauth':'nope.html',
        },
        # this is same as default, routing to user's profile upon login
        reroutes = {
            'login':'viauth.profile',
            'logout': 'reroute_with_kwarg',
        },
        # if reroute requires additional args on the url_for function call
        # indicate reroute on logout, pass '123' to 'test' on route 'reroute_with_kwarg'
        reroutes_kwarg = {
            'logout': {'test': '123'}
        },
        # use /basic/login.
        # leaving it empty will prefix with /viauth on AUTH-based url (login, logout and profile)
        url_prefix = '/basic'
    )

    u1 = AuthUser('jason','test123')
    u2 = AuthUser('ting','hello')
    arch.update_users([u1, u2])
    arch.init_app(app)

    @app.route('/')
    def root():
        return redirect(url_for('viauth.profile'))

    @app.route('/treasure')
    @login_required
    def treasure():
        return 'you got the treasure'

    @app.route('/kwarg/<test>')
    def reroute_with_kwarg(test):
        return 'test with kwarg %s' % test

    return app
