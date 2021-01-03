import os
import tempfile
import pytest

from examples import withadmin

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_file = tempfile.mkstemp()
    db_uri = 'sqlite:///%s' % db_file
    app = withadmin.create_app({"TESTING": True, "DBURI": db_uri})

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

def test_withadmin(client):

    rv = client.get('/set_admin')
    assert rv.status_code == 302

    rv = client.post('/viauth/register', data=dict( username="wajason", emailaddr="wajason@mail", password="test"))
    rv = client.post('/viauth/register', data=dict( username="wating", emailaddr="wating@mail", password="test"))
    assert rv.status_code == 302
    assert b'/login' in rv.data

    rv = login(client, 'wajason', 'test')
    assert rv.status_code == 200

    rv = client.get('/viauth/users')
    assert rv.status_code == 403

    rv = client.get('/admin_secret')
    assert rv.status_code == 403

    rv = client.get('/set_admin')
    assert rv.status_code == 200
    assert b'ok' in rv.data

    rv = client.get('/viauth/users')
    assert rv.status_code == 200

    rv = client.get('/admin_secret')
    assert rv.status_code == 200
    assert b'you are an admin!' in rv.data

    logout(client)

    rv = client.get('/admin_secret')
    assert rv.status_code == 401
