import jinja2
import logging
import os
import sys
import traceback
import webapp2
import cStringIO
import itertools
import mimetools
import mimetypes
import urllib
import urllib2

from datetime import datetime
from jinja2 import Undefined
from webapp2_extras import sessions
from webapp2_extras import auth
from webapp2_extras import sessions_ndb
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.api import search
from google.appengine.ext import ndb

import models
import json
import re
import random

class SilentUndefined(Undefined):
    '''
    Dont break pageloads because vars arent there!
    '''
    def _fail_with_undefined_error(self, *args, **kwargs):
        logging.exception('JINJA2: something was undefined!')
        return None

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True,
    undefined=SilentUndefined)
env.globals = {
    'uri_for': webapp2.uri_for,
}

class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def auth(self):
        """Shortcut to access the auth instance as a property."""
        return auth.get_auth()

    @webapp2.cached_property
    def user_info(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        u = self.user_info
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        return self.auth.store.user_model

    @webapp2.cached_property
    def session(self):
        # return self.session_store.get_session(backend="datastore")
        return self.session_store.get_session(name='db_session', factory=sessions_ndb.DatastoreSessionFactory)

    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
        """
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    def render(self, tempname, context = {}):
        user = self.user
        if not context.get('user'):
            context['user'] = {}
        if user is not None:
            context['user']['is_auth'] = True
            context['user'].update(user.get_public_info())
            context['user'].update(user.get_private_info())
        else:
            context['user']['is_auth'] = False

        message = self.session.get('message')
        if message is not None:
            context['message'] = message
            self.session.pop('message')
        context['category'] = models.Video_Category
        context['subcategory'] = models.Video_SubCategory
        path = 'template/' + tempname + '.html'
        template = env.get_template(path)
        self.response.write(template.render(context))
    
    def notify(self, notice, status=200):
        self.response.set_status(status)
        self.render('notice', {'notice': notice})

def login_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if not auth.get_user_by_session():
        xrequest = self.request.headers.get('X-Requested-With')
        if xrequest and xrequest == 'XMLHttpRequest':
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Please log in!'
            }))
            return
        else:
            self.redirect(self.uri_for('signin'), abort=True)
    else:
        return handler(self, *args, **kwargs)
 
  return check_login

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return
    
    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

class Home(BaseHandler):
    def get(self):
        context = {}
        context['top_ten_videos'] = []
        videos, total_page = models.Video.get_page(order=models.Video.hits, page=1, page_size=10)
        for video in videos:
            uploader = models.User.get_by_id(video.uploader.id())
            video_info = video.get_basic_info()
            video_info['uploader'] = uploader.get_public_info()
            context['top_ten_videos'].append(video_info)
        self.render('index', context)

class Video(BaseHandler):
    def get(self):
        # models.Video.fetch_page()
        self.response.headers['Content-Type'] = 'application/json'
        category = self.request.get('category')
        subcategory = self.request.get('subcategory')

        try:
            if category:
                for cat_name, url_name in dict((k,v[0]) for k,v in models.URL_NAME_DICT.items()).iteritems():
                    if url_name == category:
                        category = cat_name
                        break
                if subcategory:
                    for subcat_name, url_name in models.URL_NAME_DICT[category][1].iteritems():
                        if url_name == subcategory:
                            subcategory = subcat_name
                            break
                else:
                    subcategory = ""
            else:
                category = ""
        except (KeyError, BadValueError) as e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid category/subcategory'
            }))
            return

        order_str = self.request.get('order')
        if not order_str:
            order = models.Video.hits
        elif order_str == 'hits':
            order = models.Video.hits
        elif order_str == 'created':
            order = models.Video.created
        elif order_str == 'last_liked':
            order = models.Video.last_liked
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid order'
            }))
            return

        page = self.request.get('page')
        if not page:
            page = 1
        else:
            try:
                page = int(self.request.get('page'))
            except ValueError:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Invalid page'
                }))
                return

        try:
            page_size = int(self.request.get('page_size'))
        except ValueError:
            page_size = models.PAGE_SIZE

        # videos, more = models.Video.fetch_page(category, subcategory, order, page)
        videos, total_pages = models.Video.get_page(category, subcategory, order, page, page_size)

        # try:
        #     videos, more = models.Video.fetch_page(category, subcategory, order, page)
        # except Exception, e:
        #     logging.info(e)
        #     self.response.out.write(json.dumps({
        #         'error': True,
        #         'message': str(e)
        #     }))
        #     return

        try:
            limit = int(self.request.get('limit'))
        except ValueError:
            limit = len(videos)

        result = {}
        result['videos'] = []
        for video in videos[0:limit]:
            uploader = models.User.get_by_id(video.uploader.id())
            video_info = video.get_basic_info()
            video_info['uploader'] = uploader.get_public_info()
            result['videos'].append(video_info)
        result['total_pages'] = total_pages

        self.response.out.write(json.dumps(result))

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        raw_url = self.request.get('video-url')
        if not raw_url:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'video url must not be empty!'
            }))
            return

        category = self.request.get('category')
        if not category:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'category must not be empty!'
            }))
            return

        subcategory = self.request.get('subcategory')
        if not subcategory:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'subcategory must not be empty!'
            }))
            return

        title = self.request.get('title')
        if not title:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'title must not be empty!'
            }))
            return

        description = self.request.get('description')
        if not description:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'description must not be empty!'
            }))
            return

        # res = models.Video.parse_url(raw_url)
        # logging.info(res)
        try:
            video = models.Video.Create(
                raw_url = raw_url,
                user = user,
                description = description,
                title = title,
                category = category,
                subcategory = subcategory
            )
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return

        self.response.out.write(json.dumps({
            'url': '/video/'+ video.key.id()
        }))
        user.videos_submited += 1
        user.put()

class RandomVideos(BaseHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        try:
            size = int(self.request.get('size'))
        except ValueError:
            size = 5

        size = min(100, models.Video.get_video_count(), size)

        try:
            result = {}
            result['videos'] = []
            max_id = models.Video.get_max_id()
            random_ids = random.sample(xrange(1,models.Video.get_max_id()+1), min(size * 2, max_id))
            fetched = 0
            for video_id in random_ids:
                video = models.Video.get_by_id('dt'+str(video_id))
                if video is not None:
                    uploader = models.User.get_by_id(video.uploader.id())
                    video_info = video.get_basic_info()
                    video_info['uploader'] = uploader.get_public_info()
                    result['videos'].append(video_info)
                    fetched += 1
                    if fetched == size:
                        result['size'] = size
                        self.response.out.write(json.dumps(result))
                        return

            result['size'] = fetched
            self.response.out.write(json.dumps(result))
            
        except Exception, e:
            logging.info('error occurred fetching random videos')
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            

class Watch(BaseHandler):
    def get(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            uploader = models.User.get_by_id(video.uploader.id())
            context = {'video': video.get_basic_info(), 'uploader': uploader.get_public_info()}
            self.render('video', context)

            video.hits += 1
            video.put()
            video.create_index('videos_by_hits', video.hits )
            uploader.videos_watched += 1
            uploader.put()

            user = self.user
            if user is not None:
                l = len(user.history)
                videos = [h.video for h in user.history]
                try:
                    idx = videos.index(video.key)
                    user.history.pop(idx)
                except ValueError:
                    logging.info('not found')
                    l += 1
                if l > 100:
                    user.history.pop(0)
                new_history = models.History(video=video.key)
                user.history.append(new_history)
                user.put()
        else:
            self.notify('video not found.', 404)

class Favor(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            if video.key not in [f.video for f in user.favorites]:
                if len(user.favorites) >= user.favorites_limit:
                    self.response.out.write(json.dumps({
                        'error': True,
                        'message': 'You have reached favorites limit.'
                    }))
                    return

                new_favorite = models.Favorite(video=video.key)
                user.favorites.append(new_favorite)
                user.put()
                self.response.out.write(json.dumps({
                    'message': 'success'
                }))
                video.favors += 1
                video.put()
                video.create_index('videos_by_favors', video.favors )
                uploader = models.User.get_by_id(video.uploader.id())
                uploader.videos_favored += 1
                uploader.put()
            else:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'video already favored'
                }))
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'video not found'
            }))

class Unfavor(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            video_keys = [f.video for f in user.favorites]
            try:
                idx = video_keys.index(video.key)
                user.favorites.pop(idx)
                user.put()
                self.response.out.write(json.dumps({
                    'message': 'success'
                }))
                video.favors -= 1
                video.put()
                video.create_index('videos_by_favors', video.favors )
                uploader = models.User.get_by_id(video.uploader.id())
                uploader.videos_favored -= 1
                uploader.put()
            except ValueError:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'video not favored',
                }))
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'video not found',
            }))

class Like(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            video.likes += 1
            video.last_liked = datetime.now()
            video.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'video not found'
            }))

class Danmaku(BaseHandler):
    def get(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            danmaku_itr = models.Danmaku.query(models.Danmaku.video==video.key)
            danmakus = []
            for danmaku in danmaku_itr:
                danmakus.append({
                    'content': danmaku.content,
                    'timestamp': danmaku.timestamp,
                    'created': danmaku.created.strftime("%m-%d %H:%M"),
                    'created_seconds': (danmaku.created - datetime(1970,1,1)).total_seconds(),
                });
            self.response.out.write(json.dumps(danmakus))
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'video not found',
            }))

    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            danmaku = models.Danmaku(
                video = video.key,
                timestamp = float(self.request.get('timestamp')),
                creator = user.key,
                content = self.request.get('content'),
                protected = False
            )
            danmaku.put()

            self.response.out.write(json.dumps({
                'timestamp': danmaku.timestamp,
                'content': danmaku.content,
                'creator': user.nickname,
                'created': danmaku.created.strftime("%m-%d %H:%M")
            }))
            video.danmaku_counter += 1
            video.put()
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'video not found',
            }))


class Player(BaseHandler):
    def get(self):
        self.render('video')

class Category(BaseHandler):
    def get(self):
        category = self.request.route.name
        context = {}
        context['category_name'] = category
        self.render('category', context)

class Subcategory(BaseHandler):
    def get(self):
        [category, subcategory] = self.request.route.name.split('-')
        context = {}
        context['category_name'] = category
        context['subcategory_name'] = subcategory
        context['video_count'] = models.Video.get_video_count(category, subcategory)
        context['page_count'] = models.Video.get_page_count(category, subcategory)
        self.render('subcategory', context)

class Space(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        self.render('space', {'host': host.get_public_info()})
        host.space_visited += 1
        host.put()

class Subscribe(BaseHandler):
    @login_required
    def post(self, user_id):
        self.response.headers['Content-Type'] = 'application/json'
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not found',
            }))
            return

        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'cannot subscribe self'
            }))
            return

        l = len(user.subscriptions)
        if host.key not in user.subscriptions:
            if l >= 1000:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'You have reached subscriptions limit.'
                }))
                return
        
            user.subscriptions.append(host.key)
            user.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
            host.subscribers_counter += 1
            host.put()
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'already subscribed'
            }))

class Unsubscribe(BaseHandler):
    @login_required
    def post(self, user_id):
        self.response.headers['Content-Type'] = 'application/json'
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not found'
            }))
            return

        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'cannot unsubscribe self'
            }))
            return

        try:
            user.subscriptions.remove(host.key)
            user.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
            host.subscribers_counter -= 1
            host.put()
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not subscribed'
            }))

class Search(BaseHandler):
    def get(self):
        # all_videos = models.Video.query().fetch()
        # for video in all_videos:
        #     video.create_index('videos_by_created', models.time_to_seconds(video.created))
        #     video.create_index('videos_by_hits', video.hits)
        #     video.create_index('videos_by_favors', video.favors)

        try:
            page_size = int(self.request.get('page_size'))
        except ValueError:
            page_size = models.PAGE_SIZE

        try:
            page = int(self.request.get('page') )
        except ValueError:
            page = 1

        page =  min(page, -(-models.MAX_QUERY_RESULT // page_size))

        offset = (page - 1) * page_size

        keywords_raw = self.request.get('keywords')
        if not keywords_raw:
            keywords = ''
            query_string = ''
        else:
            keywords = keywords_raw.strip().lower()
            if keywords:
                query_string = 'content: ' + keywords
            else:
                query_string = ''

        context = {}
        category = self.request.get('category')
        if category:
            if category in models.Video_Category:
                context['cur_category'] = category
                if not keywords:
                    query_string += 'category: \"' + category + '\"'
                else:
                    query_string += ' AND category: \"' + category + '\"'
                subcategory = self.request.get('subcategory')
                if subcategory:
                    if subcategory in models.Video_SubCategory[category]:
                        context['cur_subcategory'] = subcategory
                        query_string += ' AND subcategory: \"' + subcategory + '\"'
                                   
        options = search.QueryOptions(offset=offset, limit=page_size)
        query = search.Query(query_string=query_string, options=options)

        order = self.request.get('order')
        if not order:
            index = search.Index(name='videos_by_hits')
        elif order == 'hits':
            index = search.Index(name='videos_by_hits')
        elif order == 'created':
            index = search.Index(name='videos_by_created')
        elif order == 'favors':
            index = search.Index(name='videos_by_favors')
        else:
            index = search.Index(name='videos_by_hits')
        
        try:
            result = index.search(query)                
            total_found = result.number_found
            total_videos = min(total_found, 1000)
            total_pages = -(-total_videos // page_size)
            
            fetched_videos = len(result.results)
            if total_videos > 0 and fetched_videos == 0:
                # fetch last page
                page = total_pages
                offset = (page - 1) * page_size
                options = search.QueryOptions(offset=offset, limit=page_size)
                query = search.Query(query_string=query_string, options=options)
                result = index.search(query)

            video_keys = []
            for video_doc in result.results:
                video_keys.append(ndb.Key(urlsafe=video_doc.doc_id))
            videos = ndb.get_multi(video_keys)

            min_page = max(page-2, 1);
            max_page = min(min_page + 4, total_pages);
            context.update({
                'keywords': keywords_raw,
                'order': order,
                'videos': [], 
                'total_found': total_found,
                'total_videos': total_videos,
                'total_pages': total_pages,
                'cur_page': page,
                'page_range': range(min_page, max_page+1)
            })

            for video in videos:
                video_info = video.get_basic_info()
                uploader = models.User.get_by_id(video.uploader.id())
                video_info['uploader'] = uploader.get_public_info()
                context['videos'].append(video_info)

            # logging.info(videos)
            self.render('search', context)

        except search.Error:
            logging.info("search failed")
            self.render('search', {'error': 'search failed due to internal error.'})

        # total_pages = -(-total_videos // page_size)

        # result = index.search("")
        # logging.info(result.number_found)
        # for doc in result.results:
        #     logging.info(doc)

        # key_words_ori = self.request.get('keywords')
        # logging.info(key_words_ori)
        # self.render('search', {'keywords': key_words_ori})