'''
basic example using the default AuthUser from the persistdb type
running this example:
(in virtualenv)
EXPORT FLASK_APP = minimal
flask run
'''
from flask import Flask, render_template, redirect, url_for, request
from viauth.persistdb import Arch, AuthUser
from flask_login import login_required, current_user

app = Flask(__name__)
app.secret_key = 'v3rypowerfuls3cret! JUST KIDDING PLEASE CHANGE THIS!'
# define a place to find the templates

dburi = 'sqlite:///tmp.db'

try:
    AuthUser.create_table(dburi)
except Exception as e:
    print(e)

arch = Arch(
        templates = {'login':'login.html','register':'signup.html','profile':'profile.html'},
        reroutes= {'login':'protected','logout':'viauth.login','register':'viauth.login'}
        )

arch.configure_db(dburi)

arch.init_app(app)

@app.route('/')
@login_required
def protected():
    return render_template('home.html')

@app.route('/users')
@login_required
def list():
    ulist = AuthUser.query.all()
    return render_template('ulist.html', data=ulist)

@app.route('/update', methods=['GET','POST'])
@login_required
def update():
    if request.method == 'POST':
        emailaddr = request.form.get('emailaddr')
        tar = AuthUser.query.filter(AuthUser.id == current_user.id).first()
        tar.emailaddr = emailaddr
        try:
            arch.session.add(tar)
            arch.session.commit()
            return redirect(url_for('protected'))
        except Exception as e:
            arch.session.rollback()
            return e
    return render_template('edit.html')

@app.route('/delete')
@login_required
def delete():
    try:
        tar = AuthUser.query.filter(AuthUser.id == current_user.id).first()
        arch.session.delete(tar)
        arch.session.commit()
        return redirect(url_for('viauth.logout'))
    except Exception as e:
        arch.session.rollback()
        return e
