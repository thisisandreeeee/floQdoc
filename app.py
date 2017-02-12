from __future__ import print_function
from flask import Flask, url_for, request
from gevent.wsgi import WSGIServer
from settings import *
from creds import APP_ID, BOT_TOKEN
from pprint import pprint
from helper import *
from instruct import instructions
from pyflock import FlockClient, verify_event_token
from pyflock import Message, SendAs, Attachment, Views, WidgetView, HtmlView, ImageView, Image, Download, Button, OpenWidgetAction, OpenBrowserAction, SendToAppAction
import json

app = Flask(__name__)
flock_client = FlockClient(token=BOT_TOKEN, app_id=APP_ID)

@app.route("/events", methods=['POST'])
def events():
    data = json.loads(request.data)
    pprint(data)
    event_name = data['name']

    # auth event when installing app
    if event_name == 'app.install':
        token = data['token']
        user_id = data['userId']
        save_credentials(user_id, token)

    elif event_name == 'chat.slashCommand':
        # victor
        instructions()

    elif event_name == 'client.flockmlAction':
        if 'actionId' in data.keys():
            if data['actionId'] == 'remind':
                # victor: implement reminder for 30 minutes
                print("this fired!")
                pass
    return event_name, 200

@app.route("/floqdoc", methods=['POST'])
def floqdoc():
    try:
        data = json.loads(request.data)
        pprint(data)
        if data['event_name'] == 'question.assign':
            question_id = data['question_id']
            asker_id = data['asker']
            asker_obj = get_tokens(asker_id)
            asker_name = "{} {}".format(asker_obj['first_name'], asker_obj['last_name'])
            ask_url = 'https://devweek.kyletan.me/ask/{}'.format(question_id)
            views = Views()
            markup = create_flockml(asker_id, asker_name, data['question_title'], ask_url)
            views.add_flockml(markup)

            groups = get_groups()
            for group in data['assigned_to']:
                # send attachment to group
                recipient = groups['by_name'][group]
                attachment = Attachment(title='Answer or Remind', views=views)
                button_message = Message(to = recipient, attachments = [attachment])
                res = flock_client.send_chat(button_message)
                print(res)

    except ValueError, e:
        return '{} - Try json.dumps.'.format(e), 500
    return 'ok'

@app.route("/ready")
def ready():
    # users are redirected here after install, we can show a config page here
    return "installed"

if __name__=="__main__":
    server = WSGIServer(("", FLOCK_PORT), app)
    print('Serving on port', FLOCK_PORT)
    server.serve_forever()
