from google.appengine.ext import db

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    messages = db.ListProperty(db.Key)

class Video(db.Model):
  url = db.StringProperty(required=True)
  vid = db.StringProperty(required=True)
  source = db.StringProperty(required=True, choices=['youtube'])
  description = db.StringProperty()

class Danmaku(db.Model):
  video = db.ReferenceProperty(Video)
  timestamp = db.TimeProperty(required=True) # datetime.time(hour, minute, second)
  content = db.StringProperty(required=True, multiline=False)
  creator = db.ReferenceProperty(User)
  created = db.DateTimeProperty(auto_now_add=True)