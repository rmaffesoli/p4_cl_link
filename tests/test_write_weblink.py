import os
import sys
from unittest.mock import Mock, patch

# Ensure the src/directory is importable (tests live next to src)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Set env vars before importing the module under test (module reads them at import-time)
os.environ.setdefault('DAM_SERVER_ADDRESS', 'http://dam.test')
os.environ.setdefault('DAM_ACCOUNT_KEY', 'test-account-key')

import pytest

from dam_api.write_weblink import (
    gather_webhook_configs,
    gather_weblink_type_id,
    attach_weblink,
)
import dam_api.write_weblink as ww
import requests


def make_mock_response(json_data=None, raise_on_json=False, status=200):
    resp = Mock()
    resp.status_code = status
    resp.raise_for_status = Mock()
    if raise_on_json:
        resp.json.side_effect = ValueError('no json')
    else:
        resp.json.return_value = json_data
    return resp


def test_gather_webhook_configs_success():
    sample = {
        'results': [
            {
                'name': 'planhook',
                'uuid': 'uuid-plan',
                'service': 'atlassian-plan',
                'config': {'url': 'https://plan.example.com'},
            }
        ]
    }

    with patch('dam_api.write_weblink.requests.get') as mock_get:
        mock_get.return_value = make_mock_response(json_data=sample)
        cfg = gather_webhook_configs()
        assert 'planhook' in cfg
        assert cfg['planhook']['uuid'] == 'uuid-plan'
        assert cfg['planhook']['url'] == 'https://plan.example.com'


def test_gather_webhook_configs_non_json():
    with patch('dam_api.write_weblink.requests.get') as mock_get:
        mock_get.return_value = make_mock_response(raise_on_json=True)
        cfg = gather_webhook_configs()
        assert cfg == {}


def test_gather_weblink_type_id_plan_and_jira():
    webhook_config = {
        'planhook': {'uuid': 'u1', 'service': 'some plan', 'url': 'https://plan.example.com'},
        'jirahook': {'uuid': 'u2', 'service': 'jira', 'url': 'https://jira.example.com'},
    }

    plan_link = 'https://plan.example.com/items/12345'
    wtype, uuid, wid = gather_weblink_type_id(plan_link, webhook_config)
    assert wtype == 'plan'
    assert uuid == 'u1'
    assert wid == '12345'

    jira_link = 'https://jira.example.com/browse/ISSUE-999/'
    wtype, uuid, wid = gather_weblink_type_id(jira_link, webhook_config)
    assert wtype == 'jira'
    assert uuid == 'u2'
    assert wid == 'ISSUE-999'


def test_attach_weblink_posts_plan_payload():
    # prepare webhook configs returned by GET
    webhook_json = {
        'results': [
            {
                'name': 'planhook',
                'uuid': 'uuid-plan',
                'service': 'some plan',
                'config': {'url': 'https://plan.example.com'},
            }
        ]
    }

    post_resp = make_mock_response(json_data={'ok': True})

    with patch('dam_api.write_weblink.requests.get') as mock_get, patch('dam_api.write_weblink.requests.post') as mock_post:
        mock_get.return_value = make_mock_response(json_data=webhook_json)
        mock_post.return_value = post_resp

        depot_path = '//depot/project/file.txt@123'
        weblink = 'https://plan.example.com/items/777'

        attach_weblink(depot_path, weblink)

        # verify POST called correctly
        assert mock_post.call_count == 1
        called_url = mock_post.call_args[0][0]
        called_json = mock_post.call_args[1]['json']
        assert called_url.endswith('/api/weblinks')
        assert called_json['account_key'] == 'test-account-key'
        assert called_json['depot_path'] == '//depot/project/file.txt'
        assert called_json['url'] == weblink
        assert called_json['config'] == {'item_id': '777'}
        assert called_json['webhook'] == 'uuid-plan'


def test_attach_weblink_posts_generic_payload_text_field():
    # No matching webhook -> generic weblink with text extracted
    with patch('dam_api.write_weblink.requests.get') as mock_get, patch('dam_api.write_weblink.requests.post') as mock_post:
        mock_get.return_value = make_mock_response(json_data={'results': []})
        post_resp = make_mock_response(json_data={'ok': True})
        mock_post.return_value = post_resp

        depot_path = '//depot/project/img.png'
        weblink = 'https://example.com/preview/image.png'
        attach_weblink(depot_path, weblink)

        assert mock_post.call_count == 1
        called_json = mock_post.call_args[1]['json']
        # since regex extracts domain after // until first / or :, expect 'example.com'
        assert called_json['text'] == 'example.com'


def test_gather_webhook_configs_missing_env_vars_prints_and_returns_empty(capsys):
    # Temporarily clear module-level SERVER_ADDRESS/ACCOUNT_KEY
    orig_server = ww.SERVER_ADDRESS
    orig_account = ww.ACCOUNT_KEY
    try:
        ww.SERVER_ADDRESS = None
        ww.ACCOUNT_KEY = None
        cfg = gather_webhook_configs()
        captured = capsys.readouterr()
        assert cfg == {}
        assert 'DAM_SERVER_ADDRESS and DAM_ACCOUNT_KEY must be set' in captured.out
    finally:
        ww.SERVER_ADDRESS = orig_server
        ww.ACCOUNT_KEY = orig_account


def test_attach_weblink_post_raises_prints_error():
    with patch('dam_api.write_weblink.requests.get') as mock_get, patch('dam_api.write_weblink.requests.post') as mock_post:
        mock_get.return_value = make_mock_response(json_data={'results': []})
        mock_post.side_effect = requests.RequestException('boom')

        depot_path = '//depot/project/file.txt'
        weblink = 'https://example.com/foo'

        # capture print output
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            attach_weblink(depot_path, weblink)
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert 'error attaching weblink' in out


def test_attach_weblink_post_raise_for_status_prints_error():
    with patch('dam_api.write_weblink.requests.get') as mock_get, patch('dam_api.write_weblink.requests.post') as mock_post:
        mock_get.return_value = make_mock_response(json_data={'results': []})
        resp = make_mock_response(json_data={'ok': True})
        resp.raise_for_status.side_effect = requests.HTTPError('bad')
        mock_post.return_value = resp

        depot_path = '//depot/project/file.txt'
        weblink = 'https://example.com/foo'

        from io import StringIO
        import sys
        old_stdout = sys.stdout
        try:
            sys.stdout = StringIO()
            attach_weblink(depot_path, weblink)
            out = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert 'error attaching weblink' in out
