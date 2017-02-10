from __future__ import print_function
from flask import Flask, render_template, url_for, request
from gevent.wsgi import WSGIServer
from settings import TOKEN_FILE, LOBBY_ID, FLOCK_PORT, ALEXA_PORT
from creds import APP_ID, APP_SECRET, BOT_USER_ID, BOT_TOKEN
from pprint import pprint
import json
import requests
import os

app = Flask(__name__)

def _save_credentials(user_id, token):
    tokens = {}
    if os.path.exists(TOKEN_FILE):
        tokens = json.loads(open(TOKEN_FILE).read())
    if user_id not in tokens:
        tokens['users'][user_id] = {
            'token': token
        }
        tokens['changed'] = True
        open(TOKEN_FILE, 'w').write(json.dumps(tokens, indent=4))

def _send_message(recipient, message):
    tokens = _tokens()
    payload = {
        'to': recipient,
        'text': message,
        'token': BOT_TOKEN
    }
    r = requests.post('https://api.flock.co/v1/chat.sendMessage', data=payload)
    print(r.status_code, r.json())

def _tokens():
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

@app.route("/events", methods=['POST'])
def events():
    data = json.loads(request.data)
    pprint(data)
    event_name = data['name']

    # auth event when installing app
    if event_name == 'app.install':
        token = data['token']
        user_id = data['userId']
        _save_credentials(user_id, token)

    # bot events
    elif event_name == 'chat.receiveMessage':
        message = data['message']
        tokens = _tokens()
        if message['from'] in tokens: # only users who have installed the app will be added to the token file
            if message['text'].lower() == 'ping':
                _send_message(message['from'], 'pong')
        else: # when the bot receives a message in the lobby
            pass

    # slash events
    elif event_name == 'client.slashCommand':
        if data['command'] == 'ping':
            _send_message(LOBBY_ID, 'pong')

    return event_name

@app.route("/ready")
def ready():
    # users are redirected here after install, we can show a config page here
    return "installed"

if __name__=="__main__":
    server = WSGIServer(("", FLOCK_PORT), app)
    print('Serving on port', FLOCK_PORT)
    server.serve_forever()
