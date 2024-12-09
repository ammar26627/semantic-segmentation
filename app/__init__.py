# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
from datetime import timedelta
import ee, os, json
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from app.routes import api_bp


def create_app(isTest=False):

    access_token = initialize_earth_engine()

    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
    app.config['SESSION_FILE_THRESHOLD'] = 20
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['TESTING'] = isTest
    app.config['ACCESS_TOKEN'] = access_token

    Session(app)
    # socketio = SocketIO(app, cors_allowed_origins="*")
    CORS(app, supports_credentials=True)


    app.register_blueprint(api_bp)
    return app

def initialize_earth_engine():
    load_dotenv()
    data = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    credentials = json.loads(data)
    scopes = ['https://www.googleapis.com/auth/earthengine']
    credentials = Credentials.from_service_account_info(credentials, scopes= scopes)
    request = Request()
    credentials.refresh(request)
    access_token = credentials.token
    ee.Initialize(credentials)
    return(access_token)
