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
import time
from threading import Thread

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

    elif event_name == 'client.slashCommand':
        print('inside slash')
        # victor
        groups = get_groups()
        receipient = groups['by_name']['Engineering']
        msg = Message(to=receipient, text='floqdoc command called')
        res = flock_client.send_chat(msg)

    elif event_name == 'client.flockmlAction':
        if 'actionId' in data.keys():
            if data['actionId'] == 'remind':
                # TODO find out if i can tag someone and send message in the group
                # TODO questions.answered
                # TODO idea for expiring data, add a timestamp
                # victor: implement reminder for 30 minutes
                # user id instead
                groups = get_groups()
                receipient = groups['by_name']['Engineering']
                text_msg_to_user = "@" + data['userName'] + " reminder set for 30mins"

                msg = Message(to=receipient, text=text_msg_to_user)
                res = flock_client.send_chat(msg)

                t = Thread(target = send_after_n_mins, args = (1, data))
                t.start()

    return json.dumps({'event_name': event_name})

def send_after_n_mins(n, data):
    print("\nENTERED AND PRINT HERE\n")
    time.sleep(n*60)
    print("\nTHIS WILL PRINT AFTER A MINUTE\n")
    groups = get_groups()
    receipient = groups['by_name']['Engineering']

# TODO create file in json/ called remind.json




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
                # TODO read remind.json, remind[recipient] = data['question_title']
                remind_data = get_remind()

                recipient_data = {}
                recipient_data['asker_id'] = asker_id
                recipient_data['asker_name'] = asker_name
                recipient_data['ask_url'] = ask_url
                recipient_data['question_title'] = data['question']
                recipient_data['timestamp'] = time.mktime(datetime.datetime.utcnow().timetuple())
                remind_data[recipient] = recipient_data
                save_and_update_remind(remind_data)

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
