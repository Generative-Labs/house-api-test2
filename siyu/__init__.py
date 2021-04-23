from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys
from flask_cors import CORS, cross_origin
import stripe
import os

application = app = Flask(__name__)
cors = CORS(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://field:fieldyc2020@database-2.ccrl6jgkfooz.us-west-1.rds.amazonaws.com:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_SECRET_KEY'] = b'+S\x8b>\x07\xa3\x14|ny\xb2u'

db = SQLAlchemy(app)
# keep ithere
from siyu import routes
