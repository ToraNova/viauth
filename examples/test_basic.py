import pytest

from examples.basic import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({"TESTING": True})

    # create the database and load test data
    with app.app_context():
        pass

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_redirect(client):
    '''test redirect on protected route'''
    rv = client.get('/')
    assert b'You should be redirected automatically to target URL: <a href="/viauth/login">' in rv.data

def login(client, username, password):
    return client.post('/viauth/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/viauth/logout', follow_redirects=True)

def test_login_logout(client):
    '''test login and logout'''

    rv = login(client, "john", "test123")
    assert b'hello john, you are authenticated' in rv.data

    rv = logout(client)
    assert b'<input name="username" required>' in rv.data
    assert b'<input name="password" type="password" required>' in rv.data

    rv = login(client, "john", "test1234")
    assert b'invalid credentials' in rv.data

    rv = login(client, "alice", "hello")
    assert b'invalid credentials' in rv.data

    rv = login(client, "alice", None)
    assert rv.status_code == 400
