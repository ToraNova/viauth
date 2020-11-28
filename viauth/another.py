from viauth import source

@source.bp.route('/login', methods=['GET','POST'])
def login():
    return 'another login'

arch = source.bp
