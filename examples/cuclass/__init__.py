'''
an example on how to extend on the AuthUser class from the persistdb type
running this example:
(in virtualenv @ examples/)
EXPORT FLASK_APP = cuclass
flask run
'''
from flask import Flask, render_template, redirect, url_for, request
from viauth.persistdb import Arch, AuthUser
from flask_login import login_required, current_user
from sqlalchemy import Column, Integer, String, Boolean, DateTime

# TODO create your own user class and inherit from AuthUser
class ExtendedAuthUser(AuthUser):
    favorite_os = Column(String(), unique=False, nullable=True)

    def __init__(self, reqform):
        super().__init__(reqform)
        self.favorite_os = reqform.get("favos")

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

    arch = Arch(
        templates = {'login':'login.html','register':'signup.html','profile':'profile.html'},
        reroutes= {'login':'protected','logout':'viauth.login','register':'viauth.login'}
    )

    arch.set_authuserclass(ExtendedAuthUser)
    arch.configure_db(app.config['DBURI'])
    arch.init_app(app)

    @app.route('/')
    @login_required
    def protected():
        return render_template('favos.html')

    @app.route('/update', methods=['GET','POST'])
    @login_required
    def update():
        if request.method == 'POST':
            favos = request.form.get('favos')
            tar = ExtendedAuthUser.query.filter(ExtendedAuthUser.id == current_user.id).first()
            tar.favorite_os = favos
            try:
                arch.session.add(tar)
                arch.session.commit()
                return redirect(url_for('protected'))
            except Exception as e:
                arch.session.rollback()
                return e
        return render_template('favos_edit.html')

    return app
