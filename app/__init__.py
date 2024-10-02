# app/__init__.py

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import ee, os, json
from google.oauth2.service_account import Credentials
from app.routes import api_bp

def create_app():

    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    CORS(app, supports_credentials=True)

    initialize_earth_engine()

    app.register_blueprint(api_bp)
    return app

def initialize_earth_engine():
    load_dotenv()
    data = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    credentials = json.loads(data)
    scopes = ['https://www.googleapis.com/auth/earthengine']
    credentials = Credentials.from_service_account_info(credentials, scopes= scopes)
    ee.Initialize(credentials)
