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
from lib.helpers import model_json

import routes.activities
import routes.users
import routes.general
import routes.messages

app = Flask(__name__)


#init_cloudwatch(app)
init_honeycomb(app)
init_cors(app)
init_xray(app)
init_rollbar(app)



# load routes ---------------
routes.general.load(app)
routes.activities.load(app)
routes.messages.load(app)
routes.users.load(app)



if __name__ == "__main__":
  app.run(debug=True)