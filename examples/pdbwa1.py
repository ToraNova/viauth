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

def test_run(client):

    rv = client.get('/elevate')
    assert b'login required.' in rv.data

    rv = client.post('/viauth/register', data=dict( username="jason", password="test"), follow_redirects = True)
    assert rv.status_code == 200
    rv = client.post('/viauth/register', data=dict( username="ting", password="test"), follow_redirects = True)
    assert rv.status_code == 200

    rv = client.post('/viauth/login', data=dict(username='jason', password='test'), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/treasure')
    assert rv.status_code == 403
    assert b'you are an admin!' not in rv.data

    rv = client.get('/viauth/users')
    assert rv.status_code == 403

    rv = client.get('/viauth/sudo/delete/2')
    assert rv.status_code == 403

    rv = client.get('/viauth/delete')
    assert rv.status_code == 404

    # self elevation test
    rv = client.post('/viauth/update', data=dict(is_admin="on"), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/treasure')
    assert rv.status_code == 403
    assert b'you are an admin!' not in rv.data

    rv = client.get('/elevate')
    assert rv.status_code == 200
    assert b'elevated.' in rv.data

    rv = client.get('/viauth/users')
    assert rv.status_code == 200
    assert b'jason. is admin? True' in rv.data
    assert b'ting. is admin? False' in rv.data

    rv = client.get('/treasure')
    assert rv.status_code == 200
    assert b'you are an admin!' in rv.data

    rv = client.get('/viauth/sudo/delete/2', follow_redirects=True)
    assert rv.status_code == 200
    assert b'ting' not in rv.data

    rv = client.post('/viauth/sudo/register', data=dict(username='ting', password='test', is_admin='on'), follow_redirects=True)
    assert rv.status_code == 200
    assert b'user account created' in rv.data
    assert b'ting. is admin? True' in rv.data

    rv = client.post('/viauth/sudo/update/2', data=dict(is_admin='off'), follow_redirects=True)
    assert rv.status_code == 200
    assert b'ting. is admin? False' in rv.data

    rv = client.get('/viauth/logout', follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/treasure')
    assert rv.status_code == 401
