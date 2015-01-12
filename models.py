from google.appengine.ext import db

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    username = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)
    profile_url = db.StringProperty(required=True)
    messages = db.ListProperty(db.Key)

class Video(db.Model):
  url = db.StringProperty(required=True)
  vid = db.StringProperty(required=True)
  source = db.StringProperty(required=True, choices=['youtube'])
  created = db.DateTimeProperty(auto_now_add=True)
  # uploader
  description = db.StringProperty()

class Danmaku(db.Model):
  video = db.ReferenceProperty(Video)
  timestamp = db.FloatProperty(required=True)
  content = db.StringProperty(required=True, multiline=False)
  creator = db.ReferenceProperty(User)
  created = db.DateTimeProperty(auto_now_add=True)