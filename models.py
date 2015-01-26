from google.appengine.ext import db
from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
from google.appengine.ext import blobstore
from google.appengine.api import images
import urllib2
import urlparse
import time
import re
import logging

# class User(db.Model):
#     id = db.StringProperty(required=True)
#     created = db.DateTimeProperty(auto_now_add=True)
#     updated = db.DateTimeProperty(auto_now=True)
#     username = db.StringProperty(required=True)
#     email = db.EmailProperty(required=True)
#     profile_url = db.StringProperty(required=True)
#     messages = db.ListProperty(db.Key)

class History(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  last_viewed_time = ndb.DateTimeProperty(auto_now_add=True)
  # last_viewed_timestamp

class User(webapp2_extras.appengine.auth.models.User):
  nickname = ndb.StringProperty(required=True)
  intro = ndb.StringProperty(default="")
  avatar = ndb.BlobKeyProperty()
  default_avatar = ndb.IntegerProperty(default=1, choices=[1,2,3,4,5,6])
  favorites = ndb.KeyProperty(kind='Video', repeated=True)
  favorites_limit = ndb.IntegerProperty(default=100, required=True)
  # history = ndb.KeyProperty(kind='Video', repeated=True)
  history = ndb.StructuredProperty(History, repeated=True)
  subscritions = ndb.KeyProperty(kind='User', repeated=True)
  bullets = ndb.IntegerProperty(required=True, default=0)
  videos_submited = ndb.IntegerProperty(required=True, default=0)
  videos_watched = ndb.IntegerProperty(required=True, default=0)
  videos_favored = ndb.IntegerProperty(required=True, default=0)
  space_visited = ndb.IntegerProperty(required=True, default=0)
  subscribers_counter = ndb.IntegerProperty(required=True, default=0)

  def set_password(self, raw_password):
    self.password = security.generate_password_hash(raw_password, length=12)

  def get_public_info(self):
    public_info = {}
    public_info['nickname'] = self.nickname
    public_info['email'] = self.email
    public_info['intro'] = self.intro
    public_info['created'] = self.created.strftime("%Y-%m-%d %H:%M")
    if self.avatar:
      avatar_url = images.get_serving_url(self.avatar)
    else:
      avatar_url = '/static/emoticons_img/default_avatar' + str(self.default_avatar) + '.png'
    public_info['avatar_url'] = avatar_url
    public_info['space_url'] = '/user/' + str(self.key.id())
    
    return public_info

  def get_private_info(self):
    private_info = {
      'bullets': self.bullets
    }
    
    return private_info

  def get_statistic_info(self):
    statistic_info = {
      'videos_submited': self.videos_submited,
      'videos_watched': self.videos_watched,
      'videos_favored': self.videos_favored,
      'space_visited': self.space_visited,
      'subscribers_counter': self.subscribers_counter,
      'favorites_counter': len(self.favorites),
      'subscritions_counter': len(self.subscritions)
    }
    return statistic_info

  @classmethod
  def validate_nickname(cls, nickname):
    nickname = nickname.strip();
    if not nickname:
      logging.info('nickname 1')
      return None
    if re.match(r".*[@.,?!;:/\\\"'].*", nickname):
      logging.info('nickname 2')
      return None
    if len(nickname) > 30:
      logging.info('nickname 3')
      return None
    res = cls.query(cls.nickname==nickname).get()
    if res is not None:
      logging.info('nickname 4')
      return None
    return nickname

  @classmethod
  def validate_password(cls, password):
    if not password:
      logging.info('password 1')
      return None
    if not password.strip():
      logging.info('password 2')
      return None
    if len(password) < 6:
      logging.info('password 3')
      return None
    if len(password) > 40:
      logging.info('password 4')
      return None

    return password

  @classmethod
  def validate_email(cls, email):
    email = email.strip()
    if not email:
      logging.info('email 1')
      return None
    if re.match(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", email) is None:
      logging.info('email 2')
      return None

    return email

  @classmethod
  def create_pwdreset_token(cls, user_id):
    entity = cls.token_model.create(user_id, 'pwdreset')
    return entity.token

  @classmethod
  def validate_pwdreset_token(cls, user_id, token):
    return cls.validate_token(user_id, 'pwdreset', token)

  @classmethod
  def delete_pwdreset_token(cls, user_id, token):
    cls.token_model.get_key(user_id, 'pwdreset', token).delete()

  @classmethod
  def get_by_auth_token(cls, user_id, token, subject='auth'):
    """Returns a user object based on a user ID and token.
 
    :param user_id:
        The user_id of the requesting user.
    :param token:
        The token string to be verified.
    :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
    """
    token_key = cls.token_model.get_key(user_id, subject, token)
    user_key = ndb.Key(cls, user_id)
    # Use get_multi() to save a RPC call.
    valid_token, user = ndb.get_multi([token_key, user_key])
    if valid_token and user:
        timestamp = int(time.mktime(valid_token.created.timetuple()))
        return user, timestamp
 
    return None, None

class Notification(ndb.Model):
  receiver = ndb.KeyProperty(kind='User', required=True)
  content = ndb.TextProperty(required=True, indexed=False)
  title = ndb.StringProperty(required=True, indexed=False)


class Message(ndb.Model):
  sender = ndb.KeyProperty(kind='User', required=True)
  receiver = ndb.KeyProperty(kind='User', required=True)
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

URL_NAME_DICT = {
  # Categories
  'Anime': ['anime', {
    # Subcategories of Anime
    'Continuing Anime': 'continuing',
    'Finished Anime': 'finished',
    'MAD/AMV/GMV': 'mad',
    'MMD/3D': 'mmd',
    'Original/Voice Acting': 'original',
    'General': 'general',
  }],
  'Music': ['music', {
    # Subcategories of Music
    'Music Sharing': 'sharing',
    'Cover Version': 'cover',
    'Instrument Playing': 'instrument',
    'VOCALOID/UTAU': 'vocaloid',
    'Music Selection': 'selection',
    'Sound Mix': 'mix',
  }],
  'Dance': ['dance', {
    # Subcategories of Dance
    'Dance': 'dance',
  }],
  'Game': ['game', {
    # Subcategories of Game
    'Game Video': 'video',
    'Game Guides/Commentary': 'guides',
    'Eletronic Sports': 'esports',
    'Mugen': 'mugen',
  }],
  'Entertainment': ['ent', {
    # Subcategories of Entertainment
    'Funny Video': 'fun',
    'Animal Planet': 'animal',
    'Tasty Food': 'food',
    'Entertainment TV Show': 'show',
  }],
  'Techs': ['techs', {
    # Subcategories of Techs
    'Documentary': 'documentary',
    'Various Techs': 'various',
    'Wild Techs': 'wild',
    'Funny Tech Intro': 'fun',
  }],
  'Sports': ['sports', {
    # Subcategories of Sports
    'Amazing Human': 'human',
    'Sports Video': 'video',
    'Tournament': 'tournament',
  }],
  'Movie': ['movie', {
    # Subcategories of Movie
    'Movie': 'movie',
    'Micro/Short Film': 'micro',
    'Trailer/Highlights': 'trailer',
  }],
  'TV Drama': ['drama', {
    # Subcategories of TV Drama
    'Continuing Drama': 'continuing',
    'Finished Drama': 'finished',
    'Tokusatsu': 'tokusatsu',
    'Trailer/Highlights': 'trailer',
  }],
};

class PlayList(ndb.Model):
  user_belonged = ndb.KeyProperty(kind='User', required=True)
  title = ndb.StringProperty(required=True)
  video_counter = ndb.IntegerProperty(required=True)

class Video(ndb.Model):
  url = ndb.StringProperty(indexed=False)
  vid = ndb.StringProperty(required=True, indexed=False)
  source = ndb.StringProperty(required=True, choices=['youtube'])
  created = ndb.DateTimeProperty(auto_now_add=True)
  uploader = ndb.KeyProperty(kind='User', required=True)
  description = ndb.StringProperty(required=True)
  title = ndb.StringProperty(required=True)
  category = ndb.StringProperty(required=True, choices=Video_Category)
  subcategory = ndb.StringProperty(required=True)

  # video_list_belonged = ndb.KeyProperty(kind='PlayList', required=True, indexed=False)
  video_order = ndb.IntegerProperty(required=True)
  danmaku_counter = ndb.IntegerProperty(required=True, default=0)
  comment_counter = ndb.IntegerProperty(required=True, default=0)
  tags = ndb.StringProperty(repeated=True);
  banned_tags = ndb.StringProperty(repeated=True);

  hits = ndb.IntegerProperty(required=True, default=0)
  likes = ndb.IntegerProperty(required=True, default=0)
  favors = ndb.IntegerProperty(required=True, default=0)
  bullets = ndb.IntegerProperty(required=True, default=0)
  be_collected = ndb.IntegerProperty(required=True, default=0)

  def get_basic_info(self):
    basic_info = {
      'title': self.title,
      'url': '/video/'+ str(self.key.id()),
      'thumbnail_url': 'http://img.youtube.com/vi/' + self.vid + '/default.jpg',
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'category': self.category,
      'subcategory': self.subcategory,
      'hits': self.hits,
      'danmaku_counter': self.danmaku_counter, 
      'likes': self.likes,
      'favors': self.favors
    }
    return basic_info

  @classmethod
  def get_by_id(cls, id):
    return super(Video, cls).get_by_id(id, parent=ndb.Key('EntityType', 'Video'))

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

  @classmethod
  @ndb.transactional(retries=2)
  def getID(cls):
    try:
      cls.id_counter += 1
    except AttributeError:
      latest_video = cls.query(ancestor=ndb.Key('EntityType', 'Video')).order(-cls.key).get()
      if latest_video is not None:
        max_id = int(latest_video.key.id()[2:])
        cls.id_counter = max_id + 1
      else:
        cls.id_counter = 1
      # cls.id_counter = 1
    return cls.id_counter

  @classmethod
  def Create(cls, raw_url, user, description, title, category, subcategory):
    res = cls.parse_url(raw_url)
    if res.get('error'):
      # return 'URL Error.'
      raise Exception(res['error'])
    else:
      if (category in Video_Category) and (subcategory in Video_SubCategory[category]):
        try:
          id = 'dt'+str(cls.getID())
          logging.info(id)
          video = Video(
            # id = 'dt'+str(cls.getID()),
            key = ndb.Key('Video', id, parent=ndb.Key('EntityType', 'Video')),
            url = raw_url,
            vid = res['vid'],
            source = res['source'],
            uploader = user.key,
            description = description,
            title = title, 
            category = category,
            subcategory = subcategory,
            video_order = 1,
          )
          video.put()
        except:
          raise Exception('Failed to submit video')
        else:
          return video
      else:
        # return 'Category mismatch.'
        raise Exception('Category mismatch')

class Danmaku(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  position = db.StringProperty(required=True, default='RightToLeft', choices=['RightToLeft', 'Top', 'Bottom'])
  color = db.IntegerProperty(required=True, default=255*256*256+255*256+255)
  # creator = db.ReferenceProperty(User)
  # order = ndb.IntegerProperty(required=True)
  protected = ndb.BooleanProperty(required=True)
  creator = ndb.KeyProperty(kind='User', required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

class Comment(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  creator = ndb.KeyProperty(kind='User', required=True)
  content = ndb.TextProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  floor = ndb.IntegerProperty(required=True)
  inner_comment_counter = ndb.IntegerProperty(required=True, indexed=False)

class CommentOfComment(ndb.Model):
  comment_belonged = ndb.KeyProperty(kind='Comment', required=True)
  creator = ndb.KeyProperty(kind='User', required=True)
  content = ndb.TextProperty(required=True, indexed=False)
  floor = ndb.IntegerProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

class AtUser(ndb.Model):
  sender = ndb.KeyProperty(kind='User', required=True)
  receiver = ndb.KeyProperty(kind='User', required=True)
  comment = ndb.KeyProperty(kind='Comment', indexed=False)
  inner_comment = ndb.KeyProperty(kind='CommentOfComment', indexed=False)
  danmaku = ndb.KeyProperty(kind='Danmaku', indexed=False)
