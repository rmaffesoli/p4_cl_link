#!/usr/bin/env python
from __future__ import print_function
import pprint
import os
import re
import requests


SERVER_ADDRESS = os.environ.get('DAM_SERVER_ADDRESS')
ACCOUNT_KEY = os.environ.get('DAM_ACCOUNT_KEY')

def get_or_create_metadata_field(field_name):
    metadata_field_url = "{}/api/company/file_attribute_templates".format(SERVER_ADDRESS)
    
    all_metadata_params = {
        'account_key': ACCOUNT_KEY,
    }
        
    all_metadata_response = requests.get(
        metadata_field_url, 
        params=all_metadata_params,
    )

    if all_metadata_response.status_code > 299:
        print('request failed')
        return
    
    all_metadata = all_metadata_response.json()
    
    image_description_field = [_ for _ in all_metadata['results'] if _['name'] == field_name]

    if image_description_field:
        image_description_field = image_description_field[0]
    else:
        add_metadata_field_params = {
            'account_key': ACCOUNT_KEY,
            "name": field_name,
            "type": "text",
            "available_values":[],
            "hidden": False
        }
        
        add_metadata_field_response = requests.post(
            metadata_field_url, 
            json=add_metadata_field_params,
        )

        image_description_field = add_metadata_field_response.json()

    return image_description_field


def attach_metadata(selected_asset, field_name, value):

    image_description_field = get_or_create_metadata_field(field_name)

    add_asset_metadata_url = "{}/api/p4/batch/custom_file_attributes".format(SERVER_ADDRESS)
    
    add_asset_metadata_body = {
        'account_key': ACCOUNT_KEY,
        'paths':[
            {
                'path': selected_asset
            }
        ],
        'create': [
            {
                'uuid': image_description_field['uuid'],
                'value': value
            }
        ]
    }
        
    if '@' in selected_asset:
        asset_path, asset_identifier = selected_asset.split('@')
        add_asset_metadata_body['paths'][0]['path'] = asset_path
        add_asset_metadata_body['paths'][0]['identifier'] = asset_identifier

    add_asset_metadata_response = requests.put(
        add_asset_metadata_url, 
        json=add_asset_metadata_body,
    )

    print(add_asset_metadata_response)
    try:
        pprint.pp(add_asset_metadata_response.json())
    except:
        print('no metadata json')


def attach_additional_tags(selected_asset, tags):
    if not tags:
        return
    
    add_asset_tags_url = "{}/api/p4/batch/tags".format(SERVER_ADDRESS)
    add_asset_tags_body = {
        'account_key': ACCOUNT_KEY,
        'paths':[
            {
                'path': selected_asset
            }
        ],
        'create': tags,
    }
        
    if '@' in selected_asset:
        asset_path, asset_identifier = selected_asset.split('@')
        add_asset_tags_body['paths'][0]['path'] = asset_path
        add_asset_tags_body['paths'][0]['identifier'] = asset_identifier

    add_asset_tags_response = requests.put(
        add_asset_tags_url, 
        json=add_asset_tags_body,
    )

    print(add_asset_tags_response)
    try:
        pprint.pp(add_asset_tags_response.json())
    except:
        print('no tags json')


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
        add_asset_weblink_body['text'] = 'Jira'
    elif type == 'plan':
        add_asset_weblink_body['config'] = {'item_id': id}            
        add_asset_weblink_body['webhook'] = webhook
        add_asset_weblink_body['text'] = 'P4Plan'
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

    print(add_asset_weblink_response)
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

    # print(webhook_config_response)
    try:
        # pprint.pp(webhook_config_response.json())
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

    # pprint.pp(webhook_dict)
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
        if webhook_data['service'] == 'plan':
            plan_webhook_uuid = webhook_data['uuid']
            plan_url = webhook_data['url']
            plan_id = weblink.split('/')[-1]
        elif webhook_data['service'] == 'jira':
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
