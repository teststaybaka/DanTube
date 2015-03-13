from google.appengine.ext import db
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
  return int((time - datetime(2000, 1, 1)).total_seconds())

class History(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  last_viewed_time = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  # last_viewed_timestamp

class Favorite(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  favored_time = ndb.DateTimeProperty(auto_now=True, indexed=False)

class User(webapp2_extras.appengine.auth.models.User):
  verified = ndb.BooleanProperty(required=True, indexed=False)
  nickname = ndb.StringProperty(required=True)
  intro = ndb.TextProperty(default="", required=True, indexed=False)
  avatar = ndb.BlobKeyProperty(indexed=False)
  default_avatar = ndb.IntegerProperty(default=1, choices=[1,2,3,4,5,6], indexed=False)
  spacename = ndb.StringProperty(indexed=False)
  css_file = ndb.BlobKeyProperty(indexed=False)
  # favorites = ndb.KeyProperty(kind='Video', repeated=True)
  favorites = ndb.StructuredProperty(Favorite, repeated=True, indexed=False)
  favorites_limit = ndb.IntegerProperty(default=100, required=True, indexed=False)
  # history = ndb.KeyProperty(kind='Video', repeated=True)
  history = ndb.StructuredProperty(History, repeated=True, indexed=False)
  subscriptions = ndb.KeyProperty(kind='User', repeated=True, indexed=False)
  bullets = ndb.IntegerProperty(required=True, default=0, indexed=False)
  videos_submitted = ndb.IntegerProperty(required=True, default=0, indexed=False)
  playlists_created = ndb.IntegerProperty(required=True, default=0, indexed=False)
  videos_watched = ndb.IntegerProperty(required=True, default=0, indexed=False)
  videos_favored = ndb.IntegerProperty(required=True, default=0, indexed=False)
  space_visited = ndb.IntegerProperty(required=True, default=0, indexed=False)
  subscribers_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  threads_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)
  new_messages = ndb.IntegerProperty(required=True, default=0, indexed=False)

  def delete_index(self):
    index = search.Index(name='upers_by_created')
    index.delete(self.key.urlsafe())

  def create_index(self):
    index = search.Index(name='upers_by_created')
    searchable = " ".join([self.nickname, self.intro]);
    doc = search.Document(
      doc_id = self.key.urlsafe(), 
      fields = [
        search.TextField(name='content', value=searchable),
      ],
      rank = time_to_seconds(self.created),
    )
    try:
      add_result = index.put(doc)
    except search.Error:
      logging.info('failed to create upers_by_created index for user %s' % (self.key.id()))

  def set_password(self, raw_password):
    self.password = security.generate_password_hash(raw_password, length=12)

  def get_public_info(self):
    public_info = {}
    public_info['id'] = self.key.id()
    public_info['verified'] = self.verified
    public_info['nickname'] = self.nickname
    public_info['intro'] = self.intro
    public_info['created'] = self.created.strftime("%Y-%m-%d %H:%M")
    public_info['spacename'] = self.spacename
    if self.css_file:
      public_info['space_css'] = str(self.css_file)
    else:
      public_info['space_css'] = ''

    if self.avatar:
      avatar_url = images.get_serving_url(self.avatar)
    else:
      avatar_url = '/static/emoticons_img/default_avatar' + str(self.default_avatar) + '.png'
      
    public_info['avatar_url'] = avatar_url
    public_info['space_url'] = '/user/' + str(self.key.id())
    
    return public_info

  def get_private_info(self):
    private_info = {
      'email': self.email,
      'bullets': self.bullets
    }
    return private_info

  def get_statistic_info(self):
    statistic_info = {
      'videos_submitted': self.videos_submitted,
      'videos_watched': self.videos_watched,
      'videos_favored': self.videos_favored,
      'space_visited': self.space_visited,
      'subscribers_counter': self.subscribers_counter,
      'favorites_counter': len(self.favorites),
      'subscriptions_counter': len(self.subscriptions)
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
  sender = ndb.KeyProperty(kind='User', required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  when = ndb.DateTimeProperty(required=True) #indexed=False)

class MessageThread(ndb.Model):
  messages = ndb.LocalStructuredProperty(Message, repeated=True)
  # messages = ndb.KeyProperty(kind='Message', repeated=True, indexed=False)
  subject = ndb.StringProperty(required=True, indexed=False)
  sender = ndb.KeyProperty(kind='User')
  receiver = ndb.KeyProperty(kind='User')
  delete_user = ndb.KeyProperty(kind='User', default=None, indexed=False)
  updated = ndb.DateTimeProperty(required=True)#, indexed=False)
  new_messages = ndb.IntegerProperty(required=True, default=1, indexed=False)


Video_Category = ['Anime', 'Music', 'Dance', 'Game', 'Entertainment', 'Techs', 'Sports', 'Movie', 'TV Series']
Video_SubCategory = {'Anime': ['Continuing Anime', 'Finished Anime', 'MAD/AMV/GMV', 'MMD/3D', 'Original/Voice Acting', 'General']
                  , 'Music': ['Music Sharing', 'Cover Version', 'Instrument Playing', 'VOCALOID/UTAU', 'Music Selection', 'Sound Remix']
                  , 'Dance': ['Dance']
                  , 'Game': ['Game Video', 'Game Guides/Commentary', 'Eletronic Sports', 'Mugen']
                  , 'Entertainment': ['Funny Video', 'Animal Planet', 'Tasty Food', 'Entertainment TV Show']
                  , 'Techs': ['Documentary', 'Various Techs', 'Wild Techs', 'Funny Tech Intro']
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
  'TV Series': ['series', {
    # Subcategories of TV Series
    'Continuing Series': 'continuing',
    'Finished Series': 'finished',
    'Tokusatsu': 'tokusatsu',
    'Trailer/Highlights': 'trailer',
  }],
};

MAX_QUERY_RESULT = 1000
DEFAULT_PAGE_SIZE = 10

class PlayList(ndb.Model):
  creator = ndb.KeyProperty(kind='User', required=True)
  title = ndb.StringProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
  modified = ndb.DateTimeProperty(auto_now_add=True)
  videos = ndb.KeyProperty(kind='Video', repeated=True, indexed=False)
  intro = ndb.TextProperty(required=True, default='', indexed=False)

  def get_basic_info(self):
    basic_info = {
      'videos_num': len(self.videos),
      'title': self.title, 
      'intro': self.intro,
      'id': self.key.id(),
    }
    if len(self.videos) != 0:
      video_info = self.videos[0].get().get_basic_info()
      basic_info['thumbnail_url'] = video_info['thumbnail_url']
      basic_info['thumbnail_url_hq'] = video_info['thumbnail_url_hq']
      basic_info['url'] = video_info['url']
    else:
      basic_info['thumbnail_url'] = '/static/img/empty_list.png'
      basic_info['thumbnail_url_hq'] = '/static/img/empty_list.png'
    return basic_info

  def change_info(self, title, intro):
    changed = False
    if self.title != title:
      self.title = title
      changed = True

    if self.intro != intro:
      self.intro = intro
      changed = True

    if changed:
      self.modified = datetime.now()
      self.put()
      self.create_index('playlists_by_modified', time_to_seconds(self.modified) )
      self.create_index('playlists_by_user' + str(self.creator.id()), time_to_seconds(self.modified) )

  def delete_index(self, index_name):
    index = search.Index(name=index_name)
    index.delete(self.key.urlsafe())

  def Delete(self):
    videos = ndb.get_multi(self.videos)
    for i in range(0, len(videos)):
        videos[i].playlist_belonged = None
    ndb.put_multi(videos)

    self.delete_index('playlists_by_modified')
    self.delete_index('playlists_by_user' + str(self.creator.id()))
    self.key.delete()

  def create_index(self, index_name, rank):
    index = search.Index(name=index_name)
    searchable = " ".join([self.title, self.intro]);
    doc = search.Document(
      doc_id = self.key.urlsafe(), 
      fields = [
        search.TextField(name='content', value=searchable),
      ],
      rank = rank
    )
    try:
      add_result = index.put(doc)
    except search.Error:
      logging.info('failed to create %s index for playlist %s' % (index_name, self.key.id()))

  @staticmethod
  def Create(user, title, intro):
    new_list = PlayList(creator=user.key, title=title, intro=intro)
    new_list.put()

    user.playlists_created += 1
    user.put()

    new_list.create_index('playlists_by_modified', time_to_seconds(new_list.modified) )
    new_list.create_index('playlists_by_user' + str(new_list.creator.id()), time_to_seconds(new_list.modified) )
    return new_list


class VideoClip(ndb.Model):
  subintro = ndb.TextProperty(default='', required=True, indexed=False)
  raw_url = ndb.StringProperty(indexed=False)
  vid = ndb.StringProperty(required=True, indexed=False)
  source = ndb.StringProperty(required=True, choices=['youtube'])

  @staticmethod
  def parse_url(raw_url):
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

  @staticmethod
  def Create(subintro, raw_url):
    res = VideoClip.parse_url(raw_url)
    clip = VideoClip(
      subintro=subintro, 
      raw_url=raw_url,
      vid = res['vid'],
      source=res['source']
    )
    clip.put()
    return clip

  def set_url(self, raw_url):
    res = VideoClip.parse_url(raw_url)
    self.raw_url = raw_url
    self.vid = res['vid']
    self.source = res['source']

class CategoryCounter(ndb.Model):
  counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

class VideoIDFactory(ndb.Model):
  id_counter = ndb.IntegerProperty(required=True, default=0, indexed=False)

class Video(ndb.Model):
  created = ndb.DateTimeProperty(auto_now_add=True)
  last_liked = ndb.DateTimeProperty(default=datetime.fromtimestamp(0))
  uploader = ndb.KeyProperty(kind='User', required=True)
  description = ndb.TextProperty(required=True, indexed=False)
  title = ndb.StringProperty(required=True, indexed=False)
  category = ndb.StringProperty(required=True, choices=Video_Category)
  subcategory = ndb.StringProperty(required=True)
  video_type = ndb.StringProperty(required=True, choices=['original', 'republish'], default='republish')
  thumbnail = ndb.BlobKeyProperty(indexed=False)

  video_clips = ndb.KeyProperty(kind='VideoClip', repeated=True, indexed=False)
  video_clip_titles = ndb.StringProperty(repeated=True, indexed=False)
  default_thumbnail = ndb.StringProperty(indexed=False)

  playlist_belonged = ndb.KeyProperty(kind='PlayList', indexed=False)
  allow_tag_add = ndb.BooleanProperty(required=True, default=True, indexed=False)
  tags = ndb.StringProperty(repeated=True, indexed=False)
  banned_tags = ndb.StringProperty(repeated=True, indexed=False)

  hits = ndb.IntegerProperty(required=True, default=0)
  hot_score = ndb.IntegerProperty(required=True, default=0)
  hot_score_updated = ndb.IntegerProperty(required=True, default=0)
  likes = ndb.IntegerProperty(required=True, default=0)
  favors = ndb.IntegerProperty(required=True, default=0)
  bullets = ndb.IntegerProperty(required=True, default=0)
  be_collected = ndb.IntegerProperty(required=True, default=0, indexed=False)
  comment_counter = ndb.IntegerProperty(required=True, default=0)

  # cls_var = 0
  # page_size = 3
  # page_cursors = {}
  video_counter = {}

  @staticmethod
  def get_query(category="", subcategory=""):
    if category:
      if subcategory:
        query = Video.query(Video.category==category, Video.subcategory==subcategory)
      else:
        query = Video.query(Video.category==category)
    else:
      query = Video.query()
    return query

  @staticmethod
  def get_video_count(category="", subcategory=""):
    count_key = category + ';' + subcategory
    try:
      return Video.video_counter[count_key].counter
    except Exception:
      category_counter = CategoryCounter.query(ancestor=ndb.Key('CategoryCounter', count_key)).get()
      if not category_counter:
        return 0
      else:
        Video.video_counter[count_key] = category_counter
        return Video.video_counter[count_key].counter

  @staticmethod
  @ndb.transactional(retries=10)
  def inc_video_count(category="", subcategory=""):
    count_key = category + ';' + subcategory
    try:
      Video.video_counter[count_key].counter += 1
      Video.video_counter[count_key].put()
    except Exception:
      category_counter = CategoryCounter.query(ancestor=ndb.Key('CategoryCounter', count_key)).get()
      if not category_counter:
        category_counter = CategoryCounter(parent=ndb.Key('CategoryCounter', count_key))
      category_counter.counter += 1
      category_counter.put()
      Video.video_counter[count_key] = category_counter

  @staticmethod
  @ndb.transactional(retries=10)
  def dec_video_count(category="", subcategory=""):
    count_key = category + ';' + subcategory
    try:
      Video.video_counter[count_key].counter -= 1
      Video.video_counter[count_key].put()
    except Exception:
      category_counter = CategoryCounter.query(ancestor=ndb.Key('CategoryCounter', count_key)).get()
      if not category_counter:
        category_counter = CategoryCounter(parent=ndb.Key('CategoryCounter', count_key))
      category_counter.counter -= 1
      category_counter.put()
      Video.video_counter[count_key] = category_counter

  @staticmethod
  def get_page_count(page_size, category="", subcategory=""):
    video_count = Video.get_video_count(category, subcategory)
    page_count = math.ceil(video_count/float(page_size))
    return min(page_count, 100)

  @staticmethod
  def get_page(page_size, page, category="", subcategory="", order=""):
    page_count = Video.get_page_count(category=category, subcategory=subcategory, page_size=page_size)
    if page > page_count:
      return [], page_count
    offset = (page - 1) * page_size
    videos = Video.get_query(category, subcategory).order(-order).fetch(limit=page_size, offset=offset)
    return videos, page_count

  @classmethod
  def fetch_page(cls, page, category="", subcategory="", order=""):
    page_count = cls.get_page_count(category, subcategory)
    if page > page_count:
      return [], False
    
    query_key = category + ';' + subcategory + ';' + order._name
    query = cls._get_query(category, subcategory)
    query_forward = query.order(-order) # descending order as forward
    query_backward = query.order(order)
    
    try:
      cursors = cls._page_cursors[query_key]
    except KeyError:
      cls._page_cursors[query_key] = {}
      cursors = cls._page_cursors[query_key]

    logging.info(cursors)
    logging.info('-------')
    if page == 1:
      videos, next_cursor, more = query_forward.fetch_page(cls._page_size)
      if next_cursor:
        cursors[page+1] = next_cursor
    else:
      is_last_page = False
      if page == page_count:
        if page in cursors: # already has the last page cursor, done
          cursor = cursors[page]
          videos, next_cursor, more = query_forward.fetch_page(cls._page_size, start_cursor=cursor)
          return videos, more
        else: # need to fetch the previous page to get the last page cursor
          page -= 1
          is_last_page = True

      cached_pages = cursors.keys()
      if not cached_pages:
        offset = cls._page_size * (page - 1)
        videos, next_cursor, more = query_forward.fetch_page(cls._page_size, offset=offset)
        if next_cursor:
          cursors[page+1] = next_cursor
      else:
        # find the nearest cached page, O(n) time, might be improved using btree
        nearest_page = min(cached_pages, key=lambda x:abs(x-page))
        
        if nearest_page <= page:
          cursor = cursors[nearest_page]
          offset = cls._page_size * (page - nearest_page)
          videos, next_cursor, more = query_forward.fetch_page(cls._page_size, offset=offset, start_cursor=cursor)
          if next_cursor:
            cursors[page+1] = next_cursor

        else: # nearest_page >= page + 1
          rev_cursor = cursors[nearest_page].reversed()
          offset = cls._page_size * (nearest_page - page - 1)
          videos, next_cursor, more = query_backward.fetch_page(cls._page_size, offset=offset, start_cursor=rev_cursor)
          if next_cursor:
            cursors[page] = next_cursor.reversed()

      if is_last_page:
        page += 1
        try:
          cursor = cursors[page]
          videos, next_cursor, more = query_forward.fetch_page(cls._page_size, start_cursor=cursor)
        except KeyError:
          return [], False

    logging.info(cursors)
    logging.info(cls._page_cursors)
    return videos, more

  def update_hot_score(self, score):
    now = time_to_seconds(datetime.now())
    raw_score = self.hot_score - self.hot_score_updated
    time_passed = now - self.hot_score_updated
    max_time = 60 * 30 # score decayed linearly to 0 after 30 min
    decay = max(-1.0 * time_passed / max_time + 1, 0)
    new_score = now + int(min(decay * raw_score + score, max_time))
    self.hot_score = new_score
    self.hot_score_updated = now

  def get_basic_info(self):
    if self.thumbnail is None:
      thumbnail_url = 'http://img.youtube.com/vi/' + self.default_thumbnail + '/mqdefault.jpg'
      thumbnail_url_hq = 'http://img.youtube.com/vi/' + self.default_thumbnail + '/maxresdefault.jpg'
    else:
      thumbnail_url = images.get_serving_url(self.thumbnail, size=240)
      thumbnail_url_hq = images.get_serving_url(self.thumbnail)

    basic_info = {
      'title': self.title,
      'url': '/video/'+ str(self.key.id()),
      'id_num': self.key.id().replace('dt', ''),
      'thumbnail_url': thumbnail_url,
      'thumbnail_url_hq': thumbnail_url_hq,
      'description': self.description,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'category': self.category,
      'subcategory': self.subcategory,
      'hits': self.hits,
      'bullets': self.bullets,
      'comment_counter': self.comment_counter,
      'likes': self.likes,
      'favors': self.favors,
      'last_liked': self.last_liked.strftime("%Y-%m-%d %H:%M:%S"),
      'tags': self.tags,
      'type': self.video_type,
    }
    return basic_info

  def get_full_info(self):
    full_info = {
      'clips': [],
      'allow_tag_add': self.allow_tag_add,
    }
    clips = ndb.get_multi(self.video_clips)
    for i in range(0, len(self.video_clips)):
      full_info['clips'].append({
        'subtitle': self.video_clip_titles[i],
        'subintro': clips[i].subintro,
        'raw_url': clips[i].raw_url,
        'source': clips[i].source,
        'index': i,
      })
    full_info.update(self.get_basic_info())
    return full_info

  def delete_index(self, index_name):
    index = search.Index(name=index_name)
    index.delete(self.key.urlsafe())

  def create_index(self, index_name, rank):
    index = search.Index(name=index_name)
    searchable = " ".join(self.tags + [self.title, self.description]);
    doc = search.Document(
      doc_id = self.key.urlsafe(), 
      fields = [
        search.TextField(name='content', value=searchable),
        search.AtomField(name='category', value=self.category),
        search.AtomField(name='subcategory', value=self.subcategory)
      ],
      rank = rank
    )
    try:
      add_result = index.put(doc)
    except search.Error:
      logging.info('failed to create %s index for video %s' % (index_name, self.key.id()))

  @staticmethod
  def get_by_id(id):
    return super(Video, Video).get_by_id(id, parent=ndb.Key('VideoEntry', 'Video'+id))

  @staticmethod
  def get_max_id():
    try:
      return Video.video_id_factory.id_counter
    except AttributeError:
      Video.video_id_factory = VideoIDFactory.query(ancestor=ndb.Key('EntityType', 'VideoIDFactory')).get()
      if not Video.video_id_factory:
        return 0
      else:
        return Video.video_id_factory.id_counter

  @staticmethod
  @ndb.transactional(retries=10)
  def getID():
    try:
      Video.video_id_factory.id_counter += 1
      Video.video_id_factory.put()
    except AttributeError:
      Video.video_id_factory = VideoIDFactory.query(ancestor=ndb.Key('EntityType', 'VideoIDFactory')).get()
      if not Video.video_id_factory:
        Video.video_id_factory = VideoIDFactory(parent=ndb.Key('EntityType', 'VideoIDFactory'))
      Video.video_id_factory.id_counter += 1
      Video.video_id_factory.put()
    return Video.video_id_factory.id_counter

  @staticmethod
  def Create(user, description, title, category, subcategory, video_type, tags, allow_tag_add, thumbnail, subtitles, video_clips):
    try:
      id = 'dt'+str(Video.getID())
      logging.info(id)
      current_time = time_to_seconds(datetime.now())
      video = Video(
        parent = ndb.Key('VideoEntry', 'Video'+id),
        id = id,
        # key = ndb.Key('Video', id, parent=ndb.Key('VideoEntry', 'Video'+id)),
        uploader = user.key,
        description = description,
        title = title, 
        category = category,
        subcategory = subcategory,
        video_type = video_type,
        tags = tags,
        allow_tag_add = allow_tag_add,
        thumbnail = thumbnail,
        default_thumbnail = video_clips[0].get().vid,
        video_clip_titles = subtitles,
        video_clips = video_clips,
        hot_score_updated = current_time,
        hot_score = current_time
      )
      video.put()
    except Exception, e:
      logging.info(e)
      # Video._dec_video_count(category)
      # Video._dec_video_count(category, subcategory)
      raise Exception('Failed to submit the video. Please try again.')
    else:
      Video.inc_video_count(category)
      Video.inc_video_count(category, subcategory)
      video.create_index('videos_by_created', time_to_seconds(video.created) )
      video.create_index('videos_by_hits', video.hits )
      video.create_index('videos_by_favors', video.favors )
      video.create_index('videos_by_user' + str(video.uploader.id()), time_to_seconds(video.created) )
      return video

  def Delete(self):
    if self.playlist_belonged != None:
      belonged = self.playlist_belonged.get()
      idx = belonged.videos.index(self.key)
      belonged.videos.pop(idx)
      belonged.put()

    if self.thumbnail != None:
      images.delete_serving_url(self.thumbnail)
      blobstore.BlobInfo(self.thumbnail).delete()

    for i in range(0, len(self.video_clips)):
      self.video_clips[i].delete()

    Video.dec_video_count(self.category)
    Video.dec_video_count(self.category, self.subcategory)
    self.delete_index('videos_by_created')
    self.delete_index('videos_by_hits')
    self.delete_index('videos_by_favors')
    self.delete_index('videos_by_user' + str(self.uploader.id()))
    self.key.delete()

class Danmaku(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True, indexed=False)
  timestamp = ndb.FloatProperty(required=True, indexed=False)
  content = ndb.StringProperty(required=True, indexed=False)
  position = db.StringProperty(required=True, default='RightToLeft', choices=['RightToLeft', 'Top', 'Bottom'], indexed=False)
  color = db.IntegerProperty(required=True, default=255*256*256+255*256+255, indexed=False)
  # creator = db.ReferenceProperty(User)
  # order = ndb.IntegerProperty(required=True)
  protected = ndb.BooleanProperty(required=True, indexed=False)
  creator = ndb.KeyProperty(kind='User', required=True)
  created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)

class Comment(ndb.Model):
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False) # add an Activity class to record it
  content = ndb.TextProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
  floorth = ndb.IntegerProperty(required=True, default=0, indexed=False)
  deleted = ndb.BooleanProperty(required=True, default=False, indexed=False)
  inner_comment_counter = ndb.IntegerProperty(required=True, default=0)

  @staticmethod
  def get_by_id(id, video_key):
    return super(Comment, Comment).get_by_id(id, parent=video_key)

  @staticmethod
  @ndb.transactional(retries=10)
  def Create(video, user, content):
    video.comment_counter += 1
    video.put()

    comment = Comment(parent=video.key, creator=user.key, content=content, floorth=video.comment_counter)
    comment.put()
    return comment

  def Delete():
    self.deleted = True
    self.content = ''
    self.put()

class InnerComment(ndb.Model):
  creator = ndb.KeyProperty(kind='User', required=True, indexed=False)
  content = ndb.TextProperty(required=True, indexed=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
  floorth = ndb.IntegerProperty(required=True, default=0, indexed=False)
  inner_floorth = ndb.IntegerProperty(required=True, default=0, indexed=False)
  deleted = ndb.BooleanProperty(required=True, default=False, indexed=False)

  @staticmethod
  @ndb.transactional(retries=10)
  def Create(comment, user, content):
    comment.inner_comment_counter += 1
    comment.put()

    inner_comment = InnerComment(parent=comment.key, creator=user.key, content=content, floorth=comment.floorth, inner_floorth=comment.inner_comment_counter)
    inner_comment.put()
    return inner_comment

  def Delete():
    self.deleted = True
    self.content = ''
    self.put()

class AtUser(ndb.Model):
  sender = ndb.KeyProperty(kind='User', required=True, indexed=False)
  receiver = ndb.KeyProperty(kind='User', required=True, indexed=False)
  comment = ndb.KeyProperty(kind='Comment', indexed=False)
  inner_comment = ndb.KeyProperty(kind='CommentOfComment', indexed=False)
  danmaku = ndb.KeyProperty(kind='Danmaku', indexed=False)
