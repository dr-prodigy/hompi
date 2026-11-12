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
    assert '{}/timetable'.format(API_PREFIX) in rules
    assert '{}/_timetable_data'.format(API_PREFIX) in rules
    assert '{}/_timetable_data/<int:timetable_id>'.format(API_PREFIX) in rules


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
    assert b'Hompi status' in rv.data


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

    remote_body = (
        '{"id": "remote", "mode_desc": "Manual",'
        ' "temperatures": [{"id": 3, "description": "Comfort", "temp_c": 21.0}]}'
    )
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
    assert b'"id": "remote"' in rv.data or b'"id":"remote"' in rv.data
    assert b'Comfort' in rv.data


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


def test_get_image_creates_thumbnail(tmp_path, monkeypatch):
    from PIL import Image
    from hompi import api as api_mod
    from hompi.config import config

    monkeypatch.setattr(api_mod, 'API_KEY', '')

    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)
    (img_dir / "thumbs").mkdir(parents=True)

    img_path = img_dir / "sample.jpg"
    im = Image.new("RGB", (200, 200), color="red")
    im.save(str(img_path), "JPEG")

    monkeypatch.setattr(config, 'IMAGE_PATH', str(img_dir / '*.jpg'))
    monkeypatch.setattr(config, 'THUMB_SIZE', (50, 50))

    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/_get_image/sample.jpg')
    assert rv.status_code == 200

    thumb_path = img_dir / "thumbs" / "sample.jpg"
    assert thumb_path.is_file()
    with Image.open(str(thumb_path)) as thumb:
        assert thumb.size[0] <= 50 and thumb.size[1] <= 50


def test_get_image_not_found(tmp_path, monkeypatch):
    from hompi import api as api_mod
    from hompi.config import config

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)
    monkeypatch.setattr(config, 'IMAGE_PATH', str(img_dir / '*.jpg'))

    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/_get_image/nonexistent.jpg')
    assert rv.status_code == 404


def test_get_image_rejects_path_traversal(tmp_path, monkeypatch):
    from hompi import api as api_mod
    from hompi.config import config

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    img_dir = tmp_path / "images"
    img_dir.mkdir(parents=True)
    monkeypatch.setattr(config, 'IMAGE_PATH', str(img_dir / '*.jpg'))

    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/_get_image/..%2fsecret.txt')
    assert rv.status_code in (400, 403, 404)


def test_dashboard_page_has_timetable_link(monkeypatch):
    from hompi import api as api_mod
    from hompi.config import config

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    monkeypatch.setattr(config, 'DASHBOARD_API_URL', None)
    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/dashboard')
    assert rv.status_code == 200
    assert f'{API_PREFIX}/timetable'.encode() in rv.data
    assert b'Timetables' in rv.data


def test_timetable_page_renders(monkeypatch):
    from hompi import api as api_mod

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/timetable')
    assert rv.status_code == 200
    assert b'text/html' in rv.content_type.encode()
    assert b'Timetables' in rv.data
    assert f'{API_PREFIX}/dashboard'.encode() in rv.data
    assert b'Back to Dashboard' in rv.data
    assert b'&larr;' not in rv.data
    assert b'Schedule:' not in rv.data
    assert b'Days on columns, time slots on rows' not in rv.data
    assert f'{API_PREFIX}/_timetable_data'.encode() in rv.data
    assert b'timetable-select' in rv.data
    assert b'program-table' in rv.data
    assert b'active-badge' in rv.data


def test_timetable_page_back_link_preserves_api_key(monkeypatch):
    import hashlib
    from hompi import api as api_mod

    secret = 'secret-test'
    digest = hashlib.md5(secret.encode('utf-8')).hexdigest().upper()
    monkeypatch.setattr(api_mod, 'API_KEY', digest)

    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/timetable?api_key={digest}')
    assert rv.status_code == 200
    assert f'{API_PREFIX}/dashboard?api_key={digest}'.encode() in rv.data


def test_timetable_data_endpoint(monkeypatch):
    import json
    from hompi import api as api_mod

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    client = app.test_client()

    # Default (active timetable)
    rv = client.get(f'{API_PREFIX}/_timetable_data')
    assert rv.status_code == 200
    assert rv.content_type == 'application/json'
    data = json.loads(rv.data)
    assert 'timetables' in data
    assert 'active_timetable_id' in data
    assert 'selected_timetable_id' in data
    assert 'days' in data
    assert 'time_slots' in data
    assert len(data['timetables']) > 0
    assert len(data['days']) >= 7

    # Specific timetable ID
    rv2 = client.get(f'{API_PREFIX}/_timetable_data/2')
    assert rv2.status_code == 200
    data2 = json.loads(rv2.data)
    assert data2['selected_timetable_id'] == 2
    assert data2['selected_timetable']['description'] == 'Automatic'
    assert len(data2['time_slots']) > 0


def test_timetable_data_auth_gate(monkeypatch):
    import hashlib
    from hompi import api as api_mod

    digest = hashlib.md5(b'testkey').hexdigest().upper()
    monkeypatch.setattr(api_mod, 'API_KEY', digest)
    client = app.test_client()

    # Forbidden without key
    rv = client.get(f'{API_PREFIX}/_timetable_data')
    assert rv.status_code == 403

    # Forbidden with wrong key
    rv_bad = client.get(f'{API_PREFIX}/_timetable_data?api_key=WRONGKEY')
    assert rv_bad.status_code == 403

    # Success with correct key
    rv_ok = client.get(f'{API_PREFIX}/_timetable_data?api_key={digest}')
    assert rv_ok.status_code == 200


def test_timetable_data_not_found(monkeypatch):
    from hompi import api as api_mod

    monkeypatch.setattr(api_mod, 'API_KEY', '')
    client = app.test_client()
    rv = client.get(f'{API_PREFIX}/_timetable_data/999999')
    assert rv.status_code == 404


def test_build_timetable_data_helper():
    from hompi.api import _build_timetable_data

    # Test loading default/active
    data_default = _build_timetable_data()
    assert data_default is not None
    assert 'timetables' in data_default
    assert 'active_timetable_id' in data_default
    assert 'days' in data_default
    assert 'time_slots' in data_default
    assert len(data_default['days']) >= 7

    # Test loading specific timetable
    data_tt2 = _build_timetable_data(2)
    assert data_tt2 is not None
    assert data_tt2['selected_timetable_id'] == 2
    assert data_tt2['selected_timetable']['description'] == 'Automatic'
    assert len(data_tt2['time_slots']) > 0

    # Test loading non-existent timetable
    data_none = _build_timetable_data(999999)
    assert data_none is None




