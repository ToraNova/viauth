import os
import tempfile
import pytest

from examples import persistdb

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_file = tempfile.mkstemp()
    db_uri = 'sqlite:///%s' % db_file
    app = persistdb.create_app({"TESTING": True, "DBURI": db_uri})

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
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def test_redirect(client):
    '''test redirect on protected route'''
    rv = client.get('/')
    assert rv.status_code == 302
    assert b'/login' in rv.data

    rv = login(client, "john", "test123")
    assert b'invalid credentials' in rv.data

def test_register(client):
    rv = client.post('/register', data=dict(
        username="jason", emailaddr="jason@mail", password="test"))
    assert rv.status_code == 302
    assert b'/login' in rv.data

    rv = client.post('/register', data=dict(
        username="jason", emailaddr="jason@mail", password="test"))
    assert b'username/email-address is taken' in rv.data

    rv = login(client, "jason", "test")
    assert rv.status_code == 200

    rv = client.get('/')
    assert rv.status_code == 200
    assert b'hello, jason' in rv.data

    rv = client.get('/profile')
    assert b'jason@mail' in rv.data

    rv = client.post('/update', data=dict(emailaddr='jason@newmail'))
    rv = client.get('/profile')
    assert b'jason@newmail' in rv.data

    rv = logout(client)
    rv = client.get('/')
    assert rv.status_code == 302
    assert b'/login' in rv.data
