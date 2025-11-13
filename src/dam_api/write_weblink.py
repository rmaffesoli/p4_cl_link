#!/usr/bin/env python
from __future__ import print_function
import os
import re
from typing import Dict, Optional, Tuple
import requests
from urllib.parse import urlparse


SERVER_ADDRESS = os.environ.get('DAM_SERVER_ADDRESS')
ACCOUNT_KEY = os.environ.get('DAM_ACCOUNT_KEY')


def _last_path_segment(url: str) -> Optional[str]:
    """Return the last non-empty path segment from a URL, or None."""
    try:
        parsed = urlparse(url)
        segments = [seg for seg in parsed.path.split('/') if seg]
        if not segments:
            return None
        return segments[-1]
    except Exception:
        return None


def attach_weblink(selected_asset: str, weblink: str) -> None:
    """Attach a weblink to a depot asset via the DAM API.

    This is a best-effort helper — it will print error messages on failure
    rather than raising.
    """
    if not weblink:
        return

    if not SERVER_ADDRESS or not ACCOUNT_KEY:
        print('DAM_SERVER_ADDRESS and DAM_ACCOUNT_KEY must be set')
        return

    if not selected_asset:
        print('selected_asset is required')
        return

    if '@' in selected_asset:
        selected_asset = selected_asset.split('@')[0]

    add_asset_weblink_url = f"{SERVER_ADDRESS}/api/weblinks"
    add_asset_weblink_body = {
        'account_key': ACCOUNT_KEY,
        'depot_path': selected_asset,
        'url': weblink,
    }

    webhook_config = gather_webhook_configs()
    weblink_type, webhook_uuid, webhook_id = gather_weblink_type_id(weblink, webhook_config)
    if weblink_type == 'jira':
        add_asset_weblink_body['config'] = {'issue_id': webhook_id}
        add_asset_weblink_body['webhook'] = webhook_uuid
    elif weblink_type == 'plan':
        add_asset_weblink_body['config'] = {'item_id': webhook_id}
        add_asset_weblink_body['webhook'] = webhook_uuid
    else:
        title_pattern = r"(?<=//)[^/:]*"
        weblink_matches = re.search(title_pattern, weblink)
        title = None
        if weblink_matches:
            title = weblink_matches.group()
        add_asset_weblink_body['text'] = title

    try:
        resp = requests.post(add_asset_weblink_url, json=add_asset_weblink_body, timeout=10)
        resp.raise_for_status()
        try:
            print(resp.json())
        except ValueError:
            print('weblink attached (no json returned)')
    except requests.RequestException as exc:
        print(f'error attaching weblink: {exc}')


def gather_webhook_configs() -> Dict[str, Dict[str, str]]:
    """Fetch webhook configs from the DAM API and return a mapping by name.

    Returns an empty dict on error.
    """
    webhook_dict: Dict[str, Dict[str, str]] = {}

    if not SERVER_ADDRESS or not ACCOUNT_KEY:
        print('DAM_SERVER_ADDRESS and DAM_ACCOUNT_KEY must be set')
        return webhook_dict

    webhook_config_url = f"{SERVER_ADDRESS}/api/webhooks"
    webhook_config_body = {'account_key': ACCOUNT_KEY}

    try:
        resp = requests.get(webhook_config_url, json=webhook_config_body, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f'error fetching webhook configs: {exc}')
        return webhook_dict

    try:
        response_json = resp.json()
    except ValueError:
        print('no webhook json')
        return webhook_dict

    results = response_json.get('results')
    if not results:
        return webhook_dict

    for webhook in results:
        # defensive lookups
        name = webhook.get('name')
        uuid = webhook.get('uuid')
        service = webhook.get('service')
        url = None
        cfg = webhook.get('config') or {}
        url = cfg.get('url')
        if name and uuid and service and url:
            webhook_dict[name] = {'uuid': uuid, 'service': service, 'url': url}

    return webhook_dict


def gather_weblink_type_id(weblink: str, webhook_config: Dict[str, Dict[str, str]]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Determine if a weblink corresponds to a known webhook (jira/plan) and
    return (type, webhook_uuid, id).
    """
    webhook_uuid = None
    weblink_type = None
    webhook_id = None

    plan_webhook_uuid = None
    plan_url = None

    jira_webhook_uuid = None
    jira_url = None

    for _, webhook_data in webhook_config.items():
        service = webhook_data.get('service', '')
        if 'plan' in service:
            plan_webhook_uuid = webhook_data.get('uuid')
            plan_url = webhook_data.get('url')
        elif 'jira' in service:
            jira_webhook_uuid = webhook_data.get('uuid')
            jira_url = webhook_data.get('url')

    # extract id as last path segment (if present)
    last_seg = _last_path_segment(weblink)

    if plan_url and plan_url in weblink:
        weblink_type = 'plan'
        webhook_uuid = plan_webhook_uuid
        webhook_id = last_seg
    elif jira_url and jira_url in weblink:
        weblink_type = 'jira'
        webhook_uuid = jira_webhook_uuid
        webhook_id = last_seg

    return weblink_type, webhook_uuid, webhook_id


if __name__ == '__main__':
    webhook_config = gather_webhook_configs()
