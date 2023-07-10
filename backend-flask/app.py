from flask import Flask
from flask import request, g
from flask_cors import CORS, cross_origin
import os
import sys

from lib.rollbar import init_rollbar
from lib.xray import init_xray
from lib.honeycomb import init_honeycomb
from lib.cors import init_cors
from lib.cognito_jwt_token import jwt_required
from lib.cloudwatch import init_cloudwatch

from services.home_activities import *
from services.notifications_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *
from services.users_short import *
from services.update_profile import *


# app.py updates Honeycomb
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# AWS X-RAY

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# Cloudwatch Logs
import watchtower
import logging
from time import strftime

# Rollbar import
import os
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception


# Configuring Logger to Use CloudWatch - setup a log group
#LOGGER = logging.getLogger(__name__)
#LOGGER.setLevel(logging.DEBUG)
#console_handler = logging.StreamHandler()
#cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
#LOGGER.addHandler(console_handler)
#LOGGER.addHandler(cw_handler)
#LOGGER.info("test log")


# AWS X-RAY
#xray_url = os.getenv("AWS_XRAY_URL")
#xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)


app = Flask(__name__)


# Initialize automatic instrumentation with Flask   //// HoneyComb
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


# Rollbar -------------------------
#init_cloudwatch(app)
init_honeycomb(app)
init_cors(app)
init_xray(app)
with app.app_context():
  rollbar = init_rollbar(app)


def return_model(model):
  if model['errors'] is not None:
    return model ['errors'], 422
  else:
    return model ['data'], 200


@app.route('/api/health-check')
def health_check():
  return {'success': True}, 200

#@app.route('/rollbar/test')
#def rollbar_test():
#    rollbar.report_message('Hello World!', 'warning')
#    return "Hello World!"

@app.route("/api/message_groups", methods=['GET'])
@jwt_required()
def data_message_groups():
      model = MessageGroups.run(
        cognito_user_id=g.cognito_user_id
        )
      if model['errors'] is not None:
        return model['errors'], 422
      else:
        return model['data'], 200
 

@app.route("/api/messages/<string:message_group_uuid>", methods=['GET'])
@jwt_required()
def data_messages(message_group_uuid): 
    model = Messages.run(
      cognito_user_id=g.cognito_user_id,
      message_group_uuid=message_group_uuid
    )
    if model['errors'] is not None:
      return model['errors'], 422
    else:
      return model['data'], 200

@app.route("/api/profile/update", methods=['POST','OPTIONS'])
@cross_origin()
@jwt_required()
def data_update_profile():
  bio          = request.json.get('bio',None)
  display_name = request.json.get('display_name',None)
  access_token = extract_access_token(request.headers)
  model = UpdateProfile.run(
      cognito_user_id=g.cognito_user_id,
      bio=bio,
      display_name=display_name
    )
  return model_json(model)


@app.route("/api/messages", methods=['POST','OPTIONS'])
@cross_origin()
@jwt_required()
def data_create_message():
  user_receiver_handle = request.json.get('handle',None)
  message_group_uuid = request.json.get('message_group_uuid',None)
  message = request.json['message']
    
  if message_group_uuid == None:
      # Create for the first time
      model = CreateMessage.run(
        mode="create",
        message=message,
        cognito_user_id=g.cognito_user_id,
        user_receiver_handle=user_receiver_handle
      )
  else:
      # Push onto existing Message Group
      model = CreateMessage.run(
        mode="update",
        message=message,
        message_group_uuid=message_group_uuid,
        cognito_user_id=g.cognito_user_id
      )
    
  if model['errors'] is not None:
      return model['errors'], 422
  else:
      return model['data'], 200

@app.route("/api/activities/notifications", methods=['GET'])
def data_notifications():
  data = NotificationsActivities.run()
  return data, 200


def default_home_feed(e):
  app.logger.debug(e)
  app.logger.debug("unauthenticated")
  data = HomeActivities.run()
  return data, 200

@app.route("/api/activities/home", methods=['GET'])
#@xray_recorder.capture('activities_home')
@jwt_required(on_error=default_home_feed)
def data_home():
  data = HomeActivities.run(cognito_user_id=g.cognito_user_id)
  return data, 200

@app.route("/api/activities/@<string:handle>", methods=['GET'])
#@xray_recorder.capture('activities_users')
def data_handle(handle):
  model = UserActivities.run(handle)
  return return_model(model)
 

@app.route("/api/activities/search", methods=['GET'])
def data_search():
  term = request.args.get('term')
  model = SearchActivities.run(term)
  return model_json(model)

@app.route("/api/activities", methods=['POST','OPTIONS'])
@cross_origin()
@jwt_required()
def data_activities():
    message = request.json['message']
    ttl = request.json['ttl']
    model = CreateActivity.run(message, g.cognito_user_id, ttl)
    return model_json(model)
  

@app.route("/api/activities/<string:activity_uuid>", methods=['GET'])
@xray_recorder.capture('activities_show')
def data_show_activity(activity_uuid):
  data = ShowActivity.run(activity_uuid=activity_uuid)
  return data, 200

@app.route("/api/activities/<string:activity_uuid>/reply", methods=['POST','OPTIONS'])
@cross_origin()
def data_activities_reply(activity_uuid):
  user_handle = 'TheChosenOne'
  message = request.json['message']
  model = CreateReply.run(message, user_handle, activity_uuid)
  return model_json(model)
  
@app.route("/api/users/@<string:handle>/short", methods=['GET'])
def data_users_short(handle):
  data = UsersShort.run(handle)
  return data, 200

  
if __name__ == "__main__":
  app.run(debug=True)