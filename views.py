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
        path = 'template/' + tempname + '.html'
        template = env.get_template(path)
        self.response.write(template.render(context))

class Home(BaseHandler):
    def get(self):
        logging.info(self.user_info)
        context = {}
        # self.render('index', context)
        
        # template = env.get_template('template/player.html')
        # self.response.write(template.render(context))
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
        username = self.request.get('username')
        email = self.request.get('email')
        password = self.request.get('password')
        password_confirm = self.request.get('password-confirm')
        logging.info(password)
        logging.info(password_confirm)
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
        if not email:
            return {'error': 'email must not be empty!'}
        email = email.strip()
        if not email:
            return {'error': 'email must not be empty!'}
        if re.match(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", email) is None:
            return {'error': 'invalid email format!'}
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
            context = {}
            template = env.get_template('template/signup.html')
            self.response.write(template.render(context))
    
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        res = self.validateSignupForm()
        if res.get('error'):
            self.response.out.write(json.dumps({
                'error': res['error']
            }))
            return

        unique_properties = ['username']
        user_data = self.user_model.create_user(res['username'],
            unique_properties,
            username=res['username'], email=res['email'], password_raw=res['password'], verified=False)
        if not user_data[0]: #user_data is a tuple
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (username, user_data[1])
            # self.render('signup')
            self.response.out.write(json.dumps({
                'error': 'username already exists!'
            }))
            return

        user = user_data[1]
        user_id = user.get_id()
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
    def get(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            context = {'video': video, 'video_id': video_id, 
                        'category': models.Video_Category, 'subcategory': models.Video_SubCategory}
            self.render('video', context)
        else:
            self.response.write('video not found')
            self.response.set_status(404)

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user_info
        if not user:
            self.response.out.write(json.dumps({
                'error': 'not logged in!',
            }))
            return

        raw_url = self.request.get('video-url')
        description = self.request.get('description')
        if not raw_url:
            self.response.out.write(json.dumps({
                'error': 'video url must not be empty!'
            }))
            return
        res = models.Video.parse_url(raw_url)
        logging.info(res)
        if res.get('error'):
            self.response.out.write(json.dumps({
                'error': 'failed to submit video'
            }))
        else:
            video = models.Video(
                url = res['url'],
                vid = res['vid'],
                source = res['source'],
                uploader = user['username'],
                description = description
            )
            video.put()

            self.response.out.write(json.dumps({
                'url': '/video/dt'+ str(video.key().id_or_name())
            }))

class Videolist(BaseHandler):
    def get(self):
        logging.info('hehe')
        self.response.headers['Content-Type'] = 'application/json'
        video_itr = models.Video.all().run()
        videos = []
        for video in video_itr:
            videos.append({
                'url': '/video/dt'+ str(video.key().id_or_name()),
                'vid': video.vid,
                'uploader': video.uploader,
                'created': video.created.strftime("%Y-%m-%d %H:%M:%S")
            });
        self.response.out.write(json.dumps(videos))

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
        user = self.user_info
        if not user:
            self.response.out.write(json.dumps({
                'error': 'not logged in!',
            }))
            return

        video = models.Video.get_by_id(int(video_id))
        if video is not None:
            danmaku = models.Danmaku(
                video = video,
                timestamp = float(self.request.get('timestamp')),
                creator = user['username'],
                content = self.request.get('content')
            )
            danmaku.put()
            
            self.response.out.write(json.dumps({
                'timestamp': danmaku.timestamp,
                'content': danmaku.content,
                'creator': danmaku.creator,
                'created': danmaku.created.strftime("%Y-%m-%d %H:%M:%S")
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
        context = {'category': models.Video_Category, 'subcategory': models.Video_SubCategory}
        self.render('video', context)