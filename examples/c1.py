from examples import basic, persistdb, cuclass, withadmin

def test_config():
    """Test create_app without passing test config."""
    assert not basic.create_app().testing
    assert not persistdb.create_app().testing
    assert not cuclass.create_app().testing
    assert not withadmin.create_app().testing
    assert basic.create_app({"TESTING": True}).testing
    assert persistdb.create_app({"TESTING": True}).testing
    assert cuclass.create_app({"TESTING": True}).testing
    assert withadmin.create_app({"TESTING": True}).testing
