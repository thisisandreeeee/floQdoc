from __future__ import print_function
from settings import *
from creds import *
from pprint import pprint
import json
import requests
import os

def save_credentials(user_id, token):
    tokens = {}
    if os.path.exists(TOKEN_FILE):
        tokens = json.loads(open(TOKEN_FILE).read())
    if user_id not in tokens:
        tokens['users'][user_id] = {
            'token': token
        }
        tokens['changed'] = True
        open(TOKEN_FILE, 'w').write(json.dumps(tokens, indent=4))

# def _send_message(recipient, message):
#     tokens = _tokens()
#     payload = {
#         'to': recipient,
#         'text': message,
#         'token': BOT_TOKEN
#     }
#     r = requests.post('https://api.flock.co/v1/chat.sendMessage', data=payload)
#     print(r.status_code, r.json())

def get_tokens():
    tokens = json.loads(open(TOKEN_FILE).read())
    if tokens['changed']:
        for user_id, dic in tokens['users'].iteritems():
            if len(dic.values()) == 1:
                r = requests.get('https://api.flock.co/v1/users.getInfo?token={}'.format(dic['token']))
                user_obj = r.json()
                tokens['users'][user_id] = {
                    'first_name': user_obj['firstName'],
                    'last_name': user_obj['lastName'],
                    'role': user_obj['role'],
                    'token': dic['token']
                }
                print(r.status_code, tokens['users'][user_id])
        tokens['changed'] = False
        open(TOKEN_FILE, 'w').write(json.dumps(tokens, indent=4))
    return tokens

def get_groups():
    groups = json.loads(open(GROUP_FILE).read())
    r = requests.get('https://api.flock.co/v1/groups.list?token={}'.format(ADMIN_TOKEN))
    groups_by_id, groups_by_name = groups['by_id'], groups['by_name']
    changed = False
    for group in r.json():
        _id, _name = group['id'], group['name']
        if _id not in groups_by_id:
            groups_by_id[_id] = _name
            changed = True
        if _name not in groups_by_name:
            groups_by_name[_name] = _id
            changed = True
    groups['by_id'] = groups_by_id
    groups['by_name'] = groups_by_name
    open(GROUP_FILE, 'w').write(json.dumps(groups, indent=4))
    return groups