from viauth import source

@source.bp.route('/login', methods=['GET','POST'])
def login():
    return 'basic login'

arch = source.bp
