from views import *
from google.appengine.api import images
from google.appengine.ext import ndb
import time

class Account(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        context = {}
        context['user'] = user.get_statistic_info()
        self.render('account', context);

class ManageVideo(BaseHandler):
    @login_required
    def get(self):
        videos = models.Video.query(models.Video.uploader==self.user.key).fetch()
        context = {'videos': []}
        for video in videos:
            context['videos'].append(video.get_basic_info())
        self.render('manage_video', context)

class Favorites(BaseHandler):
    @login_required
    def get(self):
        videos = ndb.get_multi(self.user.favorites)
        context = {'videos': []}
        for video in videos:
            context['videos'].append(video.get_basic_info())
        self.render('favorites', context)

class Subscriptions(BaseHandler):
    @login_required
    def get(self):
        subscribed_users = ndb.get_multi(self.user.subscriptions)
        context = {'subscribed_users': []}
        for user in subscribed_users:
            context['subscribed_users'].append(user.get_public_info())
        self.render('subscriptions', context)

class History(BaseHandler):
    @login_required
    def get(self):
        history = self.user.history
        l = len(history)
        videos = ndb.get_multi([h.video for h in history])
        context = {'videos': []}
        for idx, video in enumerate(reversed(videos)):
            video_info = video.get_basic_info()
            video_info.update({'last_viewed_time': history[l-1-idx].last_viewed_time.strftime("%Y-%m-%d %H:%M")})
            context['videos'].append(video_info)
        self.render('history', context)

class Verification(BaseHandler):
    def get(self, *args, **kwargs):
        # user = self.user
        # if user and user.verified:
        #     self.render('verification', {'error':False, 'message':"Your account %s has been activated!" % (user.email)})
        #     return
                
        user = None
        user_id = int(kwargs['user_id'])
        signup_token = kwargs['signup_token']

        user, ts = self.user_model.get_by_auth_token(user_id, signup_token, 'signup')

        if not user:
          logging.info('Could not find any user with id "%s" and token "%s"', user_id, signup_token)
          self.render('verification', {'error':True, 'message':"Url not found."})
          return
        
        time_passed = time.mktime(datetime.now().timetuple()) - ts
        if time_passed > 24 * 60 * 60: # 24 hours
            self.user_model.delete_signup_token(user_id, signup_token)
            self.render('verification', {'error':True, 'message':"Url has expired. Please make a new request."})
            return

        # current_user = self.user
        # if current_user:
        #     if current_user.get_id() != user_id:
        #         self.render('verification', {'error':True, 'message':"Invalid operation!"})
        #         self.notify('Invalid operation!')
        #         return
        # else:
        #     # store user data in the session
        #     self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
     
        # remove signup token, we don't want users to come back with an old link
        self.user_model.delete_signup_token(user.get_id(), signup_token)
     
        if not user.verified:
            user.verified = True
            user.put()

        self.render('verification', {'error':False, 'message':"Your account %s has been activated!" % (user.email)})

class SendVerification(BaseHandler):
    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        if user.verified:
            self.response.out.write(json.dumps({'error':True,'message': 'Your account has been activated.'}))
            return

        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)
 
        verification_url = self.uri_for('verification', user_id=user_id,
          signup_token=token, _full=True)

        message = mail.EmailMessage(sender="DanTube Support <tianfanw@gmail.com>",
                            subject="Verficaition Email from DanTube")

        message.to = user.email
        message.body = """
        Dear %s:

        Please use the following url to activate your account:
        %s
        """ % (user.nickname, verification_url)
        logging.info(message.body)
        message.send()
        self.response.out.write(json.dumps({'error':False}))

class ChangePassword(BaseHandler):
    @login_required
    def get(self):
        self.render('change_password')

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        old_password = self.request.get('cur_password')
        if not old_password:
            self.response.out.write(json.dumps({'error':True,'message': 'Please enter your old password.'}))
            return

        new_password = self.user_model.validate_password(self.request.get('new_password'))
        if not new_password:
            self.response.out.write(json.dumps({'error':True,'message': 'Invalid new password.'}))
            return

        user = self.user
        try:
            self.user_model.get_by_auth_password(user.email, old_password)
            user.set_password(new_password)
            user.put()
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            self.response.out.write(json.dumps({'error':True,'message': 'Password incorrect.'}))
            return
        except Exception, e:
            logging.info(e)
            logging.info(type(e))
            self.response.out.write(json.dumps({'error':True,'message': e}))
            return

        self.response.out.write(json.dumps({'error':False}))

class ChangeNickname(BaseHandler):
    @login_required
    def get(self):
        self.render('change_nickname')

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        user = self.user
        nickname = self.request.get('nickname')
        if nickname != self.user.nickname:
            nickname = self.user_model.validate_nickname(nickname)
            if not nickname:
                self.response.out.write(json.dumps({'error':True,'message': 'Invalid nickname.'}))
                return
        else:
            self.response.out.write(json.dumps({'error':True,'message': 'Already applied.'}))
            return

        try:
            user.nickname = nickname
            user.put()
        except Exception, e:
            logging.info(e)
            logging.info(type(e))
            self.response.out.write(json.dumps({'error':True,'message': e}))
            return 

        self.response.out.write(json.dumps({'error':False}))

class ChangeAvatar(BaseHandler):
    @login_required
    def get(self):
        self.render('change_avatar')

class AvatarUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    @login_required
    def get(self):
        upload_url = models.blobstore.create_upload_url('/account/avatar/upload')
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({'error':False,'url': upload_url}))

    def post(self):
        logging.info(self.request)
        self.response.headers['Content-Type'] = 'application/json'
        upload = self.get_uploads('upload-avatar')
        if upload == []:
            self.response.out.write(json.dumps({'error':True,'message': 'Please select a file.'}))
            return

        uploaded_image = upload[0]
        logging.info("upload content_type:"+uploaded_image.content_type)
        logging.info("upload size:"+str(uploaded_image.size))
        types = uploaded_image.content_type.split('/')
        if types[0] != 'image':
            uploaded_image.delete()
            self.response.out.write(json.dumps({'error':True,'message': 'File type error.'}))
            return

        if uploaded_image.size > 50*1024*1024:
            uploaded_image.delete()
            self.response.out.write(json.dumps({'error':True,'message': 'File is too large.'}))
            return

        user = self.user
        if user.avatar != None:
            images.delete_serving_url(user.avatar)
            models.blobstore.BlobInfo(user.avatar).delete()
        user.avatar = uploaded_image.key()
        user.put()
        self.response.out.write(json.dumps({'error':False}))
