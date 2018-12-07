# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import http.server
import http.client
import urllib.parse
import requests
import time
import json
import asyncio
from botbuilder.schema import (Activity, ActivityTypes, ChannelAccount)
from botframework.connector import ConnectorClient
from botframework.connector.auth import (MicrosoftAppCredentials,
                                         JwtTokenValidation, SimpleCredentialProvider)
#update these values with your own 
APP_ID = ''
APP_PASSWORD = ''
HOST = ""
ENDPOINT_KEY=""
KB=""
METHOD = "/knowledgebases/"+KB+"/generateAnswer"


class BotRequestHandler(http.server.BaseHTTPRequestHandler):
    @staticmethod
    def __create_reply_activity(request_activity, text):
        return Activity(
            type=ActivityTypes.message,
            channel_id=request_activity.channel_id,
            conversation=request_activity.conversation,
            recipient=request_activity.from_property,
            from_property=request_activity.recipient,
            text=text,
            service_url=request_activity.service_url)

    def __handle_conversation_update_activity(self, activity):
        print("in conversation update activity")
        self.send_response(202)
        self.end_headers()
        if activity.members_added[0].id != activity.recipient.id:
            credentials = MicrosoftAppCredentials(APP_ID, APP_PASSWORD)
            reply = BotRequestHandler.__create_reply_activity(activity, 'Hello and welcome to the echo bot!')
            connector = ConnectorClient(credentials, base_url=reply.service_url)
            connector.conversations.send_to_conversation(reply.conversation.id, reply)


            

    def __get_response_from_QNA(self, path, content):
        headers = {
            'Authorization': 'EndpointKey ' + ENDPOINT_KEY,
            'Content-Type' : 'application/json'
        }
        question = {
            'question':''+content
        }
        cont = json.dumps(question)
        conn = http.client.HTTPSConnection(HOST)
       
      #Add the url you will be hitting, for example QnA bot endpoint
        url = ""
       
        r = requests.post(url, data=cont, headers=headers)
        print("response")
        t = json.loads((r.text))
        return t['answers'][0]['answer']
        #response = conn.getresponse()

    def __parse_json(self, res):
        print(json.loads(str(res)))
        r = json.loads(res)
        print("here")
        print(r['answers'][0]['answer'])
        return "test"
        #r['answers'][0]['answer']""

    def __handle_message_activity(self, activity):
        print("in handle message")
        self.send_response(200)
        self.end_headers()
        credentials = MicrosoftAppCredentials(APP_ID, APP_PASSWORD)
        connector = ConnectorClient(credentials, base_url=activity.service_url)
        res = self.__get_response_from_QNA(METHOD,activity.text)

        reply = BotRequestHandler.__create_reply_activity(activity, 'You said: %s' % res)
        connector.conversations.send_to_conversation(reply.conversation.id, reply)

    def __handle_authentication(self, activity):
        credential_provider = SimpleCredentialProvider(APP_ID, APP_PASSWORD)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(JwtTokenValidation.authenticate_request(
                activity, self.headers.get("Authorization"), credential_provider))
            return True
        except Exception as ex:
            self.send_response(401, ex)
            self.end_headers()
            return False
        finally:
            loop.close()

    def __unhandled_activity(self):
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(str(body, 'utf-8'))
        activity = Activity.deserialize(data)
        print(activity.type)
        print(ActivityTypes.conversation_update.value)
        print(ActivityTypes.message.value)

        if not self.__handle_authentication(activity):
            return

        if activity.type == ActivityTypes.conversation_update.value:
            self.__handle_conversation_update_activity(activity)
        elif activity.type == ActivityTypes.message.value:
            self.__handle_message_activity(activity)
        else:
            self.__unhandled_activity()
            
try:
    SERVER = http.server.HTTPServer(('localhost', 9000), BotRequestHandler)
    print('Started http server')
    SERVER.serve_forever()
except KeyboardInterrupt:
    print('^C received, shutting down server')
    SERVER.socket.close()
