import os
import tempfile
import pytest

from examples import cuclass

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_file = tempfile.mkstemp()
    db_uri = 'sqlite:///%s' % db_file
    app = cuclass.create_app({"TESTING": True, "DBURI": db_uri})

    # create the database and load test data
    with app.app_context():
        pass
    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_file)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

#TODO: repeat registration test
@pytest.mark.parametrize(
    ("username", "emailaddr", "password", "message"),
    (
        ("", "", "", b"invalid input length"),
        ("bob", "", "", b"invalid input length"),
        ("bob", "", "test", b"email cannot be empty"),
        ("bob", "bobmail", "test", b"successfully registered"),
    ),
)
def test_params(client, username, emailaddr, password, message):
    rv = client.post('/viauth/register', data=dict(username=username, emailaddr=emailaddr, password=password), follow_redirects=True)
    assert message in rv.data

def test_run(client):
    '''main test'''

    rv = client.get('/')
    assert rv.status_code == 302 #redirected

    rv = client.post('/viauth/login', data=dict(username='jason', password='test'), follow_redirects = True)
    assert rv.status_code == 400

    rv = client.post('/viauth/login', data=dict(emailaddr='jason@mail.test', password='test'), follow_redirects = True)
    assert rv.status_code == 401

    rv = client.post('/viauth/register', data=dict(username='ting', password='hello', emailaddr='ting@mail.test'), follow_redirects = True)
    assert rv.status_code == 200
    assert b'successfully registered' in rv.data

    rv = client.post('/viauth/register', data=dict(username='ting', password='hello', emailaddr='jason@mail.test'), follow_redirects = True)
    assert rv.status_code == 409
    assert b'registration unavailable' in rv.data

    rv = client.post('/viauth/register', data=dict(username='jason', password='test123', emailaddr='ting@mail.test'), follow_redirects = True)
    assert rv.status_code == 409
    assert b'registration unavailable' in rv.data

    rv = client.post('/viauth/register', data=dict(username='jason', password='test123', emailaddr='jason@mail.test'), follow_redirects = True)
    assert rv.status_code == 200
    assert b'successfully registered' in rv.data

    rv = client.post('/viauth/login', data=dict(emailaddr='jason@mail.test', password='test123'), follow_redirects = True)
    assert rv.status_code == 200
    assert b'hello, jason' in rv.data
    assert b'login success.' in rv.data

    rv = client.get('/viauth/profile')
    assert b'jason@mail.test' in rv.data
    lut = rv.data[rv.data.find(b'updated on: ')+12:]
    lut = lut[: lut.find(b'</p>')]

    rv = client.get('/viauth/update')
    assert rv.status_code == 200

    rv = client.post('/viauth/update', data={}, follow_redirects = True)
    assert b'email cannot be empty' in rv.data

    rv = client.post('/viauth/update', data=dict(emailaddr='new2mail'), follow_redirects = True)
    assert rv.status_code == 200
    nut = rv.data[rv.data.find(b'updated on: ')+12:]
    nut = nut[: nut.find(b'</p>')]
    assert lut != nut
    assert b'new2mail' in rv.data

    rv = client.get('/viauth/logout', follow_redirects=True)
    assert rv.status_code == 200
    assert b'logout success.' in rv.data

    rv = client.get('/viauth/logout')
    assert rv.status_code == 302
