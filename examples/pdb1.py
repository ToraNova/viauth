import os
import tempfile
import pytest

from examples import persistdb

@pytest.fixture
def app():
    '''Create and configure a new app instance for each test.'''
    db_fd, db_file = tempfile.mkstemp()
    db_uri = 'sqlite:///%s' % db_file
    app = persistdb.create_app({'TESTING': True, 'DBURI': db_uri})

    # create the database and load test data
    with app.app_context():
        pass
    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_file)

@pytest.fixture
def client(app):
    '''A test client for the app.'''
    return app.test_client()

@pytest.mark.parametrize(
    ('username', 'password', 'message'),
    (
        ('ting', '', b'invalid input length'),
        ('', 'hello', b'invalid input length'),
        ('', '', b'invalid input length'),
        ('ting', 'hello', b'successfully registered'),
    ),
)
def test_params(client, username, password, message):
    rv = client.post('/viauth/register', data=dict(username=username, password=password), follow_redirects = True)
    assert rv.status_code == 200
    assert message in rv.data

def test_run(client):

    rv = client.get('/')
    assert rv.status_code == 302 #redirected

    rv = client.get('/users')
    assert rv.status_code == 401
    assert b'login required.' in rv.data

    rv = client.get('/viauth/login')
    assert rv.status_code == 200

    rv = client.get('/viauth/profile')
    assert rv.status_code == 401

    rv = client.get('/viauth/logout')
    assert rv.status_code == 302

    rv = client.post('/viauth/login', data=dict(username='jason', password='test'), follow_redirects = True)
    assert rv.status_code == 401

    rv = client.get('/viauth/register')
    assert rv.status_code == 200

    rv = client.post('/viauth/register', data=dict(username='ting', password='hello'), follow_redirects = True)
    assert rv.status_code == 200
    assert b'successfully registered' in rv.data

    rv = client.post('/viauth/register', data=dict(username='ting', password='hello'), follow_redirects = True)
    assert rv.status_code == 409
    assert b'registration unavailable' in rv.data

    rv = client.post('/viauth/register', data=dict(username='jason', password='test123'), follow_redirects = True)
    assert rv.status_code == 200
    assert b'successfully registered' in rv.data

    rv = client.post('/viauth/login', data=dict(username='jason', password='test'), follow_redirects = True)
    assert rv.status_code == 401

    rv = client.post('/viauth/login', data=dict(username='jaso', password='test123'), follow_redirects = True)
    assert rv.status_code == 401

    rv = client.post('/viauth/login', data=dict(username='jason', password='test123'), follow_redirects = True)
    assert rv.status_code == 200
    assert b'hello, jason' in rv.data
    assert b'login success.' in rv.data

    rv = client.get('/users')
    assert rv.status_code == 200
    assert b'jason' in rv.data and b'ting' in rv.data

    rv = client.get('/viauth/profile')
    lut = rv.data[rv.data.find(b'updated on: ')+12:]
    lut = lut[: lut.find(b'</p>')]

    rv = client.get('/viauth/update')
    assert rv.status_code == 200

    rv = client.post('/viauth/update', follow_redirects = True)
    assert rv.status_code == 200
    nut = rv.data[rv.data.find(b'updated on: ')+12:]
    nut = nut[: nut.find(b'</p>')]
    assert lut != nut

    rv = client.get('/viauth/logout', follow_redirects=True)
    assert rv.status_code == 200
    assert b'off you GO!' in rv.data

    rv = client.get('/viauth/update')
    assert rv.status_code == 401

    rv = client.post('/viauth/update')
    assert rv.status_code == 401

    rv = client.get('/viauth/profile')
    assert rv.status_code == 401
