from flask import Flask, request
from flask_cors import CORS
from pymongo import MongoClient
from main.tools import JsonResp
from jose import jwt
import os
from pymongo.server_api import ServerApi

# Import Routes
from main.user.routes import user_blueprint

def create_app():

  # Flask Config
  app = Flask(__name__)
  app.config.from_pyfile("config/config.cfg")
  cors = CORS(app, resources={r"/*": { "origins": app.config["FRONTEND_DOMAIN"] }})

  # Misc Config
  os.environ["TZ"] = app.config["TIMEZONE"]
  uri = "mongodb+srv://forgetful:qL6YzwjDKXJwHHx3@cluster0.qi4w9mc.mongodb.net/?retryWrites=true&w=majority"
  # Database Config
  if app.config["ENVIRONMENT"] == "development":
    mongo = MongoClient(app.config["MONGO_HOSTNAME"], app.config["MONGO_PORT"])
    # mongo = MongoClient(uri, server_api=ServerApi('1'))
    # mongo
    app.db = mongo[app.config["MONGO_APP_DATABASE"]]
  else:
    mongo = MongoClient(uri)
    mongo[app.config["MONGO_AUTH_DATABASE"]].authenticate(app.config["MONGO_AUTH_USERNAME"], app.config["MONGO_AUTH_PASSWORD"])
    app.db = mongo[app.config["MONGO_APP_DATABASE"]]

  # Register Blueprints
  app.register_blueprint(user_blueprint, url_prefix="/user")

  # Index Route
  @app.route("/")
  def index():
    return JsonResp({ "status": "Online" }, 200)
  
  return app