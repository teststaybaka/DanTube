from google.appengine.ext import ndb
from google.appengine.api.datastore_errors import TransactionFailedError
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import search
from webapp2_extras.appengine.auth.models import Unique
from webapp2_extras import security
from google.appengine.ext import blobstore
from google.appengine.ext import deferred
from google.appengine.api import images
import cloudstorage as gcs
from datetime import datetime
import urllib2
import urlparse
import re
import logging
import math
import json

def time_to_seconds(time):
  return int((time - datetime(1970, 1, 1)).total_seconds())

def number_upper_limit_99(num):
  if num > 99:
    return '99+'
  elif num == 0:
    return ''
  else:
    return str(num)

EMAIL_REGEX = re.compile(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
ILLEGAL_REGEX = re.compile(r".*[&@.,?!:/\\\"'<>=].*")
ILLEGAL_LETTER = re.compile(r"[&@.,?!:/\\\"'<>=]")
VIDEO_ID_REGEX = re.compile(r"dt\d+")

class NonNegativeIntegerProperty(ndb.IntegerProperty):
  def _validate(self, value):
    # logging.info('validating')
    if not isinstance(value, int):
      raise TypeError('expected an integer, got %s' % repr(value))
    return value if value > 0 else 0

  # def _to_base_type(self, value):
  #   logging.info('to base')
  #   return value

  # def _from_base_type(self, value):
  #   logging.info('from base')
  #   return value

class UserToken(ndb.Model):
  subject = ndb.StringProperty(required=True, indexed=False)
  token = ndb.StringProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

  @classmethod
  def get_key(cls, user_id, subject, token):
    return ndb.Key(cls, '%s.%s.%s' % (str(user_id), subject, token), parent=User.get_key(user_id))

  @classmethod
  def create(cls, user_id, subject):
    token = security.generate_random_string(entropy=128)
    key = cls.get_key(user_id, subject, token)
    entity = cls(key=key, subject=subject, token=token)
    entity.put()
    return entity

  @classmethod
  def get(cls, user_id, subject, token):
    return cls.get_key(user_id, subject, token).get()

  @classmethod
  def delet_tokens(cls, user_key, subject):
    all_tokens = cls.query(ancestor=user_key).fetch()
    res_tokens = []
    for token in all_tokens:
      if token.subject == subject:
        token.key.delete()

class UserDetail(ndb.Model):
  nickname = ndb.StringProperty(required=True, indexed=False)
  intro = ndb.TextProperty(required=True, default='',indexed=False)
  spacename = ndb.StringProperty(indexed=False)
  recent_visitors = ndb.KeyProperty(kind='User', repeated=True, indexed=False)
  recent_visitor_names = ndb.StringProperty(repeated=True, indexed=False)
  bullets = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  playlists_created = NonNegativeIntegerProperty(required=True, default=0, indexed=False)

  videos_submitted = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  videos_watched = ndb.IntegerProperty(required=True, default=0, indexed=False)
  space_visited = ndb.IntegerProperty(required=True, default=0, indexed=False)

  def get_detail_info(self):
    detail_info = {
      'intro': self.intro,
      'spacename': self.spacename,
      'playlists_created': self.playlists_created,

      'videos_submitted': self.videos_submitted,
      'videos_watched': self.videos_watched,
      'space_visited': self.space_visited,
      'bullets': self.bullets,
    }
    return detail_info

  def get_visitor_info(self):
    visitor_info = {'visitors': []}
    for i in reversed(xrange(0, len(self.recent_visitors))):
      info = User.get_snapshot_info(self.recent_visitor_names[i], self.recent_visitors[i])
      visitor_info['visitors'].append(info)
    return visitor_info

  @classmethod
  def Create(cls, user_key):
    user_detail = cls(key=cls.get_key(user_key))
    user_detail.put()

class User(ndb.Model):
  AvatarPrefix = 'https://storage.googleapis.com/dantube-avatar/'
  # AvatarPrefix = 'http://localhost:8080/_ah/gcs/dantube-avatar/'
  CSSPrefix = 'https://storage.googleapis.com/dantube-css/'
  Pepper = 'McbIlx'

  auth_ids = ndb.StringProperty(repeated=True)
  email = ndb.StringProperty(indexed=False)
  password = ndb.StringProperty(required=True, indexed=False)
  nickname = ndb.StringProperty(required=True)
  level = ndb.IntegerProperty(required=True, default=1, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  updated = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  new_messages = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  new_mentions = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  new_notifications = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  new_subscriptions = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  check_new_subscription = ndb.BooleanProperty(required=True, default=False, indexed=False)
  last_subscription_check = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  subscribers_counter = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  subscription_counter = NonNegativeIntegerProperty(required=True, default=0, indexed=False)

  @classmethod
  def get_key(cls, user_id):
    return ndb.Key(cls, user_id)

  @classmethod
  def get_detail_key(cls, user_key):
    return ndb.Key('UserDetail', 'ud'+str(user_key.id()))

  @classmethod
  def get_space_url(cls, user_id):
    return '/user/' + str(user_id)

  @classmethod
  def get_avatar_url(cls, user_key):
    return cls.AvatarPrefix + 'standard-' + str(user_key.id())

  @classmethod
  def get_avatar_url_small(cls, user_key):
    return cls.AvatarPrefix + 'small-' + str(user_key.id())

  @classmethod
  def get_user_css_file(cls, user_key):
    return cls.CSSPrefix + str(user_key.id())

  @classmethod
  def get_snapshot_info(cls, nickname, user_key):
    if user_key:
      snapshot_info = {
        'id': user_key.id(),
        'space_url': cls.get_space_url(user_key.id()),
        'nickname': nickname,
        'avatar_url_small': cls.get_avatar_url_small(user_key),
      }
    else:
      snapshot_info = {
        'id': 0,
        'space_url': None,
        'nickname': None,
        'avatar_url_small': None,
      }
    return snapshot_info

  def get_public_info(self):
    public_info = {
      'id': self.key.id(),
      'level': self.level,
      'nickname': self.nickname,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'space_url': self.get_space_url(self.key.id()),
      'subscribers_counter': self.subscribers_counter,
      'subscription_counter': self.subscription_counter,
      'avatar_url': self.get_avatar_url(self.key),
      'avatar_url_small': self.get_avatar_url_small(self.key),
    }
    return public_info

  def get_private_info(self):
    if self.check_new_subscription:
      self.check_new_subscription = False
      subscriptions = Subscription.query(models.Subscription.user==self.key).fetch(projection=['uper'])
      uper_keys = [subscription.uper for subscription in subscriptions]
      if uper_keys:
        self.new_subscriptions = Video.query(ndb.AND(Video.uploader.IN(uper_keys), Video.created > self.last_subscription_check)).count()
      else:
        self.new_subscriptions = 0
      self.put()

    private_info = {
      'email': self.email,
      'new_mentions_99': number_upper_limit_99(self.new_mentions),
      'new_notifications_99': number_upper_limit_99(self.new_notifications),
      'new_messages_99': number_upper_limit_99(self.new_messages),
      'new_subscriptions_99': number_upper_limit_99(self.new_subscriptions),
    }
    info = self.get_public_info()
    info.update(private_info)
    return info

  def delete_index(self):
    index = search.Index(name='upers_by_created')
    index.delete(self.key.urlsafe())

  def create_index(self, intro):
    index = search.Index(name='upers_by_created')
    searchable = " ".join([self.nickname, intro[:300]]);
    doc = search.Document(
      doc_id = self.key.urlsafe(), 
      fields = [
        search.TextField(name='content', value=searchable.lower()),
      ],
      rank = time_to_seconds(self.created),
    )
    add_result = index.put(doc)

  @classmethod
  def validate_nickname(cls, nickname):
    if not nickname:
      logging.info('nickname 1')
      return None
    if ILLEGAL_REGEX.match(nickname):
      logging.info('nickname 2')
      return None
    if nickname == 'null' or nickname == 'None':
      logging.info('nickname 3')
      return None
    if len(nickname) > 50:
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
    if not email:
      logging.info('email 1')
      return None
    if not EMAIL_REGEX.match(email):
      logging.info('email 2')
      return None

    return email

  @classmethod
  def Create(cls, email, raw_password, nickname):
    uniques = ['%s.%s:%s' % (cls.__name__, 'email', email), '%s.%s:%s' % (cls.__name__, 'nickname', nickname)]
    ok, existing = Unique.create_multi(uniques)
    if ok:
      password = security.generate_password_hash(raw_password, method='sha1', length=12, pepper=cls.Pepper)
      user = cls(auth_ids=[email], email=email, nickname=nickname, password=password)
      user.put()
      user.create_index(intro='')
      user_detail = UserDetail(key=cls.get_detail_key(user.key), nickname=nickname)
      user_detail.put()
      return user
    else:
      return None

  @classmethod
  def check_unique(cls, name, value):
    return bool(ndb.Key(Unique, '%s.%s:%s' % (cls.__name__, name, value)).get())

  @classmethod
  def delete_unique(cls, name, value):
    ndb.Key(Unique, '%s.%s:%s' % (cls.__name__, name, value)).delete()

  @classmethod
  def create_unique(cls, name, value):
    return Unique.create('%s.%s:%s' % (cls.__name__, name, value))

  @classmethod
  def create_pwdreset_token(cls, user_id):
    entity = UserToken.create(user_id, 'pwdreset')
    return entity.token

  @classmethod
  def create_signup_token(cls, user_id):
    entity = UserToken.create(user_id, 'signup')
    return entity.token

  @classmethod
  def get_token_key(cls, user_id, token, subject):
    return UserToken.get_key(user_id, subject, token)

  def set_password(self, raw_password):
    self.password = security.generate_password_hash(raw_password, method='sha1', length=12, pepper=self.Pepper)

  def auth_password(self, raw_password):
    return security.check_password_hash(raw_password, self.password, pepper=self.Pepper)

  @classmethod
  def get_user_by_password(cls, auth_id, password):
    user = cls.query(cls.auth_ids==auth_id).get()
    if user and user.auth_password(password):
      return user
    else:
      return None

Video_Category = ['Anime', 'Music', 'Dance', 'Game', 'Entertainment', 'Techs', 'Sports', 'Movie', 'Drama']
Video_SubCategory = {'Anime': ['TV Anime', 'OVA/Movie', 'MAD/AMV/GMV', 'MMD/3D', 'Original/Voice Acting', 'General']
                  , 'Music': ['Music Sharing', 'Cover Version', 'Instrument Playing', 'VOCALOID/UTAU', 'Music Selection', 'Sound Remix']
                  , 'Dance': ['Dance']
                  , 'Game': ['Game Video', 'Walkthrough/Guides', 'Eletronic Sports', 'Mugen']
                  , 'Entertainment': ['Funny Video', 'Animal Planet', 'Tasty Food', 'Entertainment TV Show']
                  , 'Techs': ['Documentary', 'Various Techs', 'Tech Intro', 'Online Courses']
                  , 'Sports': ['Amazing Human', 'Sports Video', 'Tournament']
                  , 'Movie': ['Movie', 'Micro/Short Film', 'Trailer/Highlights']
                  , 'Drama': ['TV Series', 'Tokusatsu', 'Trailer/Highlights']}

URL_NAME_DICT = {
  # Categories
  'Anime': ['anime', {
    # Subcategories of Anime
    'TV Anime': 'series',
    'OVA/Movie': 'movie',
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
    'Sound Remix': 'mix',
  }],
  'Dance': ['dance', {
    # Subcategories of Dance
    'Dance': 'dance',
  }],
  'Game': ['game', {
    # Subcategories of Game
    'Game Video': 'video',
    'Walkthrough/Guides': 'guides',
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
    'Tech Intro': 'intro',
    'Online Courses': 'course',
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
  'Drama': ['drama', {
    # Subcategories of TV Series
    'TV Series': 'series',
    'Tokusatsu': 'tokusatsu',
    'Trailer/Highlights': 'trailer',
  }],
}

MAX_QUERY_RESULT = 1000
STANDARD_PAGE_SIZE = 10
MEDIUM_PAGE_SIZE = 20

class PlaylistDetail(ndb.Model):
  videos = ndb.KeyProperty(kind='Video', repeated=True, indexed=False)

Playlist_Type = ['Primary', 'Custom']
class Playlist(ndb.Model):
  modified = ndb.DateTimeProperty(auto_now_add=True)
  creator = ndb.KeyProperty(kind='User', required=True)
  title = ndb.StringProperty(required=True, indexed=False)
  playlist_type = ndb.StringProperty(required=True, choices=Playlist_Type)
  intro = ndb.TextProperty(required=True, default='', indexed=False)
  first_video = ndb.KeyProperty(kind='Video', indexed=False)
  videos_num = NonNegativeIntegerProperty(required=True, default=0, indexed=False)

  @classmethod
  def get_detail_key(cls, list_key):
    return ndb.Key('PlaylistDetail', 'lv'+str(list_key.id()))

  def get_info(self):
    basic_info = {
      'id': self.key.id(),
      'videos_num': self.videos_num,
      'title': self.title, 
      'type': self.playlist_type,
      'intro': self.intro[:300],
      'thumbnail_url': Video.get_thumbnail_url(self.first_video.id()) if self.first_video else '/static/img/empty_list.png',
      # 'thumbnail_url_hq': self.thumbnail_url_hq if self.thumbnail_url_hq else '/static/img/empty_list.png',
      'modified': self.modified.strftime("%Y-%m-%d %H:%M"),
    }
    if self.playlist_type == 'Primary':
      basic_info['url'] = Video.get_video_url(self.first_video.id()) if self.first_video else ''
    else:
      basic_info['url'] = Video.get_video_url(self.first_video.id(), self.key.id()) if self.first_video else ''
    return basic_info

  def delete_index(self):
    index = search.Index(name='playlists_by_modified')
    index.delete(self.key.urlsafe())

  def create_index(self):
    index = search.Index(name='playlists_by_modified')
    searchable = " ".join([self.title, self.intro[:300]]);
    doc = search.Document(
      doc_id = self.key.urlsafe(),
      fields = [
        search.TextField(name='content', value=searchable.lower()),
        search.AtomField(name='uper', value=str(self.creator.id())),
        search.AtomField(name='type', value=self.playlist_type),
        search.NumberField(name='videos', value=self.videos_num),
      ],
      rank = time_to_seconds(self.modified),
    )
    add_result = index.put(doc)

class CategoryCounter(ndb.Model):
  counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

class VideoIDFactory(ndb.Model):
  id_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

class VideoClipList(ndb.Model):
  clips = ndb.KeyProperty(kind='VideoClip', repeated=True, indexed=False)
  titles = ndb.StringProperty(repeated=True, indexed=False)

  @classmethod
  def get_key(cls, video_id):
    return ndb.Key(cls, 'cl'+video_id)

Video_Type = ['Original', 'Republish']
class Video(ndb.Model):
  ThumbnailPrefix = 'https://storage.googleapis.com/dantube-thumbnail/'

  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now_add=True)
  uploader = ndb.KeyProperty(kind='User')
  uploader_name = ndb.StringProperty(required=True, indexed=False)

  title = ndb.StringProperty(required=True, indexed=False)
  intro = ndb.TextProperty(required=True, indexed=False)
  category = ndb.StringProperty(required=True, choices=Video_Category)
  subcategory = ndb.StringProperty(required=True)
  video_type = ndb.StringProperty(required=True, choices=Video_Type, indexed=False)
  duration = ndb.IntegerProperty(required=True, default=0, indexed=False)
  playlist_belonged = ndb.KeyProperty(kind='Playlist', indexed=False)
  tags = ndb.StringProperty(repeated=True, indexed=False)
  allow_tag_add = ndb.BooleanProperty(required=True, default=True, indexed=False)

  hot_score = ndb.FloatProperty(default=0)
  hits = ndb.IntegerProperty(required=True, default=0, indexed=False)
  likes = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  bullets = ndb.IntegerProperty(required=True, default=0, indexed=False)
  shares = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  comment_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

  deleted = ndb.BooleanProperty(required=True, default=False, indexed=False)

  video_counter = {}

  @classmethod
  def get_video_url(cls, video_id, playlist_id=None):
    if playlist_id:
      return '/video/'+video_id+'?list='+str(playlist_id)
    else:
      return '/video/'+video_id

  @classmethod
  def get_thumbnail_url_large(cls, video_id):
    return cls.ThumbnailPrefix+'large-'+video_id

  @classmethod
  def get_thumbnail_url(cls, video_id):
    return cls.ThumbnailPrefix+'standard-'+video_id

  def get_basic_info(self, playlist_id=None):
    basic_info = {
      'id': self.key.id(),
      'url': Video.get_video_url(self.key.id(), playlist_id),
      'title': self.title,
      'intro': self.intro[:300],
      'category': self.category,
      'subcategory': self.subcategory,
      'duration': self.duration,
      'type': self.video_type,
      'hits': self.hits,
      'comment_counter': self.comment_counter,
      'bullets': self.bullets,
      'shares': self.shares,
      'likes': self.likes,
      'created': self.created.strftime("%Y-%m-%d %H:%M") if not self.deleted else '',
      'uploader': User.get_snapshot_info(self.uploader_name, self.uploader),
      'thumbnail_url': Video.get_thumbnail_url(self.key.id()),
      'thumbnail_url_hq': Video.get_thumbnail_url_large(self.key.id()),
    }
    return basic_info

  def get_full_info(self):
    full_info = {
      'intro': self.intro,
      'tags': [tag for tag in self.tags],
      'allow_tag_add': self.allow_tag_add,
    }
    info = self.get_basic_info()
    info.update(full_info)
    return info

  @classmethod
  def get_max_id(cls):
    try:
      return cls.video_id_factory.id_counter
    except AttributeError:
      cls.video_id_factory = ndb.Key('VideoIDFactory', 'VideoIDFactory').get()
      if not cls.video_id_factory:
        return 0
      else:
        return cls.video_id_factory.id_counter

  @classmethod
  @ndb.transactional(retries=10)
  def video_count_inc_dec(cls, action, category='', subcategory=''):
    count_key = category + ';' + subcategory
    try:
      if action == 'inc':
        cls.video_counter[count_key].counter += 1
      else: # dec
        cls.video_counter[count_key].counter -= 1
      cls.video_counter[count_key].put()
    except KeyError:
      category_counter = CategoryCounter.query(ancestor=ndb.Key('CategoryCounter', count_key)).get()
      if not category_counter:
        category_counter = CategoryCounter(parent=ndb.Key('CategoryCounter', count_key))

      if action == 'inc':
        category_counter.counter += 1
      else: # dec
        category_counter.counter -= 1
      category_counter.put()
      cls.video_counter[count_key] = category_counter

  @classmethod
  @ndb.transactional(retries=10)
  def getID(cls):
    try:
      cls.video_id_factory.id_counter += 1
      cls.video_id_factory.put()
    except AttributeError:
      cls.video_id_factory = ndb.Key('VideoIDFactory', 'VideoIDFactory').get()
      if not cls.video_id_factory:
        cls.video_id_factory = VideoIDFactory(key=ndb.Key('VideoIDFactory', 'VideoIDFactory'))
      cls.video_id_factory.id_counter += 1
      cls.video_id_factory.put()
    return cls.video_id_factory.id_counter

  def delete_index(self, index_name):
    index = search.Index(name=index_name)
    index.delete(self.key.urlsafe())

  def create_index(self, index_name, rank):
    index = search.Index(name=index_name)
    searchable = ' '.join(self.tags + [self.title, self.intro[:300], self.uploader_name, self.video_type]);
    doc = search.Document(
      doc_id = self.key.urlsafe(),
      fields = [
        search.TextField(name='content', value=searchable.lower()),
        search.AtomField(name='category', value=self.category),
        search.AtomField(name='subcategory', value=self.subcategory),
        search.AtomField(name='uper', value=str(self.uploader.id()))
      ],
      rank = rank
    )
    add_result = index.put(doc)

  @classmethod
  def Create(cls, user, intro, title, category, subcategory, video_type, duration, tags, allow_tag_add):
    try:
      video_id = 'dt'+str(cls.getID())
    except TransactionFailedError, e:
      raise e

    current_time = time_to_seconds(datetime.now())
    video = cls(
      id = video_id,
      uploader = user.key,
      uploader_name = user.nickname,
      intro = intro,
      title = title,
      category = category,
      subcategory = subcategory,
      video_type = video_type,
      duration = duration,
      tags = tags,
      allow_tag_add = allow_tag_add,
      hot_score = current_time/100.0,
    )
    video.put()

    # while True:
    #   try:
    #     cls.video_count_inc_dec('inc', category)
    #     break
    #   except TransactionFailedError:
    #     pass

    # while True:
    #   try:
    #     cls.video_count_inc_dec('inc', category, subcategory)
    #     break
    #   except TransactionFailedError:
    #     pass

    video.create_index('videos_by_created', time_to_seconds(video.created))
    video.create_index('videos_by_hits', video.hits)
    video.create_index('videos_by_likes', video.likes)
    return video

  def Delete(self):
    if self.playlist_belonged:
      playlist, list_detail = ndb.get_multi([self.playlist_belonged, Playlist.get_detail_key(self.playlist_belonged)])
      list_detail.videos.remove(self.key)
      if not list_detail.videos:
        playlist.first_video = None
      elif playlist.first_video != list_detail.videos[0]:
        playlist.first_video = list_detail.videos[0]
      playlist.videos_num = len(list_detail.videos)
      ndb.put_multi([playlist, list_detail])
      self.playlist_belonged = None

    video_clip_list = VideoClipList.get_key(self.key.id()).get()
    for i in xrange(0, len(video_clip_list.clips)):
      VideoClip.Delete(video_clip_list.clips[i])
    video_clip_list.key.delete_async()
    
    # while True:
    #   try:
    #     cls.video_count_inc_dec('dec', self.category)
    #     break;
    #   except Exception, e:
    #     pass

    # while True:
    #   try:
    #     cls.video_count_inc_dec('inc', self.category, self.subcategory)
    #     break
    #   except TransactionFailedError:
    #     pass
    
    self.delete_index('videos_by_created')
    self.delete_index('videos_by_hits')
    self.delete_index('videos_by_likes')
    
    self.deleted = True
    self.title = 'Video deleted'
    self.intro = ''
    self.duration = 0
    self.uploader = None
    self.updated = None
    self.created = None
    self.hot_score = None
    self.put()
    # self.key.delete()

class Comment(ndb.Model):
  creator = ndb.KeyProperty(kind='User', required=True)
  creator_name = ndb.StringProperty(required=True, indexed=False)
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  video_title = ndb.StringProperty(required=True, indexed=False)

  content = ndb.TextProperty(required=True, indexed=False)
  floorth = ndb.IntegerProperty(indexed=False)
  inner_floorth = ndb.IntegerProperty(indexed=False)
  inner_comment_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  share = ndb.BooleanProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)
  deleted = ndb.BooleanProperty(required=True, default=False, indexed=False)

  def get_content(self):
    content_info = {
      'id': self.key.id(),
      'parent_id': self.key.parent().id(),
      'content': self.content if not self.deleted else '[Content deleted]',
      'floorth': self.floorth,
      'inner_floorth': self.inner_floorth,
      'inner_comment_counter': self.inner_comment_counter,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'creator': User.get_snapshot_info(self.creator_name, self.creator),
    }
    content_info['video'] = {
      'url': Video.get_video_url(self.video.id()),
      'title': self.video_title,
    }
    return content_info

  def Delete():
    self.deleted = True
    self.content = ''
    self.put()

Danmaku_Positions = ['Scroll', 'Top', 'Bottom']
class Danmaku(ndb.Model):
  index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  position = ndb.StringProperty(required=True, default='Scroll', choices=Danmaku_Positions, indexed=False)
  color = ndb.IntegerProperty(required=True, default=255*256*256+255*256+255, indexed=False)
  size = ndb.IntegerProperty(required=True, default=16, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(required=True, indexed=False)

  def format(self):
    return {
              'content': self.content,
              'timestamp': self.timestamp,
              'created': self.created.strftime("%m-%d %H:%M"),
              'created_year': self.created.strftime("%Y-%m-%d %H:%M"),
              'created_seconds': time_to_seconds(self.created),
              'creator': self.creator.id(),
              'type': self.position,
              'size': self.size,
              'color': self.color,
              'index': self.index,
            }

class AdvancedDanmaku(ndb.Model):
  index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  birth_x = ndb.FloatProperty(required=True, indexed=False)
  birth_y = ndb.FloatProperty(required=True, indexed=False)
  death_x = ndb.FloatProperty(required=True, indexed=False)
  death_y = ndb.FloatProperty(required=True, indexed=False)
  speed_x = ndb.FloatProperty(required=True, indexed=False)
  speed_y = ndb.FloatProperty(required=True, indexed=False)
  longevity = ndb.FloatProperty(required=True, indexed=False)
  css = ndb.TextProperty(required=True, indexed=False)
  as_percent = ndb.BooleanProperty(required=True, indexed=False)
  relative = ndb.BooleanProperty(required=True, indexed=False)
  approved = ndb.BooleanProperty(required=True, default=False, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(required=True, indexed=False)

  def format(self):
    return {
              'content': self.content,
              'timestamp': self.timestamp,
              'created': self.created.strftime("%m-%d %H:%M"),
              'created_year': self.created.strftime("%Y-%m-%d %H:%M"),
              'created_seconds': time_to_seconds(self.created),
              'creator': self.creator.id(),
              'birth_x': self.birth_x,
              'birth_y': self.birth_y,
              'death_x': self.death_x,
              'death_y': self.death_y,
              'speed_x': self.speed_x,
              'speed_y': self.speed_y,
              'longevity': self.longevity,
              'css': self.css,
              'as_percent': self.as_percent,
              'relative': self.relative,
              'type': 'Advanced',
              'index': self.index,
              'approved': self.approved,
            }

class SubtitlesDanmaku(ndb.Model):
  index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  name = ndb.StringProperty(required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  approved = ndb.BooleanProperty(required=True, default=False, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(required=True, indexed=False)

  def format(self):
    return {
              'name': self.name,
              'subtitles': self.content,
              'creator': self.creator.id(),
              'created': self.created.strftime("%m-%d %H:%M"),
              'created_year': self.created.strftime("%Y-%m-%d %H:%M"),
              'created_seconds': time_to_seconds(self.created),
              'approved': self.approved,
            }

class CodeDanmaku(ndb.Model):
  index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  approved = ndb.BooleanProperty(required=True, default=False, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(required=True, indexed=False)

  def format(self):
    return {
              'content': self.content,
              'timestamp': self.timestamp,
              'created': self.created.strftime("%m-%d %H:%M"),
              'created_year': self.created.strftime("%Y-%m-%d %H:%M"),
              'created_seconds': time_to_seconds(self.created),
              'creator': self.creator.id(),
              'type': 'Code',
              'index': self.index,
              'approved': self.approved,
            }

class VideoClip(ndb.Model):
  DanmakuPrefix = 'https://storage.googleapis.com/danmaku/'
  # DanmakuPrefix = 'http://localhost:8080/_ah/gcs/danmaku/'

  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  uploader = ndb.KeyProperty(kind='User', required=True, indexed=False)
  title = ndb.StringProperty(required=True, indexed=False)
  index = ndb.IntegerProperty(required=True, indexed=False)
  subintro = ndb.TextProperty(default='', required=True, indexed=False)
  raw_url = ndb.StringProperty(indexed=False)
  vid = ndb.StringProperty(required=True, indexed=False)
  duration = ndb.IntegerProperty(required=True, default=0, indexed=False)
  source = ndb.StringProperty(required=True, choices=['YouTube'], indexed=False)
  peak = ndb.IntegerProperty(required=True, default=0, indexed=False)

  danmaku_num = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  danmaku_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  danmaku_buffer = ndb.LocalStructuredProperty(Danmaku, repeated=True, indexed=False)
  advanced_danmaku_num = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  advanced_danmaku_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  advanced_danmaku_buffer = ndb.LocalStructuredProperty(AdvancedDanmaku, repeated=True, indexed=False)
  subtitles_num = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  subtitles_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  code_danmaku_num = NonNegativeIntegerProperty(required=True, default=0, indexed=False)
  code_danmaku_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

  @classmethod
  def parse_url(cls, raw_url, source):
    if not urlparse.urlparse(raw_url).scheme:
      raw_url = "http://" + raw_url
    url_parts = raw_url.split('//')[-1].split('/')
    if source == 'YouTube':
      vid = url_parts[-1].split('=')[-1]
      url = 'http://www.youtube.com/embed/' + vid
    else:
      raise Exception('invalid url')
    return {'url': url, 'vid': vid}

  @classmethod
  def load_cloud_danmaku(cls, clip_key, kind):
    try:
      pool = gcs.open('/danmaku/'+str(clip_key.id())+'/'+kind, 'r')
      danmaku_list = json.loads(pool.read())
      pool.close()
    except gcs.NotFoundError:
      danmaku_list = []
    return danmaku_list

  @classmethod
  def save_cloud_danmaku(cls, clip_key, kind, danmaku_list):
    pool = gcs.open('/danmaku/'+str(clip_key.id())+'/'+kind, 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
    pool.write(json.dumps(danmaku_list))
    pool.close()

  @classmethod
  def Delete(cls, clip_key):
    try:
      gcs.delete('/danmaku/'+str(clip_key.id())+'/danmaku')
    except gcs.NotFoundError:
      pass
    try:
      gcs.delete('/danmaku/'+str(clip_key.id())+'/advanced')
    except gcs.NotFoundError:
      pass
    try:
      gcs.delete('/danmaku/'+str(clip_key.id())+'/subtitles')
    except gcs.NotFoundError:
      pass
    try:
      gcs.delete('/danmaku/'+str(clip_key.id())+'/code')
    except gcs.NotFoundError:
      pass
    clip_key.delete_async()

class Message(ndb.Model):
  sender = ndb.KeyProperty(kind='User', required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  when = ndb.DateTimeProperty(required=True, indexed=False)

class MessageThread(ndb.Model):
  messages = ndb.LocalStructuredProperty(Message, repeated=True, indexed=False)
  subject = ndb.StringProperty(required=True, indexed=False)
  users = ndb.KeyProperty(kind='User', repeated=True)
  users_backup = ndb.KeyProperty(kind='User', repeated=True, indexed=False)
  new_messages = NonNegativeIntegerProperty(required=True, indexed=False)
  updated = ndb.DateTimeProperty(required=True)

  def get_partner_key(self, user_key):
    for user in self.users_backup:
      if user != user_key:
        partner_key = user
        break
    return partner_key

  def is_sender(self, user_key):
    last_message = self.messages[-1]
    return last_message.sender == user_key

class Notification(ndb.Model):
  receiver = ndb.KeyProperty(kind='User', required=True)
  subject = ndb.StringProperty(required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  note_type = ndb.StringProperty(required=True, choices=['info', 'warning'], indexed=False)
  read = ndb.BooleanProperty(required=True, default=False, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

Danmaku_Types = ['danmaku', 'advanced', 'subtitles', 'code']
class DanmakuRecord(ndb.Model):
  creator = ndb.KeyProperty(kind='User', required=True)
  creator_name = ndb.StringProperty(required=True, indexed=False)
  content = ndb.TextProperty(indexed=False)
  danmaku_type = ndb.StringProperty(required=True, choices=Danmaku_Types, indexed=False)
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  clip_index = ndb.IntegerProperty(required=True, indexed=False)
  video_title = ndb.StringProperty(required=True, indexed=False)
  timestamp = ndb.FloatProperty(required=True, default=0, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

  def get_content(self):
    content_info = {
      'danmaku_type': self.danmaku_type,
      'content': self.content,
      'timestamp': self.timestamp,
      'clip_index': self.clip_index,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'creator': User.get_snapshot_info(self.creator_name, self.creator),
    }
    content_info['video'] = {
      'url': Video.get_video_url(self.video.id()),
      'title': self.video_title,
    }
    return content_info

class MentionedRecord(ndb.Model):
  receivers = ndb.KeyProperty(kind='User', repeated=True)
  target = ndb.KeyProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def Create(cls, user_keys, target):
    users = ndb.get_multi(user_keys)
    for i in xrange(0, len(users)):
      users[i].new_mentions += 1

    mentioned_record = MentionedRecord(receivers=user_keys, target=target)
    ndb.put_multi([mentioned_record] + users)

class ViewRecord(ndb.Model):
  user = ndb.KeyProperty(kind='User', required=True)
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  playlist = ndb.KeyProperty(kind='Playlist', indexed=False)
  clip_index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.FloatProperty(required=True, default=0, indexed=False)
  created = ndb.DateTimeProperty(auto_now=True)

  @classmethod
  def has_viewed(cls, user_key, video_key):
    return bool(ndb.Key(cls, video_key.id() + 'v:' + str(user_key.id())).get())

  @classmethod
  def get(cls, user_key, video_key):
    return ndb.Key(cls, video_key.id() + 'v:' + str(user_key.id())).get()

  @classmethod
  def get_or_create(cls, user_key, video_key):
    record = cls(key=ndb.Key(cls, video_key.id() + 'v:' + str(user_key.id())), user=user_key, video=video_key)
    r = record.key.get()
    if not r:
      record.put()
      return record, True
    else:
      return r, False

class LikeRecord(ndb.Model):
  user = ndb.KeyProperty(kind='User', required=True)
  video = ndb.KeyProperty(kind='Video', required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def has_liked(cls, user_key, video_key):
    return bool(ndb.Key(cls, video_key.id() + 'l:' + str(user_key.id())).get())

  @classmethod
  def dislike(cls, user_key, video_key):
    record = ndb.Key(cls, video_key.id() + 'l:' + str(user_key.id())).get()
    if record:
      record.key.delete()
      return True
    else:
      return False

  @classmethod
  def unique_create(cls, user_key, video_key):
    record = cls(key=ndb.Key(cls, video_key.id() + 'l:' + str(user_key.id())), user=user_key, video=video_key)
    return bool(record.put()) if not record.key.get() else False

class Subscription(ndb.Model):
  user = ndb.KeyProperty(kind='User', required=True)
  uper = ndb.KeyProperty(kind='User', required=True)
  score = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def has_subscribed(cls, user_key, uper_key):
    return bool(ndb.Key(cls, str(uper_key.id()) + 's:' + str(user_key.id())).get())

  @classmethod
  def unsubscribe(cls, user_key, uper_key):
    subscription = ndb.Key(cls, str(uper_key.id()) + 's:' + str(user_key.id())).get()    
    if subscription:
      subscription.key.delete()
      return True
    else:
      return False

  @classmethod
  def unique_create(cls, user_key, uper_key):
    subscription = cls(key=ndb.Key(cls, str(uper_key.id()) + 's:' + str(user_key.id())), user=user_key, uper=uper_key)
    return bool(subscription.put()) if not subscription.key.get() else False

Feedback_Category = ['Bug', 'Suggestion', 'Report', 'Others']
class Feedback(ndb.Model):
  sender = ndb.KeyProperty(kind='User', required=True, indexed=False)
  category = ndb.StringProperty(required=True, choices=Feedback_Category)
  subject = ndb.StringProperty(required=True, indexed=False)
  description = ndb.TextProperty(required=True, indexed=False)
  processed = ndb.BooleanProperty(required=True, default=False, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

Video_Issues = ['Graphic sexual activity', 'Nudity', 'Animal abuse', 'Promotes hatred', 'Promotes terrorism', 'Drug abuse', 'Self injury', 'Child abuse', 'Misleading thumbnail', 'Misleading text', 'Scams/fraud', 'Infringe copyrights', 'Suspicious script', 'Others']
class ReportVideo(ndb.Model):
  video_clip = ndb.KeyProperty(kind='VideoClip', required=True, indexed=False)
  issue = ndb.StringProperty(required=True, choices=Video_Issues, indexed=False)
  description = ndb.TextProperty(indexed=False)
  processed = ndb.BooleanProperty(required=True, default=False, indexed=False)
  reporter = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

Comment_Issues = ['Spam', 'Sexually explicity material', 'Hate speech', 'Harassment', 'Copyrighted material', 'Others']
class ReportComment(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  issue = ndb.StringProperty(required=True, choices=Comment_Issues, indexed=False)
  description = ndb.TextProperty(indexed=False)
  processed = ndb.BooleanProperty(required=True, default=False, indexed=False)
  reporter = ndb.KeyProperty(kind='User', required=True, indexed=False)
  comment = ndb.KeyProperty(kind='Comment', required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  user = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

Danmaku_Issues = ['Blocking screen', 'Misleading information', 'Suspicious code danmaku'] + Comment_Issues
class ReportDanmaku(ndb.Model):
  video_clip = ndb.KeyProperty(kind='VideoClip', required=True, indexed=False)
  issue = ndb.StringProperty(required=True, choices=Danmaku_Issues, indexed=False)
  description = ndb.TextProperty(indexed=False)
  processed = ndb.BooleanProperty(required=True, default=False, indexed=False)
  reporter = ndb.KeyProperty(kind='User', required=True, indexed=False)
  danmaku_index = ndb.IntegerProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  user = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
