# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

from hompi.api import API_PREFIX, app


def test_routes_use_hompi_prefix():
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert '{}/_get_status'.format(API_PREFIX) in rules
    assert '/_get_status' not in rules
    assert '{}/dashboard'.format(API_PREFIX) in rules
    assert '{}/_dashboard_status'.format(API_PREFIX) in rules
    assert '{}/'.format(API_PREFIX) in rules


def test_full_path_matches_like_flask_debug(monkeypatch):
    from hompi import api as api_mod

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    client = app.test_client()
    # No DB required for auth-gate on refresh when API_KEY unset
    rv = client.get('{}/_refresh'.format(API_PREFIX))
    assert rv.status_code == 200
    assert rv.data == b'Ok'


def test_stripped_mount_matches_like_lighttpd(monkeypatch):
    """Proxy mounts /hompi: SCRIPT_NAME=/hompi, PATH_INFO=/_refresh."""
    from hompi import api as api_mod

    monkeypatch.setattr(api_mod, 'API_KEY', '')
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


def test_dashboard_page_renders(monkeypatch):
    from hompi import api as api_mod
    from hompi.config import config

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    monkeypatch.setattr(config, 'DASHBOARD_API_URL', None)
    client = app.test_client()
    rv = client.get('{}/dashboard'.format(API_PREFIX))
    assert rv.status_code == 200
    assert b'text/html' in rv.content_type.encode()
    # Browser always uses same-origin proxy (never embeds external host)
    assert b'/_dashboard_status' in rv.data
    assert b'api_key' in rv.data
    assert b'Daemon status' in rv.data


def test_dashboard_embeds_md5_api_key(monkeypatch):
    """Dashboard must inject the MD5 hash (not the raw config secret)."""
    import hashlib

    from hompi import api as api_mod

    secret = 'change-me'
    digest = hashlib.md5(secret.encode('utf-8')).hexdigest().upper()
    monkeypatch.setattr(api_mod, 'API_KEY', digest)

    client = app.test_client()
    rv = client.get('{}/dashboard'.format(API_PREFIX))
    assert rv.status_code == 200
    assert digest.encode() in rv.data
    assert secret.encode() not in rv.data
    # Auth accepts the same hash the dashboard embeds
    assert api_mod._check_sharedkey is not None
    with app.test_request_context(
            '{}/_refresh?api_key={}'.format(API_PREFIX, digest)):
        assert api_mod._check_sharedkey() is True


def test_dashboard_status_proxies_external_api(monkeypatch):
    """DASHBOARD_API_URL is fetched server-side with the MD5 api_key."""
    from hompi import api as api_mod
    from hompi.config import config

    remote_body = '{"id": "remote", "mode_desc": "Manual"}'
    captured = {}

    class FakeResp:
        def read(self):
            return remote_body.encode('utf-8')

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(url, timeout=None):
        captured['url'] = url
        captured['timeout'] = timeout
        return FakeResp()

    monkeypatch.setattr(config, 'DASHBOARD_API_URL',
                        'http://192.168.1.10:5000/hompi/')
    monkeypatch.setattr(api_mod, 'API_KEY', 'ABCD1234')
    monkeypatch.setattr(api_mod.urllib.request, 'urlopen', fake_urlopen)

    assert api_mod._fetch_dashboard_status() == remote_body
    assert captured['url'] == (
        'http://192.168.1.10:5000/hompi/_get_status?api_key=ABCD1234')

    client = app.test_client()
    rv = client.get('{}/_dashboard_status?api_key=ABCD1234'.format(API_PREFIX))
    assert rv.status_code == 200
    assert rv.is_json or b'remote' in rv.data
    assert b'"id": "remote"' in rv.data or b'"id":"remote"' in rv.data


def test_dashboard_page_does_not_embed_external_host(monkeypatch):
    from hompi import api as api_mod
    from hompi.config import config

    monkeypatch.setattr(
        config, 'DASHBOARD_API_URL', 'http://192.168.1.10:5000/hompi')
    monkeypatch.setattr(api_mod, 'API_KEY', '')
    client = app.test_client()
    rv = client.get('{}/dashboard'.format(API_PREFIX))
    assert rv.status_code == 200
    assert b'192.168.1.10' not in rv.data
    assert b'/_dashboard_status' in rv.data
