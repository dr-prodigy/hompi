# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

from hompi.api import API_PREFIX, app


def test_routes_use_hompi_prefix():
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert '{}/_get_status'.format(API_PREFIX) in rules
    assert '/_get_status' not in rules


def test_full_path_matches_like_flask_debug():
    client = app.test_client()
    # No DB required for auth-gate on refresh when API_KEY unset
    rv = client.get('{}/_refresh'.format(API_PREFIX))
    assert rv.status_code == 200
    assert rv.data == b'Ok'


def test_stripped_mount_matches_like_lighttpd():
    """Proxy mounts /hompi: SCRIPT_NAME=/hompi, PATH_INFO=/_refresh."""
    client = app.test_client()
    rv = client.get(
        '/_refresh',
        environ_overrides={
            'SCRIPT_NAME': API_PREFIX,
            'PATH_INFO': '/_refresh',
        },
    )
    assert rv.status_code == 200
    assert rv.data == b'Ok'
