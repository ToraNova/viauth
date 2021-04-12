'''
an example on how to extend on the AuthUser class from the persistdb type
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = cuclass
flask run
'''
from flask import Flask, render_template, redirect, url_for, request, flash
from viauth.persistdb import Arch, AuthUserMixin
from flask_login import login_required, current_user
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base() # declare own Base

# TODO create your own user class and inherit from AuthUser
class ExtendedAuthUser(AuthUserMixin, Base):
    __tablename__ = "authuser"
    emailaddr = Column(String(254),unique=True,nullable=False)

    # this is called when a new class ExtendedAuthUser is created
    # may raise an exception to stop the process
    def __init__(self, reqform):
        super().__init__(reqform) # must call super's constructor
        if 'emailaddr' not in reqform or len(reqform['emailaddr']) < 1:
            raise ValueError('email cannot be empty')
        self.emailaddr = reqform.get("emailaddr")


    # login callback. this is called before a user is actually logged in
    def login(self):
        pass

    # logout callback. this is called before a user is actually logged out
    def logout(self):
        pass

    # this is called when the user updates their own profiles.
    # may raise an exception to stop the process
    def update(self, reqform):
        super().update(reqform) # call super's method ensure super's update is processed
        if 'emailaddr' not in reqform or len(reqform['emailaddr']) < 1:
            raise ValueError('email cannot be empty')
        self.emailaddr = reqform.get("emailaddr")

    # this is called before user self deletion.
    # may raise an exception to stop deletion
    def delete(self):
        raise Exception("user can't delete themselves") # this is arbitrary.

    # this is called if an admin creates the user's profiles.
    def admin_create(self, reqform):
        super().admin_create(reqform)
        # do something

    # this is called if an admin updates the user's profiles.
    # may also raise exception to stop the process
    # requires viauth.persistdb.withadmin or viauth.persistb.withroles to have effect
    def admin_update(self, reqform):
        super().admin_update(reqform)
        # do something

    # this is called before admin deletes a user
    # may raise an exception to stop deletion
    # requires viauth.persistdb.withadmin or viauth.persistb.withroles to have effect
    def admin_delete(self):
        pass

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
        # custom class is decoupled from viauth's sqlorm.Base, use your own declarative Base here
        Base,
        templates = {
            'register':'signup.html',
            'update':'edit.html',
            },
        reroutes= {
            'login':'home',
            },
        # custom user route execution callback
        # flash('successfully registered','ok') when registration is OK instead of the default
        # 'registered user account'
        rex_callback = {
            'register': {'ok': lambda *args, **kwargs: flash('successfully registered', 'ok')},
            },
        authuser_class = ExtendedAuthUser,
        # if we want to set the arch to login using emailaddress
        login_key = {
            'match': {'attr': 'emailaddr', 'form':'emailaddr'}
            }
    )

    arch.init_app(app)

    @app.route('/')
    def root():
        return redirect(url_for('viauth.login'))

    @app.route('/home')
    @login_required
    def home():
        return render_template('home.html')

    # obtain session using arch.session

    return app
