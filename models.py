from google.appengine.ext import db
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
# class User(db.Model):
#     id = db.StringProperty(required=True)
#     created = db.DateTimeProperty(auto_now_add=True)
#     updated = db.DateTimeProperty(auto_now=True)
#     username = db.StringProperty(required=True)
#     email = db.EmailProperty(required=True)
#     profile_url = db.StringProperty(required=True)
#     messages = db.ListProperty(db.Key)
class User(webapp2_extras.appengine.auth.models.User):
  def set_password(self, raw_password):
    self.password = security.generate_password_hash(raw_password, length=12)

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
  # creator = db.ReferenceProperty(User)
  creator = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)