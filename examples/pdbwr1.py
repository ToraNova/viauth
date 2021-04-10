import os
import tempfile
import pytest

from examples import withroles

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_file = tempfile.mkstemp()
    db_uri = 'sqlite:///%s' % db_file
    app = withroles.create_app({"TESTING": True, "DBURI": db_uri})

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

    rv = client.get('/content')
    assert rv.status_code == 401

    rv = client.get('/nopay')
    assert rv.status_code == 401

    rv = client.post('/viauth/register', data=dict( username="jason", password="test"), follow_redirects = True)
    assert rv.status_code == 200
    rv = client.post('/viauth/register', data=dict( username="ting", password="test"), follow_redirects = True)
    assert rv.status_code == 200

    rv = client.post('/viauth/login', data=dict(username='jason', password='test'), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/viauth/users')
    assert rv.status_code == 403

    rv = client.get('/viauth/sudo/delete/2')
    assert rv.status_code == 403

    rv = client.get('/content')
    assert rv.status_code == 403

    # self elevation test
    rv = client.get('/viauth/update')
    assert b'<option' in rv.data and b'admin</' in rv.data
    assert b'<option' in rv.data and b'peasant</' in rv.data

    rv = client.post('/viauth/update', data=dict(rid=0), follow_redirects=True)
    assert rv.status_code == 200

    rv = client.get('/content')
    assert rv.status_code == 403

    rv = client.get('/elevate')
    assert rv.status_code == 403

    rv = client.get('/pay')
    assert rv.status_code == 200
    assert b'premium account activated.' in rv.data

    rv = client.get('/content')
    assert rv.status_code == 200
    assert b'premium content.' in rv.data

    rv = client.get('/nopay')
    assert rv.status_code == 200
    assert b'premium account deactivated.' in rv.data

    rv = client.get('/content')
    assert rv.status_code == 403

    rv = client.get('/pay')
    assert rv.status_code == 200
    assert b'premium account activated.' in rv.data

    rv = client.get('/elevate')
    assert rv.status_code == 200
    assert b'elevated.' in rv.data

    rv = client.get('/viauth/users')
    assert rv.status_code == 200
    assert b'jason, admin' in rv.data
    assert b'ting, ' in rv.data

    rv = client.get('/content')
    assert rv.status_code == 403

    rv = client.get('/viauth/roles')
    assert rv.status_code == 200
    assert b'peasant' in rv.data
    assert b'testdel' in rv.data

    rv = client.get('/viauth/sudo/delete/2', follow_redirects=True)
    assert rv.status_code == 200
    assert b'ting' not in rv.data

    rv = client.get('/viauth/role/register')
    assert rv.status_code == 200
    assert b'form' in rv.data

    rv = client.get('/viauth/role/update/2')
    assert rv.status_code == 200
    assert b'peasant' in rv.data

    rv = client.get('/viauth/role/delete/4', follow_redirects=True)
    assert rv.status_code == 200
    assert b'testdel' not in rv.data

    rv = client.post('/viauth/role/update/3', data=dict(name='premium', level=4), follow_redirects=True)
    assert rv.status_code == 200
    assert b'peasant, 4' in rv.data
    assert b'premium, 4' in rv.data


    rv = client.post('/viauth/sudo/register', data=dict(username='ting2', password='test', rid=2), follow_redirects=True)
    assert rv.status_code == 200
    assert b'ting2, peasant' in rv.data

    rv = client.get('/viauth/sudo/update/2')
    assert b'<option' in rv.data and b'premium</' in rv.data

    rv = client.get('/viauth/logout', follow_redirects = True)
    assert rv.status_code == 200

    rv = client.post('/viauth/login', data=dict(username='ting2', password='test'), follow_redirects=True)
    assert rv.status_code == 200
    assert b'peasant' in rv.data

    rv = client.get('/elevate')
    assert rv.status_code == 403

    rv = client.get('/pay')
    assert rv.status_code == 200
    assert b'premium account activated.'

    rv = client.get('/elevate')
    assert rv.status_code == 403
