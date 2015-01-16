from google.appengine.ext import db
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
from google.appengine.ext import blobstore

# class User(db.Model):
#     id = db.StringProperty(required=True)
#     created = db.DateTimeProperty(auto_now_add=True)
#     updated = db.DateTimeProperty(auto_now=True)
#     username = db.StringProperty(required=True)
#     email = db.EmailProperty(required=True)
#     profile_url = db.StringProperty(required=True)
#     messages = db.ListProperty(db.Key)
class User(webapp2_extras.appengine.auth.models.User):
  nickname = db.StringProperty()
  intro = db.StringProperty()
  profile_photo = blobstore.BlobReferenceProperty()
  favorites = db.ListProperty(db.Key)

  def set_password(self, raw_password):
    self.password = security.generate_password_hash(raw_password, length=12)

class Message(db.Model):
  sender = db.StringProperty(required=True)
  receiver = db.StringProperty(required=True)
  content = db.TextProperty(required=True)
  title = db.StringProperty(required=True)
  
Video_SubCategory = []

class Video(db.Model):
  url = db.StringProperty(required=True)
  vid = db.StringProperty(required=True)
  source = db.StringProperty(required=True, choices=['youtube'])
  created = db.DateTimeProperty(auto_now_add=True)
  uploader = db.StringProperty(required=True)
  description = db.StringProperty(required=True)
  title = db.StringProperty(required=True)
  category = db.StringProperty(required=True, choices=[''])
  
  comment_counter = db.IntegerProperty(required=True)
  tags = db.StringListProperty();
  banned_tags = db.StringListProperty();

  hits = db.IntegerProperty(required=True)
  likes = db.IntegerProperty(required=True)
  bullets = db.IntegerProperty(required=True)
  be_collected = db.IntegerProperty(required=True)

class Danmaku(db.Model):
  video = db.ReferenceProperty(Video, required=True, collection_name='danmaku_pool')
  timestamp = db.FloatProperty(required=True)
  content = db.StringProperty(required=True, multiline=False)
  # creator = db.ReferenceProperty(User)
  creator = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)

class Comment(db.Model):
  video = db.ReferenceProperty(Video, required=True, collection_name='comments')
  creator = db.StringProperty(required=True)
  floor = db.IntegerProperty(required=True)
  content = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  inner_comment_counter = db.IntegerProperty(required=True)

class CommentOfComment(db.Model):
  ori_comment = db.ReferenceProperty(Comment, required=True, collection_name='inner_comments')
  creator = db.StringProperty(required=True)
  floor = db.IntegerProperty(required=True)
  content = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)

class AtUser(db.Model):
  sender = db.StringProperty(required=True)
  receiver = db.StringProperty(required=True)
  comment = db.ReferenceProperty(Comment);
  inner_comment = db.ReferenceProperty(CommentOfComment);
  danmaku = db.ReferenceProperty(Danmaku)
