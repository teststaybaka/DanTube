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

def time_to_seconds(time):
  return int((time - datetime(2000, 1, 1)).total_seconds())

class History(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  last_viewed_time = ndb.DateTimeProperty(auto_now_add=True)
  # last_viewed_timestamp

class Favorite(ndb.Model):
  video = ndb.KeyProperty(kind='Video', required=True)
  favored_time = ndb.DateTimeProperty(auto_now=True)

class User(webapp2_extras.appengine.auth.models.User):
  verified = ndb.BooleanProperty(required=True)
  nickname = ndb.StringProperty(required=True)
  intro = ndb.StringProperty(default="")
  avatar = ndb.BlobKeyProperty()
  default_avatar = ndb.IntegerProperty(default=1, choices=[1,2,3,4,5,6])
  # favorites = ndb.KeyProperty(kind='Video', repeated=True)
  favorites = ndb.StructuredProperty(Favorite, repeated=True)
  favorites_limit = ndb.IntegerProperty(default=100, required=True)
  # history = ndb.KeyProperty(kind='Video', repeated=True)
  history = ndb.StructuredProperty(History, repeated=True)
  subscriptions = ndb.KeyProperty(kind='User', repeated=True)
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
    public_info['id'] = self.key.id()
    public_info['verified'] = self.verified
    public_info['nickname'] = self.nickname
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
      'email': self.email,
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
  sent_time = ndb.DateTimeProperty(required=True, indexed=False)

class MessageThread(ndb.Model):
  # messages = ndb.LocalStructuredProperty(Message, repeated=True)
  messages = ndb.KeyProperty(kind='Message', repeated=True, indexed=False)
  subject = ndb.StringProperty(required=True, indexed=False)
  sender = ndb.KeyProperty(kind='User', required=True)
  receiver = ndb.KeyProperty(kind='User', required=True)
  updated = ndb.DateTimeProperty(required=True)
  last_message_sender = ndb.KeyProperty(kind='User', required=True, indexed=False)
  last_message = ndb.StringProperty(required=True, indexed=False)
  new_messages = ndb.IntegerProperty(required=True, default=1, indexed=False)


Video_Category = ['Anime', 'Music', 'Dance', 'Game', 'Entertainment', 'Techs', 'Sports', 'Movie', 'TV Drama']
Video_SubCategory = {'Anime': ['Continuing Anime', 'Finished Anime', 'MAD/AMV/GMV', 'MMD/3D', 'Original/Voice Acting', 'General']
                  , 'Music': ['Music Sharing', 'Cover Version', 'Instrument Playing', 'VOCALOID/UTAU', 'Music Selection', 'Sound Remix']
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
  'TV Drama': ['drama', {
    # Subcategories of TV Drama
    'Continuing Drama': 'continuing',
    'Finished Drama': 'finished',
    'Tokusatsu': 'tokusatsu',
    'Trailer/Highlights': 'trailer',
  }],
};

PAGE_SIZE = 12
MAX_QUERY_RESULT = 1000

class PlayList(ndb.Model):
  user_belonged = ndb.KeyProperty(kind='User', required=True)
  title = ndb.StringProperty(required=True)
  video_counter = ndb.IntegerProperty(required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

  def getVideoOrder(self):
    self.video_counter += 1
    self.put()
    return self.video_counter

  @classmethod
  def Create_new_list(cls, user, title):
    playList = PlayList(user_belonged = user, title = title, video_counter = 0)
    playList.put()
    return playList

class Video(ndb.Model):
  url = ndb.StringProperty(indexed=False)
  vid = ndb.StringProperty(required=True, indexed=False)
  source = ndb.StringProperty(required=True, choices=['youtube'])
  created = ndb.DateTimeProperty(auto_now_add=True)
  last_liked = ndb.DateTimeProperty(default=datetime.fromtimestamp(0))
  uploader = ndb.KeyProperty(kind='User', required=True)
  description = ndb.StringProperty(required=True)
  title = ndb.StringProperty(required=True)
  category = ndb.StringProperty(required=True, choices=Video_Category)
  subcategory = ndb.StringProperty(required=True)
  video_type = ndb.StringProperty(required=True, choices=['self-made', 'republish'], default='republish')
  thumbnail = ndb.BlobKeyProperty()

  video_list_belonged = ndb.KeyProperty(kind='PlayList')
  video_order = ndb.IntegerProperty()
  danmaku_counter = ndb.IntegerProperty(required=True, default=0)
  comment_counter = ndb.IntegerProperty(required=True, default=0)
  allow_tag_add = ndb.BooleanProperty(required=True, default=True)
  tags = ndb.StringProperty(repeated=True)
  banned_tags = ndb.StringProperty(repeated=True)

  hits = ndb.IntegerProperty(required=True, default=0)
  likes = ndb.IntegerProperty(required=True, default=0)
  favors = ndb.IntegerProperty(required=True, default=0)
  bullets = ndb.IntegerProperty(required=True, default=0)
  be_collected = ndb.IntegerProperty(required=True, default=0)

  _cls_var = 0
  _page_size = 3
  _page_cursors = {}
  _video_counts = {}

  @classmethod
  def _get_query(cls, category="", subcategory=""):
    if category:
      if subcategory:
        query = cls.query(cls.category==category, cls.subcategory==subcategory)
      else:
        query = cls.query(cls.category==category)
    else:
      query = cls.query()
    return query

  @classmethod
  def _inc_video_count(cls, category="", subcategory=""):
    count_key = category + ';' + subcategory
    try:
      cls._video_counts[count_key] += 1
    except KeyError:
      cls._video_counts[count_key] = cls._get_query(category, subcategory).count()
      cls._video_counts[count_key] += 1

  @classmethod
  def _dec_video_count(cls, category="", subcategory=""):
    count_key = category + ';' + subcategory
    try:
      cls._video_counts[count_key] -= 1
    except KeyError:
      cls._video_counts[count_key] = cls._get_query(category, subcategory).count()
      cls._video_counts[count_key] -= 1

  @classmethod
  def get_video_count(cls, category="", subcategory=""):
    count_key = category + ';' + subcategory
    try:
      video_count = cls._video_counts[count_key]
    except KeyError:
      cls._video_counts[count_key] = cls._get_query(category, subcategory).count()
      video_count = cls._video_counts[count_key]

    return video_count

  @classmethod
  def get_page_count(cls, category="", subcategory="", page_size = PAGE_SIZE):
    video_count = cls.get_video_count(category, subcategory)
    page_count = -(-video_count // page_size)

    return min(page_count, 100)

  @classmethod
  def get_page(cls, category="", subcategory="", order="", page=1, page_size = PAGE_SIZE):
    page_count = cls.get_page_count(category, subcategory, page_size)
    if page > page_count:
      return [], page_count
    offset = (page - 1) * page_size
    videos = cls._get_query(category, subcategory).order(-order).fetch(limit=page_size, offset=offset)
    return videos, page_count

  @classmethod
  def fetch_page(cls, category="", subcategory="", order="", page=1):
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

  def get_basic_info(self):
    if self.thumbnail is None:
      thumbnail_url = 'http://img.youtube.com/vi/' + self.vid + '/mqdefault.jpg'
      thumbnail_url_hq = 'http://img.youtube.com/vi/' + self.vid + '/maxresdefault.jpg'
    else:
      thumbnail_url = images.get_serving_url(self.thumbnail)
      thumbnail_url_hq = thumbnail_url

    basic_info = {
      'title': self.title,
      'vid': self.vid,
      'url': '/video/'+ str(self.key.id()),
      'id_num': self.key.id().replace('dt', ''),
      'thumbnail_url': thumbnail_url,
      'thumbnail_url_hq': thumbnail_url_hq,
      'description': self.description,
      'created': self.created.strftime("%Y-%m-%d %H:%M"),
      'category': self.category,
      'subcategory': self.subcategory,
      'hits': self.hits,
      'danmaku_counter': self.danmaku_counter,
      'bullets': self.bullets,
      'comment_counter': self.comment_counter,
      'likes': self.likes,
      'favors': self.favors,
      'last_liked': self.last_liked.strftime("%Y-%m-%d %H:%M:%S"),
      'tags': self.tags
    }
    return basic_info

  def create_index(self, index_name, rank):
    index = search.Index(name=index_name)
    searchable = " ".join(self.tags + [self.title, self.description]);
    doc = search.Document(
      doc_id=self.key.urlsafe(), 
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
  def get_max_id(cls):
    try:
      return cls.id_counter
    except AttributeError:
      latest_video = cls.query().order(-cls.created).get()
      if latest_video is not None:
        max_id = int(latest_video.key.id()[2:])
        return max_id
      else:
        return 0

  @classmethod
  @ndb.transactional(retries=10)
  def getID(cls):
    try:
      cls.id_counter += 1
    except AttributeError:
      latest_video = cls.query(ancestor=ndb.Key('EntityType', 'Video')).order(-cls.created).get()
      if latest_video is not None:
        max_id = int(latest_video.key.id()[2:])
        logging.info(max_id)
        cls.id_counter = max_id + 1
      else:
        cls.id_counter = 1
    return cls.id_counter

  @classmethod
  def Create(cls, raw_url, user, description, title, category, subcategory, video_type, tags):
    res = cls.parse_url(raw_url)
    if res.get('error'):
      # return 'URL Error.'
      raise Exception(res['error'])
    else:
      if (category in Video_Category) and (subcategory in Video_SubCategory[category]):
        cls._inc_video_count(category)
        cls._inc_video_count(category, subcategory)  
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
            video_type = video_type,
            tags = tags
          )
          video.put()
        except Exception, e:
          logging.info(e)
          cls._dec_video_count(category)
          cls._dec_video_count(category, subcategory)
          raise Exception('Failed to submit video. Please try again.')
        else:
          video.create_index('videos_by_created', time_to_seconds(video.created) )
          video.create_index('videos_by_hits', video.hits )
          video.create_index('videos_by_favors', video.favors )
          video.create_index('videos_by_user' + str(video.uploader.id()), time_to_seconds(video.created) )
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
