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

import models
import json
import re

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
        self.render('index')

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

        # videos, more = models.Video.fetch_page(category, subcategory, order, page)
        videos, total_pages = models.Video.get_page(category, subcategory, order, page)

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

class Watch(BaseHandler):
    def get(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            uploader = models.User.get_by_id(video.uploader.id())
            context = {'video': video.get_basic_info(), 'uploader': uploader.get_public_info()}
            self.render('video', context)

            video.hits += 1
            video.put()
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
            if video.key not in user.favorites:
                if len(user.favorites) >= user.favorites_limit:
                    self.response.out.write(json.dumps({
                        'error': True,
                        'message': 'You have reached favorites limit.'
                    }))
                    return

                user.favorites.append(video.key)
                user.put()
                self.response.out.write(json.dumps({
                    'message': 'success'
                }))
                video.favors += 1
                video.put()
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
            try:
                user.favorites.remove(video.key)
                user.put()
                self.response.out.write(json.dumps({
                    'message': 'success'
                }))
                video.favors -= 1
                video.put()
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
        key_words_ori = self.request.get('keywords')
        logging.info(key_words_ori)
        self.render('search', {'keywords': key_words_ori})