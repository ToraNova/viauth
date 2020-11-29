from flask import Flask, render_template
from viauth.basic import Arch, AuthUser
from flask_login import login_required, current_user

app = Flask(__name__)
app.secret_key = 'v3rypowerfuls3cret! JUST KIDDING PLEASE CHANGE THIS!'
# define a place to find the templates

arch = Arch(
        templates = {'login':'login.html'},
        reroutes= {'login':'protected','logout':'viauth.login'}
        )
u1 = AuthUser('john','test123')
u2 = AuthUser('james','hello')
ulist = [u1, u2]
#arch.update_users(ulist)
arch.update_users(u1, u2)

arch.init_app(app)

@app.route('/')
@login_required
def protected():
    return render_template('home.html')

# users registered AFTER calling init_app are not accounted for.
# please see other architectures for this (example, sqlalchemy variants)
u3 = AuthUser('blake','matter')
arch.update_users(u3)
