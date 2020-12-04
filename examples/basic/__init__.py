'''
an absolute basic auth architecture
to run:
(in virtualenv @ examples/)
export FLASK_APP=basic
flask run
'''
from flask import Flask, render_template
from viauth.basic import Arch, AuthUser
from flask_login import login_required

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'v3rypowerfuls3cret, or not. CHANGE THIS!@'
    app.testing = False
    if test_config:
        app.config.from_mapping(test_config)

    arch = Arch(
        templates = {'login':'login.html'},
        reroutes= {'login':'protected','logout':'viauth.login'}
    )

    u1 = AuthUser('john','test123')
    u2 = AuthUser('james','hello')
    arch.update_users([u1, u2])
    arch.init_app(app)

    @app.route('/')
    @login_required
    def protected():
        return render_template('home.html')

    return app
