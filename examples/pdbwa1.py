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

def test_run(client):

    rv = client.get('/set_admin')
    assert b'login required.' in rv.data

    rv = client.post('/viauth/register', data=dict( username="jason", emailaddr="jason@mail", password="test"))
    rv = client.post('/viauth/register', data=dict( username="ting", emailaddr="ting@mail", password="test"))
    assert rv.status_code == 302
    assert b'/login' in rv.data

    rv = login(client, 'jason', 'test')
    assert rv.status_code == 200

    rv = client.get('/viauth/users')
    assert rv.status_code == 403

    rv = client.get('/admin_secret')
    assert rv.status_code == 403

    rv = client.get('/viauth/delete/2')
    assert rv.status_code == 403

    # self elevation test
    rv = client.post('/viauth/update', data=dict( emailaddr="jason@mail", is_admin = "on"), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/admin_secret')
    assert rv.status_code == 403

    rv = client.get('/set_admin')
    assert rv.status_code == 200
    assert b'ok' in rv.data

    rv = client.get('/viauth/users')
    assert rv.status_code == 200
    assert b'jason' in rv.data and b'is admin? True' in rv.data
    assert b'ting' in rv.data

    rv = client.get('/admin_secret')
    assert rv.status_code == 200
    assert b'you are an admin!' in rv.data

    rv = client.get('/viauth/delete/2', follow_redirects=True)
    assert rv.status_code == 200
    assert b'ting@mail' not in rv.data

    logout(client)

    rv = client.get('/admin_secret')
    assert rv.status_code == 401
