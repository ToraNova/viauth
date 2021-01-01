'''
basic example using the default AuthUser from the persistdb type
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = persistdb
flask run
'''
from flask import Flask, render_template, redirect, url_for, request
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

    # define a place to find the templates
    # set url_prefix = '/' to have no url_prefix, leaving it empty will prefix with viauth
    arch = Arch(
        app.config['DBURI'],
        templates = {
                'login':'login.html',
                'register':'signup.html',
                'profile':'profile.html',
                'update': 'edit.html'
            },
        reroutes= {'login':'protected','logout':'viauth.login','register':'viauth.login','unauth':'nope'},
        url_prefix = '/'
    )

    arch.init_app(app)

    @app.route('/')
    @login_required
    def protected():
        return render_template('home.html')

    @app.route('/nope')
    def nope():
        return render_template('nope.html')

    @app.route('/users')
    @login_required
    def list():
        ulist = AuthUser.query.all()
        return render_template('ulist.html', data=ulist)

    # test case on how to commit/update
    @app.route('/reset_emails')
    def unset():
        ulist = AuthUser.query.all()
        try:
            for u in ulist:
                u.emailaddr = None
                arch.session.add(u)
            arch.session.commit()
            return redirect(url_for('list'))
        except Exception as e:
            arch.session.rollback()
            return e

    return app
