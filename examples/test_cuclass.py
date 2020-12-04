import os
import tempfile
import pytest

from examples import cuclass

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_file = tempfile.mkstemp()
    db_uri = f'sqlite:///{db_file}'
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

def login(client, username, password):
    return client.post('/viauth/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/viauth/logout', follow_redirects=True)

def test_redirect(client):
    '''test redirect on protected route'''
    rv = client.get('/')
    assert rv.status_code == 302
    assert b'/viauth/login' in rv.data

    rv = login(client, "john", "test123")
    assert b'invalid credentials' in rv.data

#TODO: repeat registration test
@pytest.mark.parametrize(
    ("username", "emailaddr", "password", "message"),
    (
        ("", "", "", b"invalid input length"),
        ("bob", "", "", b"invalid input length"),
        ("bob", "", "test", b"successfully registered"),
    ),
)
def test_register(client, username, emailaddr, password, message):
    rv = client.post('/viauth/register', data=dict(username=username, emailaddr=emailaddr, password=password), follow_redirects=True)
    assert message in rv.data

def test_login(client):
    rv = client.post('/viauth/register', data=dict(
        username="jason", emailaddr="jason@mail", password="test"))
    assert rv.status_code == 302
    assert b'/viauth/login' in rv.data

    rv = login(client, "jason", "test")
    assert rv.status_code == 200

    rv = client.get('/')
    assert rv.status_code == 200
    assert b'hello, jason' in rv.data

    rv = client.post('/update', data=dict(favos='linux'))
    rv = client.get('/viauth/profile')
    assert b'linux' in rv.data
