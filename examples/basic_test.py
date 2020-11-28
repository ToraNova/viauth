from flask import Flask
from viauth.basic import ArchConf

app = Flask(__name__)
# define a place to find the templates
app.register_blueprint(ArchConf({"login":"login.html"},None).generate())

@app.route('/')
def hello_world():
    return 'Hello, World!'
