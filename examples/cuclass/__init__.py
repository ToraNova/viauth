'''
an example on how to extend on the AuthUser class from the persistdb type
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = cuclass
flask run
'''
from flask import Flask, render_template, redirect, url_for, request
from viauth import ArbException
from viauth.persistdb import Arch, AuthUser
from flask_login import login_required, current_user
from sqlalchemy import Column, Integer, String, Boolean, DateTime

# TODO create your own user class and inherit from AuthUser
class ExtendedAuthUser(AuthUser):
    favorite_os = Column(String(), unique=False, nullable=True)

    # this is called when a new class ExtendedAuthUser is created
    # may raise an exception to stop the process
    def __init__(self, reqform):
        super().__init__(reqform)
        self.favorite_os = reqform.get("favos")

    # this is called when the user updates their own profiles. may raise an exception to stop the process
    def self_update(self, reqform):
        #super().update(reqform) # may call this optionally if wanna use AuthUser's original update method
        self.favorite_os = reqform.get("favos")

    # this is called if an admin updates the user's profiles. may also raise exception to stop the process
    def admin_update(self, reqform):
        pass

    # this is called before deletion. MAY raise an exception to stop deletion
    def delete(self):
        raise ArbException("user can't delete themselves") # this is arbitrary.

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'v3rypowerfuls3cret, or not. CHANGE THIS!@'
    app.config['DBURI'] = 'sqlite:///cutmp.db'
    app.testing = False
    if test_config:
        app.config.from_mapping(test_config)

    try:
        ExtendedAuthUser.create_table(app.config['DBURI'])
    except Exception as e:
        #print(e)
        pass

    # set url_prefix = '/' to have no url_prefix, leaving it empty (None) will prefix with viauth
    arch = Arch(
        app.config['DBURI'],
        templates = {
            'login':'login.html',
            'register':'signup.html',
            'profile':'profile.html',
            'update': 'favos_edit.html'
            },
        reroutes = {
            'login':'protected',
            'logout':'viauth.login',
            'register':'viauth.login'
            },
        url_prefix = None,
        authuser_class = ExtendedAuthUser
    )

    arch.init_app(app)

    @app.route('/')
    @login_required
    def protected():
        return render_template('favos.html')

    return app
