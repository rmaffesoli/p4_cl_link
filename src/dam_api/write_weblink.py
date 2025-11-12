#!/usr/bin/env python
from __future__ import print_function
import os
import re
import requests


SERVER_ADDRESS = os.environ.get('DAM_SERVER_ADDRESS')
ACCOUNT_KEY = os.environ.get('DAM_ACCOUNT_KEY')


def attach_weblink(selected_asset, weblink):
    if not (weblink):
        return
    
    if '@' in selected_asset:
        selected_asset = selected_asset.split('@')[0]

    add_asset_weblink_url = "{}/api/weblinks".format(SERVER_ADDRESS)
    add_asset_weblink_body = {
        'account_key': ACCOUNT_KEY,
        'depot_path': selected_asset,
        'url': weblink,
    }

    webhook_config = gather_webhook_configs()
    type, webhook, id = gather_weblink_type_id(weblink, webhook_config)
    if type == 'jira':
        add_asset_weblink_body['config'] = {'issue_id': id}
        add_asset_weblink_body['webhook'] = webhook
    elif type == 'plan':
        add_asset_weblink_body['config'] = {'item_id': id}            
        add_asset_weblink_body['webhook'] = webhook
    else:
        title_pattern = r"(?<=//)[^/:]*"
        weblink_matches = re.search(title_pattern, weblink)
        title = None
        if weblink_matches:
            title = weblink_matches.group()
        add_asset_weblink_body['text'] = title

    add_asset_weblink_response = requests.post(
        add_asset_weblink_url, 
        json=add_asset_weblink_body,
    )

    try:
        print(add_asset_weblink_response.json())
    except:
        print('no weblink json')  


def gather_webhook_configs():
    webhook_dict = {}
    webhook_config_url = "{}/api/webhooks".format(SERVER_ADDRESS)
    webhook_config_body = {
        'account_key': ACCOUNT_KEY,
    }

    webhook_config_response = requests.get(
        webhook_config_url, 
        json=webhook_config_body,
    )

    try:
        response_json = webhook_config_response.json()
    except:
        print('no webhook json')
        response_json = None
    
    for webhook in response_json['results']:
        webhook_dict[webhook['name']] = {
            'uuid': webhook['uuid'],
            'service': webhook['service'],
            'url' : webhook['config']['url']
        }

    return webhook_dict


def gather_weblink_type_id(weblink, webhook_config):
    webhook_uuid = None
    weblink_type = None
    webhook_id = None

    plan_id = None
    plan_webhook_uuid = None
    plan_url = None

    jira_id = None
    jira_webhook_uuid = None
    jira_url = None

    for _, webhook_data in webhook_config.items():
        if 'plan' in webhook_data['service']:
            plan_webhook_uuid = webhook_data['uuid']
            plan_url = webhook_data['url']
            plan_id = weblink.split('/')[-1]
        elif 'jira' in webhook_data['service']:
            jira_webhook_uuid = webhook_data['uuid']
            jira_url = webhook_data['url']
            jira_id = weblink.split('/')[-1]
    
    
    if plan_url and plan_url in weblink:
        weblink_type = 'plan'
        webhook_uuid = plan_webhook_uuid
        webhook_id = plan_id

    elif jira_url and jira_url in weblink:
        weblink_type = 'jira'
        webhook_uuid = jira_webhook_uuid
        webhook_id = jira_id
    return weblink_type, webhook_uuid, webhook_id


if __name__ == '__main__':
    webhook_config = gather_webhook_configs()
