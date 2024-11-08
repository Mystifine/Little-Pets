import firebase_admin
from firebase_admin import db
import json
import os

# Init
def init_firebase():
  cred_obj = firebase_admin.credentials.Certificate('little-rpg-discord-bot-firebase-adminsdk-yveas-fbba1c43e7.json')
  default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL' : os.getenv("FIRE_BASE_URL")
  })

def dict_to_json(dict):
  json_object = json.dumps(dict, indent = 3, sort_keys = True);
  return json_object;

def json_to_dict(json_string):
  return_value = None;
  if json_string != None:
    return_value = json.loads(json_string)

  return return_value;
 
def set_data(path, data):
  ref = db.reference("/"+path);
  ref.set(dict_to_json(data));

def delete_data(path):
  ref = db.reference("/"+path);
  ref.delete();

def get_data(path):
  ref = db.reference("/"+path);
  data = ref.get();
  return json_to_dict(data);

def update_data(path, new_value):
  ref = db.reference("/"+path);
  ref.update(new_value);
        
