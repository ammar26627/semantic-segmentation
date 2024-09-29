# app/__init__.py

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import ee, os
from google.oauth2.service_account import Credentials
from app.routes import api_bp

def create_app():

    app = Flask(__name__)
    CORS(app)

    initialize_earth_engine()

    app.register_blueprint(api_bp)
    return app

def initialize_earth_engine():
    load_dotenv()
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    scopes = ['https://www.googleapis.com/auth/earthengine']
    credentials = Credentials.from_service_account_file(credentials_path, scopes= scopes)
    ee.Initialize(credentials)
