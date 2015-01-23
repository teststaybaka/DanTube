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
from webapp2_extras import sessions_ndb
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.api import mail

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
        user = self.user_info
        if user is not None:
            context['is_auth'] = True
            context['nickname'] = user.get('nickname')
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
      self.redirect(self.uri_for('signin'), abort=True)
    else:
      return handler(self, *args, **kwargs)
 
  return check_login

class Home(BaseHandler):
    def get(self):
        self.render('index')

class Logout(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.session['message'] = 'Logout successfully'
    self.redirect(self.uri_for('home'))

class Verification(BaseHandler):
    def get(self, *args, **kwargs):
        user = self.user
        if user:
            if user.verified:
                self.notify('Your account has already been verified.')
                return
                
        user = None
        user_id = int(kwargs['user_id'])
        signup_token = kwargs['signup_token']

        user, ts = self.user_model.get_by_auth_token(user_id, signup_token, 'signup')

        if not user:
          logging.info('Could not find any user with id "%s" and token "%s"', user_id, signup_token)
          self.notify('404 not found.', 404)
          return
     
        current_user = self.user
        if current_user:
            if current_user.get_id() != user_id:
                self.notify('Invalid operation!')
                return
        else:
            # store user data in the session
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
     
        # remove signup token, we don't want users to come back with an old link
        self.user_model.delete_signup_token(user.get_id(), signup_token)
     
        if not user.verified:
            user.verified = True
            user.put()

        notice = "Dear %s, your email %s has been verified, thank you!" % (user.nickname, user.email)
        self.notify(notice)

class SendVerification(BaseHandler):
    @login_required
    def get(self):
        self.render('send_verification', {'verified': self.user.verified})

    @login_required
    def post(self):
        user = self.user
        if user.verified:
            self.render('send_verification', {'verified': True})
            return

        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)
 
        verification_url = self.uri_for('verification', user_id=user_id,
          signup_token=token, _full=True)

        message = mail.EmailMessage(sender="tianfanw@gmail.com",
                            subject="Verficaition Email from DanTube")

        message.to = user.email
        message.body = """
        Dear %s:

        Your verification url is:
        %s
        """ % (user.nickname, verification_url)
        logging.info(message.body)
        message.send()
        self.render('send_verification', {'hint': 'An email has been sent to you to activate your account.'})

class ForgotPassword(BaseHandler):
    def get(self):
        if self.user_info is not None:
            self.redirect(self.uri_for('home'))
            return

        self.render('forgot_password')

    def post(self):
        if self.user_info is not None:
            self.redirect(self.uri_for('home'))
            return
            
        email_or_nickname = self.request.get('email-or-nickname')
        if not email_or_nickname:
            self.render('forgot_password', {'error': 'please enter your email or nickname'})
            return

        user = models.User.query(models.User.auth_ids == email_or_nickname).get()
        if user is None:
            user = models.User.query(models.User.nickname == email_or_nickname).get()
            if user is None:
                self.render('forgot_password', {'error': 'The email or nickname you entered does not exist!'})
                return

        user_id = user.get_id()

        # delete any existing tokens if exist
        # token_model = self.user_model.token_model
        # tokens = token_model.query(token_model.user == user, subject == 'pwdreset').fetch()
        # logging.info(tokens)
        # for token in tokens:
        #     self.user_model.delete_pwdreset_token(user_id, token.token)

        token = self.user_model.create_pwdreset_token(user_id)

        password_reset_url = self.uri_for('forgot_password_reset', user_id=user_id,
            pwdreset_token=token, _full=True)
        message = mail.EmailMessage(sender="tianfanw@gmail.com",
                            subject="Password Reset Email from DanTube")

        message.to = user.email
        message.body = """
        Dear %s:

        Your password reset url is:
        %s
        """ % (user.nickname, password_reset_url)
        logging.info(message.body)
        message.send()

        self.notify('The password reset link has been sent to your email!')

class ForgotPasswordReset(BaseHandler):
    def validateToken(self, user_id, pwdreset_token):
        if self.user:
            self.notify("You are already logged in.")
            return None

        user = None

        user, ts = self.user_model.get_by_auth_token(user_id, pwdreset_token, 'pwdreset')

        if not user:
            logging.info('Could not find any user with id "%s" and token "%s"', user_id, pwdreset_token)
            self.notify('404 not found.', 404)
            return None

        return user

    def validateForm(self):
        new_password = self.request.get('new-password')
        confirm_password = self.request.get('confirm-password')

        if not new_password:
            return {'error': 'New password must not be empty.'}
        if not new_password.strip():
            return {'error': 'new password must not be empty.'}
        if len(new_password) < 6:
            return {'error': 'New password must contain at least 6 letters.'}
        if len(new_password) > 40:
            return {'error': 'New password cannot exceed 40 letters.'}
        if confirm_password != new_password:
            return {'error': 'Your passwords do not match. Please try again.'}

        return {'new_password': new_password}

    def get(self, *args, **kwargs):
        user_id = int(kwargs['user_id'])
        pwdreset_token = kwargs['pwdreset_token']
        user = self.validateToken(user_id, pwdreset_token)
        if user:
            self.render('reset_password', {'has_token': True})


    def post(self, *args, **kwargs):
        user_id = int(kwargs['user_id'])
        pwdreset_token = kwargs['pwdreset_token']
        user = self.validateToken(user_id, pwdreset_token)
        if user:
            res = self.validateForm()
            if res.get('error'):
                self.render('reset_password', {'has_token': True, 'hint': res['error']})
                return

            user.set_password(res['new_password'])
            user.put()
            self.user_model.delete_pwdreset_token(user.get_id(), pwdreset_token)
            self.notify('Your password has been reset, please remember it this time and login again.')

class PasswordReset(BaseHandler):
    def validateForm(self):
        old_password = self.request.get('old-password')
        new_password = self.request.get('new-password')
        confirm_password = self.request.get('confirm-password')

        if not old_password:
            return {'error': 'Please enter your old password.'}
        if not new_password:
            return {'error': 'New password must not be empty.'}
        if not new_password.strip():
            return {'error': 'new password must not be empty.'}
        if len(new_password) < 6:
            return {'error': 'New password must contain at least 6 letters.'}
        if len(new_password) > 40:
            return {'error': 'New password cannot exceed 40 letters.'}
        if confirm_password != new_password:
            return {'error': 'Your passwords do not match. Please try again.'}

        return {'old_password': old_password, 'new_password': new_password}

    @login_required
    def get(self):
        self.render('reset_password')

    @login_required
    def post(self):
        res = self.validateForm()
        if res.get('error'):
            self.render('reset_password', {'hint': res['error']})
            return

        user = self.user
        try:
            self.user_model.get_by_auth_password(user.email, res['old_password'])
            user.set_password(res['new_password'])
            user.put()
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            self.render('reset_password', {'hint': 'Please enter the correct password.'})
            return
        except Exception, e:
            logging.info(e)
            logging.info(type(e))
            self.render('reset_password', {'hint': 'unknown error'})

        self.render('reset_password', {'hint': 'Password reset successfully.'})

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
                        'nickname': uploader.nickname, 
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
                    'created': danmaku.created.strftime("%m-%d %H:%M"),
                    'created_seconds': (danmaku.created - datetime.datetime(1970,1,1)).total_seconds(),
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
                'creator': user.nickname,
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
                'error': True,
                'message': 'Please select a file.',
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
                'error': True,
                'message': 'File type error.',
            }))
            return

        if uploaded_image.size > 50*1000000:
            uploaded_image.delete()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'File is too large.',
            }))
            return

        user = self.user
        if user.avatar != None:
            models.blobstore.BlobInfo(user.avatar).delete()
        user.avatar = uploaded_image.key()
        user.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'message': 'Upload succeeded.',
        }))
