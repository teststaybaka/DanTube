import jinja2
import logging
import os
import sys
import traceback
import webapp2
import datetime

from jinja2 import Undefined
from webapp2_extras import sessions
from webapp2_extras import auth
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

import models
import json
import urllib2
import urlparse
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
        return self.session_store.get_session(backend="datastore")

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

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
        """
        return self.session_store.get_session()

    def render(self, tempname, context = {}):
        user = self.user_info
        if user is not None:
            context['is_auth'] = True
            context['username'] = user.get('username')
            context['email'] = user.get('email')
        else:
            context['is_auth'] = False
        message = self.session.get('message')
        if message is not None:
            context['message'] = message
            self.session.pop('message')
        context['category'] = models.Video_Category
        context['subcategory'] = models.Video_SubCategory
        path = 'template/' + tempname + '.html'
        template = env.get_template(path)
        self.response.write(template.render(context))

class Home(BaseHandler):
    def get(self):
        self.render('index')

class Signin(BaseHandler):
    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signin')

    def post(self):
        # self.response.headers['Content-Type'] = 'application/json'
        context = {}
        username = self.request.get('username')
        password = self.request.get('password')
        remember = self.request.get('remember')
        logging.info(self.request)
        if not username:
            # self.response.out.write(json.dumps({
            #     'username_error': 'username must not be empty',
            # }))
            context['form_error'] = 'username must not be empty'
            self.render('signin', context)
            return
        if not password:
            # self.response.out.write(json.dumps({
            #     'password_error': 'password must not be empty',
            # }))
            context['form_error'] = 'password must not be empty'
            self.render('signin', context)
            return
        try:
            if remember:
                u = self.auth.get_user_by_password(username, password, remember=True)
            else:
                u = self.auth.get_user_by_password(username, password, remember=False)
            self.session['message'] = 'login success'
            # self.response.out.write(json.dumps({
            #     'success': 'login success',
            # }))
            self.redirect(self.uri_for('home'))
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', username, type(e))
            self.session['message'] = 'login failed'
            # self.response.out.write(json.dumps({
            #     'error': 'invalid username or password',
            # }))
            context['form_error'] = 'invalid username or password'
            context['username_value'] = username
            if remember:
                context['remember'] = 1
            self.render('signin', context)
            
class Signup(BaseHandler):
    def validateSignupForm(self):
        email = self.request.get('email')
        username = self.request.get('username')
        password = self.request.get('password')
        password_confirm = self.request.get('password-confirm')
        logging.info(password)
        logging.info(password_confirm)
        if not email:
            return {'error': 'email must not be empty!'}
        email = email.strip()
        if not email:
            return {'error': 'email must not be empty!'}
        if re.match(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", email) is None:
            return {'error': 'invalid email format!'}
        if not username:
            return {'error': 'username must not be empty!'}
        username = username.strip()
        if not username:
            return {'error': 'username must not be empty!'}
        if len(username) < 8:
            return {'error': 'username must have at least 8 characters!'}
        if len(username) > 20:
            return {'error': 'username can not exceed 20 characters!'}
        if re.match(r"^[a-z|A-Z|0-9|\-|_]*$", username) is None:
            return {'error': 'username can only contain a-z, A-Z, 0-9, underline and dash!'}
        if not password:
            return {'error': 'password must not be empty!'}
        if len(password) < 8:
            return {'error': 'password must have at least 8 characters!'}
        if not password_confirm:
            return {'error': 'password confirmation does not match!'}
        if password_confirm != password:
            return {'error': 'password confirmation does not match!'}
        return {'username': username, 'email': email, 'password': password}

    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signup')
    
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        res = self.validateSignupForm()
        if res.get('error'):
            self.response.out.write(json.dumps({
                'error': res['error']
            }))
            return

        unique_properties = ['email']
        user_data = self.user_model.create_user(res['email'],
            unique_properties,
            username=res['username'], email=res['email'], password_raw=res['password'], verified=False)
        if not user_data[0]: #user_data is a tuple
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (username, user_data[1])
            # self.render('signup')
            self.response.out.write(json.dumps({
                'error': 'email already used!'
            }))
            return

        user = user_data[1]
        user_id = user.get_id()
        u = self.auth.get_user_by_password(res['email'], res['password'], remember=True)
        # self.session['message'] = 'Sign up successfully!'
        # self.redirect(self.uri_for('home'))
        self.response.out.write(json.dumps({
            'success': 'Sign up successfully!'
        }))

class Logout(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.session['message'] = 'Logout successfully'
    self.redirect(self.uri_for('home'))

def login_required(handler):
  """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
  """
  def check_login(self, *args, **kwargs):
    auth = self.auth
    if not auth.get_user_by_session():
      self.redirect(self.uri_for('signin'), abort=True)
    else:
      return handler(self, *args, **kwargs)
 
  return check_login

class Video(BaseHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        category = self.request.get('category')
        subcategory = self.request.get('subcategory')

        try:
            limit = int(self.request.get('limit'))
        except ValueError:
            limit = 50

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
                    videos = models.Video.query(models.Video.category == category, models.Video.subcategory == subcategory).fetch(limit=limit)
                else:
                    videos = models.Video.query(models.Video.category == category).fetch(limit=limit)
            else:
                videos = models.Video.query().fetch(limit=limit)
        except (KeyError, BadValueError) as e:
            self.response.out.write(json.dumps([]))
        except:
            self.response.out.write(json.dumps({'error': 'Failed to retrieve video infos'}))
        else:
            results = []
            for video in videos:
                uploader = models.User.get_by_id(video.uploader.id())
                results.append({
                    'url': '/video/'+ video.key.id(),
                    'vid': video.vid,
                    'uploader': {
                        'username': uploader.username, 
                    },
                    'created': video.created.strftime("%Y-%m-%d %H:%M:%S"),
                    'category': video.category,
                    'subcategory': video.subcategory,
                    'hits': video.hits,
                    'danmaku_counter': video.danmaku_counter
                });
            self.response.out.write(json.dumps(results))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        if user is None:
            self.response.out.write(json.dumps({
                'error': 'not logged in!',
            }))
            return

        raw_url = self.request.get('video-url')
        if not raw_url:
            self.response.out.write(json.dumps({
                'error': 'video url must not be empty!'
            }))
            return

        category = self.request.get('category')
        if not category:
            self.response.out.write(json.dumps({
                'error': 'category must not be empty!',
            }))
            return

        subcategory = self.request.get('subcategory')
        if not subcategory:
            self.response.out.write(json.dumps({
                'error': 'subcategory must not be empty!',
            }))
            return

        title = self.request.get('title')
        if not title:
            self.response.out.write(json.dumps({
                'error': 'title must not be empty!',
            }))
            return

        description = self.request.get('description')
        if not description:
            self.response.out.write(json.dumps({
                'error': 'description must not be empty!',
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
                'error': str(e)
            }))
        else:
            self.response.out.write(json.dumps({
                'url': '/video/'+ video.key.id()
            }))

class Watch(BaseHandler):
    def get(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            context = {'video': video, 'video_id': video_id}
            self.render('video', context)
        else:
            self.response.write('video not found')
            self.response.set_status(404)

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
                    'created': danmaku.created.strftime("%m-%d %H:%M")
                });
            self.response.out.write(json.dumps(danmakus))
        else:
            self.response.out.write(json.dumps({
                'error': 'video not found',
            }))

    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        if user is None:
            self.response.out.write(json.dumps({
                'error': 'not logged in!',
            }))
            return

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
                'creator': user.username,
                'created': danmaku.created.strftime("%m-%d %H:%M")
            }))
        else:
            self.response.out.write(json.dumps({
                'error': 'video not found',
            }))

class Submit(BaseHandler):

    @login_required
    def get(self):
        self.render('submit')

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
        self.render('subcategory', context)

class AvatarSetting(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        context = {}
        if user.avatar:
            avatar_url = images.get_serving_url(user.avatar)
            context['avatar_url'] = avatar_url
        self.render('avatar_setting', context)

class AvatarUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    @login_required
    def get(self):
        upload_url = models.blobstore.create_upload_url('/settings/avatar/upload')
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({'url': upload_url}))

    @login_required
    def post(self):
        logging.info(self.request)
        upload = self.get_uploads('upload-avatar')  # 'file' is file upload field in the form
        if upload == []:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'error': 'Please select a file.',
            }))
            return

        uploaded_image = upload[0]
        logging.info("upload content_type:"+uploaded_image.content_type)
        logging.info("upload size:"+str(uploaded_image.size))
        types = uploaded_image.content_type.split('/')
        if types[0] != 'image':
            uploaded_image.delete()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'error': 'File type error.',
            }))
            return

        if uploaded_image.size > 50*1000000:
            uploaded_image.delete()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'error': 'File is too large.',
            }))
            return

        user = self.user
        if user.avatar != None:
            models.blobstore.BlobInfo(user.avatar).delete()
        user.avatar = uploaded_image.key()
        user.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'success': 'Upload succeeded.',
        }))