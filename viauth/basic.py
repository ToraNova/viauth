from flask import render_template, request, redirect, abort
from viauth import source

class ArchConf:
    def __init__(self, templates, reroutes):
        self.__templ = templates
        self.__route = reroutes
        assert(self.__templ.get('login'))

    def generate(self):
        @source.bp.route('/login', methods=['GET','POST'])
        def login():
            tpl = render_template(self.__templ['login'])
            if(request.method == 'POST'):
                username = request.form.get('username')
                password = request.form.get('password')
                if(not username or not password):
                    abort(400)
                #TODO: port rapid2flask's user method here
            return tpl
        return source.bp
