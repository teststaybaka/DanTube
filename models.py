from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.api import search
import webapp2_extras.appengine.auth.models
from webapp2_extras import security
from google.appengine.ext import blobstore
from google.appengine.api import images
from datetime import datetime
import urllib2
import urlparse
import time
import re
import logging
import math

def time_to_seconds(time):
  return int((time - datetime(1970, 1, 1)).total_seconds())

def number_upper_limit_99(num):
  if num > 99:
    return '99+'
  elif num == 0:
    return ''
  else:
    return str(num)

EMIAL_REGEX = re.compile(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
ILLEGAL_REGEX = re.compile(r".*[&@.,?!:/\\\"'<>].*")
ILLEGAL_LETTER = re.compile(r"[&@.,?!:/\\\"'<>]")

class BlobCollection(ndb.Model):
  blob = ndb.BlobKeyProperty(required=True, indexed=False)

  def Delete(self):
    images.delete_serving_url(self.blob)
    blobstore.BlobInfo(self.blob).delete_async()

class UserSnapshot(ndb.Model):
  nickname = ndb.StringProperty(required=True, indexed=False)
  default_avatar = ndb.IntegerProperty(required=True, indexed=False)
  avatar = ndb.BlobKeyProperty(required=True, indexed=False)

  def get_snapshot_info(self, user_key):
    snapshot_info = {
      'id': user_key.id(),
      'space_url': cls.get_space_url(user_key.id()),
      'nickname': nickname,
    }
    snapshot_info['avatar_url'], snapshot_info['avatar_url_small'] = User.get_avatar_url(default_avatar, avatar)

class UserDetail(ndb.Model):
  intro = ndb.TextProperty(indexed=False)
  spacename = ndb.StringProperty(indexed=False)
  css_file = ndb.BlobKeyProperty(indexed=False)
  recent_visitors = ndb.KeyProperty(kind='User', repeated=True, indexed=False)
  visitor_snapshopts = ndb.LocalStructuredProperty(UserSnapshot, repeated=True, indexed=False)
  bullets = ndb.IntegerProperty(required=True, default=0, indexed=False)

  videos_submitted = ndb.IntegerProperty(required=True, default=0, indexed=False)
  videos_watched = ndb.IntegerProperty(required=True, default=0, indexed=False)
  space_visited = ndb.IntegerProperty(required=True, default=0, indexed=False)

  def get_detail_info(self):
    detail_info = {
      'intro': self.intro,
      'spacename': self.spacename,
      'bullets': self.bullets,
      'videos_submitted': self.videos_submitted,
      'videos_watched': self.videos_watched,
      'space_visited': self.space_visited,
    }
    if self.css_file:
      public_info['space_css'] = str(self.css_file)
    else:
      public_info['space_css'] = ''

    return detail_info

  def get_visitor_info(self):
    visitor_info = {'visitors': []}
    for i in reversed(xrange(0, len(self.recent_visitors))):
      visitor_key = self.recent_visitors[i]
      visitor = self.visitor_snapshopts[i]
      info = visitor.get_snapshot_info(visitor_key)
      visitor_info['visitors'].append(info)
    return visitor_info

  @classmethod
  def Create(cls, user_key):
    user_detail = cls(id='ud'+str(user_key.id()))
    user_detail.put_async()

  @classmethod
  def get_key(cls, user_key):
    return ndb.Key(cls, 'ud'+str(user_key.id()))

class User(webapp2_extras.appengine.auth.models.User):
  level = ndb.IntegerProperty(required=True, default=1, indexed=False)
  nickname = ndb.StringProperty(required=True)
  avatar = ndb.BlobKeyProperty(indexed=False)
  default_avatar = ndb.IntegerProperty(default=1, choices=[1,2,3,4,5,6], indexed=False)

  new_messages = ndb.IntegerProperty(required=True, default=0, indexed=False)
  new_mentions = ndb.IntegerProperty(required=True, default=0, indexed=False)
  new_notifications = ndb.IntegerProperty(required=True, default=0, indexed=False)
  new_subscriptions = ndb.IntegerProperty(required=True, default=0, indexed=False)
  subscribers_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

  @classmethod
  def get_key(cls, user_id):
    return ndb.Key(cls, user_id)

  @classmethod
  def get_space_url(cls, user_id):
    return '/user/' + str(user_id)

  @classmethod
  def get_avatar_url(cls, default_avatar, avatar):
    if self.avatar:
      url = images.get_serving_url(self.avatar)
      url_small = images.get_serving_url(self.avatar, size=64)
    else:
      url = '/static/emoticons_img/default_avatar' + str(self.default_avatar) + '.png'
      url_small = public_info['avatar_url']
    return url, url_small

  def get_public_info(self):
    public_info = {
      'id': self.key.id(),
      'level': self.level,
      'nickname': self.nickname,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'space_url': User.get_space_url(self.key.id()),
      'subscribers_counter': self.subscribers_counter,
    }
    public_info['avatar_url'], public_info['avatar_url_small'] = User.get_avatar_url(self.default_avatar, self.avatar)
    return public_info

  def get_private_info(self):
    private_info = {
      'email': self.email,
      'new_mentions_99': number_upper_limit_99(self.new_mentions),
      'new_notifications_99': number_upper_limit_99(self.new_notifications),
      'new_messages_99': number_upper_limit_99(self.new_messages),
      'new_subscriptions': number_upper_limit_99(self.new_subscriptions),
    }
    info = self.get_public_info()
    info.update(private_info)
    return info

  def create_snapshot(self):
    return UserSnapshot(nickname=self.nickname, default_avatar=self.default_avatar, avatar=self.avatar)

  def delete_index(self):
    index = search.Index(name='upers_by_created')
    index.delete(self.key.urlsafe())

  def create_index(self, intro):
    index = search.Index(name='upers_by_created')
    searchable = " ".join([self.nickname, intro[:200]]);
    doc = search.Document(
      doc_id = self.key.urlsafe(), 
      fields = [
        search.TextField(name='content', value=searchable.lower()),
      ],
      rank = time_to_seconds(self.created),
    )
    try:
      add_result = index.put(doc)
    except search.Error:
      logging.info('failed to create upers_by_created index for user %s' % (self.key.id()))

  def set_password(self, raw_password):
    self.password = security.generate_password_hash(raw_password, length=32, pepper='xxx-dantube-pepper')

  @classmethod
  def validate_nickname(cls, nickname):
    if not nickname:
      logging.info('nickname 1')
      return None
    if ILLEGAL_REGEX.match(nickname):
      logging.info('nickname 2')
      return None
    if len(nickname) > 50:
      logging.info('nickname 3')
      return None
    res = cls.query(cls.nickname==nickname).get()
    if res:
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
    if not EMIAL_REGEX.match(email):
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
  def get_token_key(cls, user_id, token, subject='auth'):
    """Returns a token key based on a user ID and token.
 
    :param user_id:
        The user_id of the requesting user.
    :param token:
        The token string to be verified.
    :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
    """
    return cls.token_model.get_key(user_id, subject, token)

Video_Category = ['Anime', 'Music', 'Dance', 'Game', 'Entertainment', 'Techs', 'Sports', 'Movie', 'TV Series']
Video_SubCategory = {'Anime': ['Continuing Anime', 'Finished Anime', 'MAD/AMV/GMV', 'MMD/3D', 'Original/Voice Acting', 'General']
                  , 'Music': ['Music Sharing', 'Cover Version', 'Instrument Playing', 'VOCALOID/UTAU', 'Music Selection', 'Sound Remix']
                  , 'Dance': ['Dance']
                  , 'Game': ['Game Video', 'Game Guides/Commentary', 'Eletronic Sports', 'Mugen']
                  , 'Entertainment': ['Funny Video', 'Animal Planet', 'Tasty Food', 'Entertainment TV Show']
                  , 'Techs': ['Documentary', 'Various Techs', 'Tech Intro', 'Online Courses']
                  , 'Sports': ['Amazing Human', 'Sports Video', 'Tournament']
                  , 'Movie': ['Movie', 'Micro/Short Film', 'Trailer/Highlights']
                  , 'TV Series': ['Continuing Series', 'Finished Series', 'Tokusatsu', 'Trailer/Highlights']}

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
    'Sound Remix': 'mix',
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
  'TV Series': ['series', {
    # Subcategories of TV Series
    'Continuing Series': 'continuing',
    'Finished Series': 'finished',
    'Tokusatsu': 'tokusatsu',
    'Trailer/Highlights': 'trailer',
  }],
}

MAX_QUERY_RESULT = 1000
STANDARD_PAGE_SIZE = 10
MEDIUM_PAGE_SIZE = 20

class PlayListDetail(ndb.Model):
  videos = ndb.KeyProperty(kind='Video', repeated=True)

class PlayList(ndb.Model):
  modified = ndb.DateTimeProperty(auto_now_add=True)
  creator = ndb.KeyProperty(kind='User', required=True)
  title = ndb.StringProperty(required=True, indexed=False)
  intro = ndb.TextProperty(required=True, default='', indexed=False)
  url = ndb.StringProperty(indexed=False)
  first_video = ndb.KeyProperty(kind='Video', indexed=False)
  thumbnail_url = ndb.StringProperty(indexed=False)
  thumbnail_url_hq = ndb.StringProperty(indexed=False)
  videos_num = ndb.IntegerProperty(required=True, default=0, indexed=False)

  @classmethod
  def get_detail_key(cls, list_key):
    return ndb.Key('PlayListDetail', 'lv'+str(list_key.id()))

  def get_info(self):
    basic_info = {
      'videos_num': self.videos_num,
      'title': self.title, 
      'intro': self.intro,
      'id': self.key.id(),
      'url': Video.get_video_url(self.first_video.id()) if self.first_video else None,
      'thumbnail_url': self.thumbnail_url if self.thumbnail_url else '/static/img/empty_list.png',
      'thumbnail_url_hq': self.thumbnail_url_hq if self.thumbnail_url_hq else '/static/img/empty_list.png',
    }
    return basic_info

  def set_first_video(self, video):
    self.first_video = video.key
    self.thumbnail_url, self.thumbnail_url_hq = video.get_thumbnail_url()

  def reset_first_video(self):
    self.first_video = None
    self.thumbnail_url = None
    self.thumbnail_url_hq = None

  def delete_index(self):
    index = search.Index(name='playlists_by_modified')
    index.delete(self.key.urlsafe())

  def create_index(self):
    index = search.Index(name='playlists_by_modified')
    searchable = " ".join([self.title, self.intro[:200]]);
    doc = search.Document(
      doc_id = self.key.urlsafe(), 
      fields = [
        search.TextField(name='content', value=searchable.lower()),
        search.AtomField(name='uper', value=self.creator.id()),
      ],
      rank = time_to_seconds(self.modified),
    )
    try:
      add_result = index.put(doc)
    except search.Error:
      logging.info('failed to create %s index for playlist %s' % (index_name, self.key.id()))

class VideoClip(ndb.Model):
  index = ndb.IntegerProperty(required=True)
  title = ndb.StringProperty(required=True)
  subintro = ndb.TextProperty(default='', required=True, indexed=False)
  raw_url = ndb.StringProperty(indexed=False)
  vid = ndb.StringProperty(required=True, indexed=False)
  duration = ndb.IntegerProperty(required=True, indexed=False, default=0)
  source = ndb.StringProperty(required=True, choices=['youtube'], indexed=False)

  danmaku_num = ndb.IntegerProperty(required=True, default=0, indexed=False)
  danmaku_pools = ndb.KeyProperty(kind='DanmakuPool', repeated=True, indexed=False)
  advanced_danmaku_num = ndb.IntegerProperty(required=True, default=0, indexed=False)
  advanced_danmaku_pool = ndb.KeyProperty(kind='AdvancedDanmakuPool', indexed=False)
  subtitle_names = ndb.StringProperty(repeated=True, indexed=False)
  subtitle_danmaku_pools = ndb.KeyProperty(kind='SubtitleDanmakuPool', repeated=True, indexed=False)
  code_danmaku_num = ndb.IntegerProperty(required=True, default=0, indexed=False)
  code_danmaku_pool = ndb.KeyProperty(kind='CodeDanmakuPool', indexed=False)
  refresh = ndb.BooleanProperty(required=True, default=True, indexed=False)

  @classmethod
  def parse_url(cls, raw_url):
    if not urlparse.urlparse(raw_url).scheme:
      raw_url = "http://" + raw_url
    url_parts = raw_url.split('//')[-1].split('/')
    source = url_parts[0].split('.')[-2]
    if source == 'youtube':
      vid = url_parts[-1].split('=')[-1]
      url = 'http://www.youtube.com/embed/' + vid
    else:
      url = raw_url
    return {'url': url, 'vid': vid, 'source': source}

  @ndb.transactional(retries=10)
  def get_lastest_danmaku_pool(self):
    if len(self.danmaku_pools) == 0:
      danmaku_pool = DanmakuPool()
      danmaku_pool.put()
      self.danmaku_pools.append(danmaku_pool.key)
      self.put()
    else:
      danmaku_pool = self.danmaku_pools[-1].get()
      if len(danmaku_pool.danmaku_list) >= 1000:
        danmaku_pool = DanmakuPool()
        danmaku_pool.put()
        self.danmaku_pools.append(danmaku_pool.key)
        if len(self.danmaku_pools) > 20:
          self.danmaku_pools.pop(0).delete()
        self.put()
    return danmaku_pool

  @ndb.transactional(retries=10)
  def get_advanced_danmaku_pool(self):
    if not self.advanced_danmaku_pool:
      advanced_danmaku_pool = AdvancedDanmakuPool()
      advanced_danmaku_pool.put()
      self.advanced_danmaku_pool = advanced_danmaku_pool
      self.put()
    return self.advanced_danmaku_pool

  @ndb.transactional(retries=10)
  def get_code_danmaku_pool(self):
    if not self.code_danmaku_pool:
      code_danmaku_pool = CodeDanmakuPool()
      code_danmaku_pool.put()
      self.code_danmaku_pool = code_danmaku_pool
      self.put()
    return self.advanced_danmaku_pool

  @ndb.transactional(retries=10)
  def append_new_subtitles(self, name, pool_key):
    self.subtitle_names.append(name)
    self.subtitle_danmaku_pools.append(pool_key)
    self.put()

  def Delete(self):
    for pool in danmaku_pools:
      pool.delete_async()
    if advanced_danmaku_pool:
      advanced_danmaku_pool.delete_async()
    for pool in subtitle_danmaku_pools:
      pool.delete_async()
    if code_danmaku_pool:
      code_danmaku_pool.delete_async()
    self.key.delete_async()

class CategoryCounter(ndb.Model):
  counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

class VideoIDFactory(ndb.Model):
  id_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

class Video(ndb.Model):
  created = ndb.DateTimeProperty(auto_now_add=True)
  updated = ndb.DateTimeProperty(auto_now_add=True)
  uploader = ndb.KeyProperty(kind='User', required=True)
  uploader_snapshot = ndb.LocalStructuredProperty(UserSnapshot, required=True, indexed=False)

  title = ndb.StringProperty(required=True, indexed=False)
  intro = ndb.TextProperty(indexed=False)
  category = ndb.StringProperty(required=True)
  video_type = ndb.StringProperty(required=True, choices=['original', 'republish'], indexed=False)
  duration = ndb.IntegerProperty(required=True, default=0, indexed=False)
  default_thumbnail = ndb.StringProperty(indexed=False)
  thumbnail = ndb.BlobKeyProperty(indexed=False)
  playlist_belonged = ndb.KeyProperty(kind='PlayList', indexed=False)
  tags = ndb.StringProperty(repeated=True, indexed=False)
  allow_tag_add = ndb.BooleanProperty(required=True, default=True, indexed=False)

  hot_score = ndb.IntegerProperty(required=True, default=0)
  hot_score_updated = ndb.IntegerProperty(required=True, default=0, indexed=False)
  hits = ndb.IntegerProperty(required=True, default=0, indexed=False)
  likes = ndb.IntegerProperty(required=True, default=0, indexed=False)
  bullets = ndb.IntegerProperty(required=True, default=0, indexed=False)
  shares = ndb.IntegerProperty(required=True, default=0, indexed=False)
  comment_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

  @classmethod
  def get_deleted_video_info(cls):
    info = {
      'id': 'None',
      'url': 'None',
      'title': 'Video deleted',
      'intro': 'Video deleted',
      'thumbnail_url': '/static/img/video_deleted.png',
      'thumbnail_url_hq': '/static/img/video_deleted.png',
      'category': 'None',
      'subcategory': 'None',
      'duration': 0,
      'type': 'None',
    }
    return info

  @classmethod
  def get_projection(cls):
    return ['title', 'intro', 'category', 'subcategory', 'duration', 'video_type', 'thumbnail', 'default_thumbnail', 'playlist_belonged', 'hits', 'likes', 'shares', 'comment_counter', 'created']

  @classmethod
  def get_video_url(cls, video_id):
    return '/video/'+video_id

  def get_thumbnail_url(self):
    if not self.thumbnail:
      res = self.default_thumbnail.split(':')
      thumbnail_url = 'http://img.youtube.com/vi/' + res[0] + '/mqdefault.jpg'
      thumbnail_url_hq = 'http://img.youtube.com/vi/' + res[0] + '/' + res[1] + 'default.jpg'
    else:
      thumbnail_url = images.get_serving_url(self.thumbnail, size=240)
      thumbnail_url_hq = images.get_serving_url(self.thumbnail)

    return thumbnail_url, thumbnail_url_hq

  def get_basic_info(self):
    category, subcategory = self.category.split('-')
    basic_info = {
      'id': self.key.id(),
      'url': Video.get_video_url(self.key.id()),
      'title': self.title,
      'intro': self.intro,
      'category': self.category,
      'subcategory': subcategory,
      'duration': duration,
      'type': self.video_type,
      'uploader': self.uploader_snapshot.get_snapshot_info(self.uploader),
    }
    basic_info['thumbnail_url'], basic_info['thumbnail_url_hq'] = self.get_thumbnail_url()    
    return basic_info

  def get_statistic_info(self):
    statistic_info = {
      'hits': self.hits,
      'comment_counter': self.comment_counter,
      'bullets': self.bullets,
      'shares': self.shares,
      'likes': self.likes,
    }
    info = self.basic_info()
    info.update(statistic_info)
    return info

  def get_full_info(self):
    full_info = {
      'intro': self.intro_full,
      'tags': self.tags,
      'allow_tag_add': self.allow_tag_add,
    }
    info = self.get_statistic_info()
    info.update(full_info)
    return info

  def update_hot_score(self, score):
    now = time_to_seconds(datetime.now())
    raw_score = self.hot_score - self.hot_score_updated
    time_passed = now - self.hot_score_updated
    max_time = 60 * 30 # score decayed linearly to 0 after 30 min
    decay = max(-1.0 * time_passed / max_time + 1, 0)
    new_score = now + int(min(decay * raw_score + score, max_time))
    self.hot_score = new_score
    self.hot_score_updated = now

  @classmethod
  def get_video_count(cls, category="-"):
    try:
      return cls.video_counter[category].counter
    except Exception:
      category_counter = CategoryCounter.query(ancestor=ndb.Key('CategoryCounter', category)).get()
      if not category_counter:
        return 0
      else:
        cls.video_counter[category] = category_counter
        return cls.video_counter[category].counter

  @classmethod
  def get_max_id(cls):
    try:
      return Video.video_id_factory.id_counter
    except AttributeError:
      Video.video_id_factory = VideoIDFactory.query(ancestor=ndb.Key('EntityType', 'VideoIDFactory')).get()
      if not Video.video_id_factory:
        return 0
      else:
        return Video.video_id_factory.id_counter

  @classmethod
  @ndb.transactional(retries=10)
  def video_count_inc_dec(cls, action, category="-"):
    try:
      if action == 'inc':
        cls.video_counter[category].counter += 1
      else: # dec
        cls.video_counter[category].counter -= 1
      cls.video_counter[category].put()
    except Exception:
      category_counter = CategoryCounter.query(ancestor=ndb.Key('CategoryCounter', category)).get()
      if not category_counter:
        category_counter = CategoryCounter(parent=ndb.Key('CategoryCounter', category))

      if action == 'inc':
        category_counter.counter += 1
      else: # dec
        category_counter.counter -= 1
      category_counter.put()
      cls.video_counter[category] = category_counter

  @classmethod
  @ndb.transactional(retries=10)
  def getID(cls):
    try:
      cls.video_id_factory.id_counter += 1
      cls.video_id_factory.put()
    except AttributeError:
      cls.video_id_factory = VideoIDFactory.query(ancestor=ndb.Key('EntityType', 'VideoIDFactory')).get()
      if not cls.video_id_factory:
        cls.video_id_factory = VideoIDFactory(parent=ndb.Key('EntityType', 'VideoIDFactory'))
      cls.video_id_factory.id_counter += 1
      cls.video_id_factory.put()
    return cls.video_id_factory.id_counter

  def delete_index(self, index_name):
    index = search.Index(name=index_name)
    index.delete(self.key.urlsafe())

  def create_index(self, index_name, rank):
    index = search.Index(name=index_name)
    searchable = ' '.join(self.tags + [self.title, self.intro[:200]]);
    category, subcategory = self.category.split('-')
    doc = search.Document(
      doc_id = self.key.urlsafe(),
      fields = [
        search.TextField(name='content', value=searchable.lower()),
        search.AtomField(name='category', value=category),
        search.AtomField(name='subcategory', value=subcategory),
        search.AtomField(name='uper', value=self.uploader.id())
      ],
      rank = rank
    )
    add_result = index.put(doc)

  @classmethod
  def Create(cls, user, intro, title, category, subcategory, video_type, duration, thumbnail, default_thumbnail, tags, allow_tag_add):
    try:
      video_id = 'dt'+str(cls.getID())
    except TransactionFailedError:
      logging.info(e)
      raise Exception('Failed to submit the video. Please try again.')

    category = category+'-'+subcategory
    current_time = time_to_seconds(datetime.now())
    video = cls(
      id = video_id,
      uploader = user.key,
      uploader_snapshot = user.create_snapshot(),
      intro = intro,
      title = title,
      category = category,
      video_type = video_type,
      duration = duration,
      tags = tags,
      allow_tag_add = allow_tag_add,
      thumbnail = thumbnail,
      default_thumbnail = default_thumbnail,
      hot_score_updated = current_time,
      hot_score = current_time,
    )
    video.put()

    while True:
      try:
        cls.video_count_inc_dec('inc', category)
        break
      except TransactionFailedError:
        pass
    return video

  def Delete(self):
    if self.playlist_belonged:
      playlist, list_detail = ndb.get_multi([self.playlist_belonged, PlayList.get_detail_key(self.playlist_belonged)])
      if playlist.first_video == self.key:
        playlist.reset_first_video()
      list_detail.videos.remove(self.key)
      ndb.put_multi_async([playlist, list_detail])

    if self.thumbnail:
      images.delete_serving_url(self.thumbnail)
      blobstore.BlobInfo(self.thumbnail).delete()

    video_clips = VideoClip.query(ancestor=self.key).fetch(keys_only=True)
    for i in xrange(0, len(video_clips)):
      video_clips[i].Delete()

    comments = Comment.query(ancestor=self.key).fetch(keys_only=True)
    for i in xrange(0, len(comments)):
      comment = comments[i]
      inner_comments = InnerComment.query(ancestor=comment).fetch(keys_only=True)
      for j in xrange(0, len(inner_comments)):
        inner_comments[j].delete_async()
      comment.delete_async()
    
    while True:
      try:
        cls.video_count_inc_dec('dec', self.category)
        break;
      except Exception, e:
        pass

    self.delete_index('videos_by_created')
    self.delete_index('videos_by_hits')
    self.delete_index('videos_by_likes')
    self.key.delete_async()

Danmaku_Positions = ['Scroll', 'Top', 'Bottom']
class Danmaku(ndb.Model):
  index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  position = ndb.StringProperty(required=True, default='Scroll', choices=Danmaku_Positions, indexed=False)
  color = ndb.IntegerProperty(required=True, default=255*256*256+255*256+255, indexed=False)
  size = ndb.IntegerProperty(required=True, default=16, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

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
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

class CodeDanmaku(ndb.Model):
  index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

class DanmakuPool(ndb.Model):
  counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  danmaku_list = ndb.LocalStructuredProperty(Danmaku, repeated=True, indexed=False)

class AdvancedDanmakuPool(ndb.Model):
  counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  danmaku_list = ndb.LocalStructuredProperty(AdvancedDanmaku, repeated=True, indexed=False)

class SubtitleDanmakuPool(ndb.Model):
  subtitles = ndb.TextProperty(required=True, indexed=False)
  status = ndb.StringProperty(required=True, indexed=False, default='Pending', choices=['Pending', 'Approved'])
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

class CodeDanmakuPool(ndb.Model):
  counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  danmaku_list = ndb.LocalStructuredProperty(CodeDanmaku, repeated=True, indexed=False)

class Comment(ndb.Model):
  creator = ndb.KeyProperty(kind='User', required=True)
  creator_snapshot = ndb.LocalStructuredProperty(UserSnapshot, required=True, indexed=False)
  video_title = ndb.StringProperty(required=True, indexed=False)

  content = ndb.TextProperty(required=True, indexed=False)
  deleted = ndb.BooleanProperty(required=True, default=False, indexed=False)
  floorth = ndb.IntegerProperty(required=True, indexed=False)
  inner_floorth = ndb.IntegerProperty(indexed=False)
  inner_comment_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def get_deleted_content(cls):
    content_info = {
      'id': 'None',
      'content': '',
      'floorth': 'None',
      'inner_floorth': 'None',
      'deleted': True,
      'created': 'None',
    }
    content_info['video'] = {
      'title': 'Video deleted',
      'url': 'None',
    }
    content_info['user'] = {
      'id': 'None',
      'space_url': 'None',
      'nickname': 'None',
      'avatar_url': '/static/emoticons_img/default_avatar0.png',
      'avatar_url_small': '/static/emoticons_img/default_avatar0.png',
    }
    return content_info

  def get_content(self):
    content_info = {
      'id': self.id(),
      'content': self.content,
      'floorth': self.floorth,
      'inner_floorth': self.inner_floorth,
      'inner_comment_counter': self.inner_comment_counter,
      'deleted': self.deleted,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'user': self.creator_snapshot.get_snapshot_info(self.creator),
    }
    content_info['video'] = {
      'title': video_title,
    }
    if self.key.parent().kind() == 'Video':
      content_info['url'] = Video.get_video_url(self.key.parent().id())
    else:
      content_info['url'] = Video.get_video_url(self.key.parent().parent().id())
    return content_info

  @classmethod
  @ndb.transactional(retries=10)
  def CreateComment(cls, user, video, content):
    newest_comment = cls.query(ancestor=video.key).order(-cls.created).get()
    if not newest_comment:
      comment_counter = 0
    else:
      comment_counter = newest_comment.floorth
    comment_counter += 1
    
    comment = cls(parent=video.key, creator=user.key, creator_snapshot=user.create_snapshot(), content=content, floorth=comment_counter)
    comment.put()
    return comment

  @classmethod
  @ndb.transactional(retries=10)
  def CreateInnerComment(cls, user, comment, content):
    comment.inner_comment_counter += 1
    inner_comment = cls(parent=comment.key, creator=user, creator_snapshot=user.create_snapshot(), content=content, floorth=comment.floorth, inner_floorth=comment.inner_comment_counter)
    ndb.put_multi([comment, inner_comment])
    return inner_comment

  def Delete():
    self.deleted = True
    self.content = ''
    self.put_async()

class Message(ndb.Model):
  sender = ndb.KeyProperty(kind='User', required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  when = ndb.DateTimeProperty(required=True, indexed=False)

class MessageThread(ndb.Model):
  messages = ndb.LocalStructuredProperty(Message, repeated=True, indexed=False)
  subject = ndb.StringProperty(required=True, indexed=False)
  users = ndb.KeyProperty(kind='User', repeated=True)
  users_backup = ndb.KeyProperty(kind='User', repeated=True, indexed=False)
  new_messages = ndb.IntegerProperty(required=True, indexed=False)
  updated = ndb.DateTimeProperty(required=True)

  def get_partner_key(self, user_key):
    for user in thread.users_backup:
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
  creator_snapshot = ndb.LocalStructuredProperty(UserSnapshot, required=True, indexed=False)
  content = ndb.TextProperty(indexed=False)
  record_type = ndb.StringProperty(required=True, choices=Danmaku_Types, indexed=False)
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  clip_index = ndb.IntegerProperty(required=True, indexed=False)
  video_title = ndb.StringProperty(required=True, indexed=False)
  timestamp = ndb.FloatProperty(indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

  def get_content(self):
    content_info = {
      'record_type': self.record_type,
      'content': self.content,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'user': self.creator_snapshot.get_snapshot_info(self.key.parent()),
    }
    content_info['video'] = {
      'url': Video.get_video_url(self.video.id())
      'title': self.video_title,
      'clip_index': self.clip_index,
    }
    return content_info

class MentionedRecord(ndb.Model):
  receivers = ndb.KeyProperty(kind='User', repeated=True)
  target = ndb.KeyProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  def Create(cls, user_keys, target):
    if not user_keys:
      return

    users = ndb.get_multi(user_keys)
    for i in xrange(0, len(users)):
      users[i].new_mentions += 1

    mentioned_record = MentionedRecord(receivers=user_keys, target=target)
    ndb.put_multi_async([mentioned_record] + users)

class ViewRecord(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  clip_index = ndb.IntegerProperty(required=True, default=0, indexed=False)
  timestamp = ndb.IntegerProperty(required=True, default=0, indexed=False)
  created = ndb.DateTimeProperty(auto_now=True)

  @classmethod
  @ndb.transactional(retries=10)
  def get_or_create(cls, user_key, video_key):
    record = cls.query(cls.video==video.key, ancestor=user_key).get()
    if not record:
      record = cls(parent=user_key, video=video_key)
      record.put()
      return record, True
    else:
      return record, False

class LikeRecord(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  @ndb.transactional(retries=10)
  def unique_create(cls, video_key, user_key):
    record_key = cls.query(cls.video==video_key, ancestor=user_key).get(keys_only=True)
    if not record_key:
      record = cls(parent=user_key, video=video_key).put()
      record.put()
      return True
    else:
      return False

class Subscription(ndb.Model):
  uper = ndb.KeyProperty(kind='User', required=True)
  score = ndb.DateTimeProperty(auto_now_add=True)

  @classmethod
  @ndb.transactional(retries=10)
  def unique_create(cls, uper_key, user_key):
    subscription = cls.query(cls.uper==uper_ey, ancestor=user_key).get(keys_only=True)
    if not subscription:
      subscription = cls(parent=user_key, uper=uper_key).put()
      subscription.put()
      return True
    else:
      return False

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
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  clip_index = ndb.IntegerProperty(required=True, indexed=False)
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
  comment = ndb.KeyProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  user = ndb.StringProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)

Danmaku_Issues = ['Blocking screen', 'Misleading information', 'Suspicious code danmaku'] + Comment_Issues
class ReportDanmaku(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  clip_index = ndb.IntegerProperty(required=True, indexed=False)
  issue = ndb.StringProperty(required=True, choices=Danmaku_Issues, indexed=False)
  description = ndb.TextProperty(indexed=False)
  processed = ndb.BooleanProperty(required=True, default=False, indexed=False)
  reporter = ndb.KeyProperty(kind='User', required=True, indexed=False)
  pool = ndb.KeyProperty(required=True, indexed=False)
  danmaku_index = ndb.IntegerProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  user = ndb.StringProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
