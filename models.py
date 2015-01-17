from google.appengine.ext import db
from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
from google.appengine.ext import blobstore
import urllib2
import urlparse

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

class Message(ndb.Model):
  sender = ndb.StringProperty(required=True)
  receiver = ndb.StringProperty(required=True)
  content = ndb.TextProperty(required=True, indexed=False)
  title = ndb.StringProperty(required=True, indexed=False)

Video_Category = ['Anime', 'Music', 'Dance', 'Game', 'Entertainment', 'Techs', 'Sports', 'Movie', 'TV Drama']
Video_SubCategory = {'Anime': ['Continuing Anime', 'Finished Anime', 'MAD/AMV/GMV', 'MMD/3D', 'Original/Voice Acting', 'General']
                  , 'Music': ['Music Sharing', 'Cover Version', 'Instrument Playing', 'VOCALOID/UTAU', 'Music Selection', 'Sound Mix']
                  , 'Dance': ['Dance']
                  , 'Game': ['Game Video', 'Game Guides/Commentary', 'Eletronic Sports', 'Mugen']
                  , 'Entertainment': ['Funny Video', 'Animal Planet', 'Tasty Food', 'Entertainment TV Show']
                  , 'Techs': ['Documentary', 'Various Techs', 'Wild Techs', 'Funny Tech Intro']
                  , 'Sports': ['Amazing Human', 'Sports Video', 'Tournament']
                  , 'Movie': ['Movie', 'Micro/Short Film', 'Trailer/Highlights']
                  , 'TV Drama': ['Continuing Drama', 'Finished Drama', 'Tokusatsu', 'Trailer/Highlights']}

class VideoList(ndb.Model):
  user_belonged = ndb.StringProperty(required=True)
  title = ndb.StringProperty(required=True)
  video_counter = ndb.IntegerProperty(required=True)

class Video(ndb.Model):
  url = ndb.StringProperty(indexed=False)
  vid = ndb.StringProperty(required=True, indexed=False)
  source = ndb.StringProperty(required=True, choices=['youtube'])
  created = ndb.DateTimeProperty(auto_now_add=True)
  uploader = ndb.StringProperty(required=True)
  description = ndb.StringProperty(required=True)
  title = ndb.StringProperty(required=True)
  category = ndb.StringProperty(required=True, choices=Video_Category)
  subcategory = ndb.StringProperty(required=True)

  # video_list_belonged = ndb.KeyProperty(kind='VideoList', required=True, indexed=False)
  video_order = ndb.IntegerProperty(required=True, default=1)
  danmaku_counter = ndb.IntegerProperty(default=0)
  comment_counter = ndb.IntegerProperty(default=0)
  tags = ndb.StringProperty(repeated=True);
  banned_tags = ndb.StringProperty(repeated=True);

  hits = ndb.IntegerProperty(default=0)
  likes = ndb.IntegerProperty(default=0)
  bullets = ndb.IntegerProperty(default=0)
  be_collected = ndb.IntegerProperty(default=0)

  @staticmethod
  def parse_url(raw_url):
    if not urlparse.urlparse(raw_url).scheme:
      raw_url = "http://" + raw_url

    try:
      req = urllib2.urlopen(raw_url)
    except:
      return {'error': 'invalid url'}
    else:
      url_parts = raw_url.split('//')[-1].split('/')
      source = url_parts[0].split('.')[-2]
      if source == 'youtube':
        vid = url_parts[-1].split('=')[-1]
        url = 'http://www.youtube.com/embed/' + vid
      else:
        url = raw_url
      return {'url': url, 'vid': vid, 'source': source}

  @staticmethod
  def getID():
    try:
        Video.id_counter += 1
    except AttributeError:
        Video.id_counter = 1
    return Video.id_counter

  @staticmethod
  def Create(raw_url, username, description, title, category, subcategory):
    res = Video.parse_url(raw_url)
    if res.get('error'):
      return 'URL Error.'
    else:
      if (category in Video_Category) and (subcategory in Video_SubCategory[category]):
        video = Video(
          id = 'dt'+str(Video.getID()),
          url = raw_url,
          vid = res['vid'],
          source = res['source'],
          uploader = username,
          description = description,
          title = title, 
          category = category,
          subcategory = subcategory,
          video_order = 1,
        )
        video.put()
        return video
      else:
        return 'Category mismatch.'

class Danmaku(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  position = db.StringProperty(required=True, default='RightToLeft', choices=['RightToLeft', 'Top', 'Bottom'])
  color = db.IntegerProperty(required=True, default=255*256*256+255*256+255)
  # creator = db.ReferenceProperty(User)
  # order = ndb.IntegerProperty(required=True)
  protected = ndb.BooleanProperty(required=True)
  creator = ndb.StringProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

class Comment(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  creator = ndb.StringProperty(required=True)
  content = ndb.TextProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  floor = ndb.IntegerProperty(required=True)
  inner_comment_counter = ndb.IntegerProperty(required=True, indexed=False)

class CommentOfComment(ndb.Model):
  comment_belonged = ndb.KeyProperty(kind='Comment', required=True)
  creator = ndb.StringProperty(required=True)
  content = ndb.TextProperty(required=True, indexed=False)
  floor = ndb.IntegerProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

class AtUser(ndb.Model):
  sender = ndb.StringProperty(required=True)
  receiver = ndb.StringProperty(required=True)
  comment = ndb.KeyProperty(kind='Comment', indexed=False);
  inner_comment = ndb.KeyProperty(kind='CommentOfComment', indexed=False);
  danmaku = ndb.KeyProperty(kind='Danmaku', indexed=False)
