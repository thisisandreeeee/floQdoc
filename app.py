from __future__ import print_function
from flask import Flask, render_template, url_for, request
from gevent.wsgi import WSGIServer
from settings import TOKEN_FILE
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
        tokens[user_id] = token
        open(TOKEN_FILE, 'w').write(json.dumps(tokens, indent=4))

def _send_message(recipient, message):
    tokens = json.loads(open(TOKEN_FILE).read())
    payload = {
        'to': recipient,
        'text': message,
        'token': tokens[recipient]
    }
    r = requests.post('https://api.flock.co/v1/chat.sendMessage', data=payload)
    print(r.status_code, r.json())

@app.route("/events", methods=['POST'])
def events():
    data = json.loads(request.data)
    pprint(data)
    event_name = data['name']

    # auth event when installing app
    if event_name == 'app.install':
        # user_token = data['userToken']
        token = data['token']
        user_id = data['userId']
        _save_credentials(user_id, token)

    # bot events
    elif event_name == 'chat.receiveMessage':
        message = data['message']
        tokens = json.loads(open(TOKEN_FILE).read())
        if message['from'] in tokens: # only users who have installed the app will be added to the token file
            if message['text'].lower() == 'ping':
                _send_message(message['from'], 'pong')
        else: # when the bot receives a message in the lobby
            pass

    # slash events
    elif event_name == 'client.slashCommand':
        if data['command'] == 'ping':
            _send_message(data['userId'], 'pong')

    return event_name

@app.route("/ready")
def ready():
    return "installed"

if __name__=="__main__":
    PORT = 5000
    server = WSGIServer(("", PORT), app)
    print('Serving on port', PORT)
    server.serve_forever()
