from app import config


def test_config_loading():
    _parsed_config = config.parse_config()

    assert 'auth' in _parsed_config
    assert 'server' in _parsed_config
    assert 'username' in _parsed_config
    assert 'password' in _parsed_config
    assert 'database_type' in _parsed_config
    assert 'database_path' in _parsed_config
