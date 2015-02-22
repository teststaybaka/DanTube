from views import *
from google.appengine.api import images
from google.appengine.ext import ndb
import time
import math
from PIL import Image

class Account(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        context = {}
        context['user'] = user.get_statistic_info()
        self.render('account', context)

class ManagePlaylist(BaseHandler):
    @login_required
    def get(self):
        # self.render('manage_playlist')
        self.render('edit_playlist')
        
class Favorites(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        context = {}
        context['user'] = {
            'favorites_counter': len(user.favorites),
            'favorites_limit': user.favorites_limit
        }
        self.render('favorites', context)

    @login_required
    def post(self):
        user = self.user
        self.response.headers['Content-Type'] = 'application/json'
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
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid page size'
            }))
            return

        result = {'error': False}
        result['videos'] = []
        requested_favorites = []

        base = len(user.favorites) - 1 - (page - 1)*page_size;
        for i in range(0, page_size):
            if base - i < 0:
                break
            requested_favorites.append(user.favorites[base - i])

        videos = ndb.get_multi([f.video for f in requested_favorites])
        for i in range(0, len(requested_favorites)):
            video = videos[i]
            video_info = video.get_basic_info()
            video_info['favored_time'] = requested_favorites[i].favored_time.strftime("%Y-%m-%d %H:%M")
            result['videos'].append(video_info)
            
        result['total_pages'] = math.ceil(len(user.favorites)/float(page_size))
        result['total_found'] = len(user.favorites)
        self.response.out.write(json.dumps(result))

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

                video.favors += 1
                video.put()

                video.create_index('videos_by_favors', video.favors)
                uploader = models.User.get_by_id(video.uploader.id())
                uploader.videos_favored += 1
                uploader.put()

                self.response.out.write(json.dumps({
                    'error': False,
                    'message': 'success'
                }))
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
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video selected.'
            }))
            return

        deleted_ids = []
        for i in range(0, len(ids)):
            video_id = ids[i]
            video = models.Video.get_by_id('dt'+video_id)
            if video is None:
                continue

            video_keys = [f.video for f in user.favorites]
            try:
                idx = video_keys.index(video.key)
                user.favorites.pop(idx)
                user.put()
                
                video.favors -= 1
                video.put()
                video.create_index('videos_by_favors', video.favors )

                uploader = models.User.get_by_id(video.uploader.id())
                uploader.videos_favored -= 1
                uploader.put()

                deleted_ids.append(video_id)
            except ValueError:
                continue
                # self.response.out.write(json.dumps({
                #     'error': True,
                #     'message': 'video not favored',
                # }))
        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video removed.'
            }))
            return

        self.response.out.write(json.dumps({
            'error': False, 
            'message': deleted_ids
        }))

class Subscribed(BaseHandler):
    @login_required
    def get(self):
        subscribed_users = ndb.get_multi(self.user.subscriptions)
        context = {'subscribed_users': []}
        for user in subscribed_users:
            context['subscribed_users'].append(user.get_public_info())
        self.render('subscribed_users', context)

class Subscriptions(BaseHandler):
    @login_required
    def get(self):
        self.render('subscriptions')

    @login_required
    def quick(self):
        subscribed_users = ndb.get_multi(self.user.subscriptions)
        context = {'subscribed_users': []}
        for user in subscribed_users:
            context['subscribed_users'].append(user.get_public_info())
        self.render('subscriptions_quick', context)

class History(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        xrequest = self.request.headers.get('X-Requested-With')
        if xrequest and xrequest == 'XMLHttpRequest':
            self.response.headers['Content-Type'] = 'application/json'
            result = {}
            result['videos'] = []
            history = user.history
            l = len(history)
            videos = ndb.get_multi([h.video for h in history])
            for idx, video in enumerate(reversed(videos)):
                video_info = video.get_basic_info()
                uploader = models.User.get_by_id(video.uploader.id())
                video_info['uploader'] = uploader.get_public_info()
                video_info.update({'last_viewed_time': history[l-1-idx].last_viewed_time.strftime("%Y-%m-%d %H:%M")})
                result['videos'].append(video_info)
            self.response.out.write(json.dumps(result))

        else:
            self.render('history')

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
            self.render('notice', {'type':'error', 'notice':"Url not found."})
            return
        
        time_passed = time.mktime(datetime.now().timetuple()) - ts
        if time_passed > 24 * 60 * 60: # 24 hours
            self.user_model.delete_signup_token(user_id, signup_token)
            self.render('notice', {'type':'error', 'notice':"Url has expired. Please make a new request."})
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

        self.render('notice', {'type':'success', 'notice':"Your account %s has been activated!" % (user.email)})

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

class ChangeInfo(BaseHandler):
    @login_required
    def get(self):
        self.render('change_info')

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        user = self.user
        nickname = self.request.get('nickname').strip()
        intro = self.request.get('intro').strip()

        if nickname == user.nickname and intro == user.intro:
            self.response.out.write(json.dumps({'error':True,'message': 'Already applied.'}))
            return

        if nickname != user.nickname:
            nickname = self.user_model.validate_nickname(nickname)
            if not nickname:
                self.response.out.write(json.dumps({'error':True,'message': 'Invalid nickname.'}))
                return
            else:
                user.nickname = nickname

        if len(intro) > 500:
            self.response.out.write(json.dumps({'error':True,'message': 'Intro can\'t exceed 500 characters.'}))
            return
        elif intro != user.intro:
            user.intro = intro

        user.put()
        self.response.out.write(json.dumps({'error':False}))

class ChangeAvatar(BaseHandler):
    @login_required
    def get(self):
        self.render('change_avatar')

    @login_required
    def post(self):
        user = self.user
        self.response.headers['Content-Type'] = 'application/json'

        x0 = int(round(float(self.request.get('x0'))))
        y0 = int(round(float(self.request.get('y0'))))
        width = int(round(float(self.request.get('width'))))
        height = int(round(float(self.request.get('height'))))

        avatar_field = self.request.POST.get('upload-avatar')
        if avatar_field != '':
            try:
                im = Image.open(avatar_field.file)
                # mypalette = frame.getpalette()
                # logging.info(frame.info['duration'])
                # nframes = 0
                # while frame:
                #     frame.putpalette(mypalette)
                #     im = frame
                #     nframes += 1
                #     if nframes > 4:
                #         break;
                #     try:
                #         frame.seek(frame.tell() + 1)
                #     except EOFError:
                #         break;

                output = cStringIO.StringIO()
                if im.mode == "RGBA" or "transparency" in im.info:
                    rgba_im = Image.new("RGBA", (128,128))
                    resized_im = im.crop((x0, y0, x0+width-1, y0+height-1)).resize((128,128), Image.ANTIALIAS)
                    rgba_im.paste(resized_im)
                    new_im = Image.new("RGB", (128,128), (255,255,255))
                    new_im.paste(rgba_im, rgba_im)
                    new_im.save(output, format='jpeg', quality=100)
                else:
                    rgb_im = Image.new("RGB", (128,128))
                    resized_im = im.crop((x0, y0, x0+width-1, y0+height-1)).resize((128,128), Image.ANTIALIAS)
                    rgb_im.paste(resized_im)
                    rgb_im.save(output, format='jpeg', quality=100)
            except Exception, e:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Image crop error.'
                }))
            else:
                output.seek(0)
                form = MultiPartForm()
                # form.add_field('raw_url', raw_url)
                form.add_file('avatarImage', 'avatar.jpg', fileHandle=output)

                # Build the request
                upload_url = models.blobstore.create_upload_url(self.uri_for('avatar_upload', user_id=user.get_id()) )
                # logging.info(upload_url)
                request = urllib2.Request(upload_url)
                request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
                body = str(form)
                request.add_header('Content-type', form.get_content_type())
                request.add_header('Content-length', len(body))
                request.add_data(body)
                # request.get_data()

                if urllib2.urlopen(request).read() == 'error':
                    self.response.out.write(json.dumps({
                        'error': True,
                        'message': 'Image upload error.'
                    }))
                    return
                else:
                    self.response.out.write(json.dumps({'error':False}))
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Image file doesn\'t exist.'
            }))

class AvatarUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    def post(self, user_id):
        user = self.user_model.get_by_id(int(user_id))
        # logging.info(self.request)
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('avatarImage')
        if upload == []:
            self.response.out.write('error')
            # self.response.out.write(json.dumps({'error':True,'message': 'Please select a file.'}))
            return

        uploaded_image = upload[0]
        logging.info("upload content_type:"+uploaded_image.content_type)
        logging.info("upload size:"+str(uploaded_image.size))
        types = uploaded_image.content_type.split('/')
        if types[0] != 'image':
            uploaded_image.delete()
            self.response.out.write('error')
            # self.response.out.write(json.dumps({'error':True,'message': 'File type error.'}))
            return

        if uploaded_image.size > 50*1024*1024:
            uploaded_image.delete()
            self.response.out.write('error')
            # self.response.out.write(json.dumps({'error':True,'message': 'File is too large.'}))
            return

        if user.avatar != None:
            images.delete_serving_url(user.avatar)
            models.blobstore.BlobInfo(user.avatar).delete()
        user.avatar = uploaded_image.key()
        user.put()
        self.response.out.write('success')
        # self.response.out.write(json.dumps({'error':False}))

class SpaceSetting(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    @login_required
    def get(self):
        self.render('space_setting')

    @login_required
    def post(self):
        user = self.user
        self.response.headers['Content-Type'] = 'application/json'

        space_name = self.request.get('space-name').strip()
        file_field = self.request.POST.get('css-file')
        
        if file_field == '' and space_name == user.spacename:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Already applied.'
            }))
            return

        if space_name == '':
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Please enter a name.'
            }))
            return
        elif len(space_name) > 30:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No longer than 30 characters.'
            }))
            return
        elif space_name != user.spacename:
            user.spacename = space_name

        file_key = None
        if file_field != '':
            form = MultiPartForm()
            # form.add_field('raw_url', raw_url)
            form.add_file('user_style', 'user_style.css', fileHandle=file_field.file)

            # Build the request
            upload_url = models.blobstore.create_upload_url(self.uri_for('css_upload'))
            # logging.info(upload_url)
            request = urllib2.Request(upload_url)
            request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
            body = str(form)
            request.add_header('Content-type', form.get_content_type())
            request.add_header('Content-length', len(body))
            request.add_data(body)
            # request.get_data()

            request_res = urllib2.urlopen(request).read()
            if request_res == 'error':
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'CSS upload error.'
                }))
                return
            else:
                 file_key = models.blobstore.BlobKey(request_res)

        if file_key != None:
            if user.css_file != None:
                models.blobstore.BlobInfo(user.css_file).delete()
            user.css_file = file_key

        user.put()
        self.response.out.write(json.dumps({
            'error': False,
        }))

    def css_upload(self):
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('user_style')
        if upload == []:
            self.response.out.write('error')
            return

        uploaded_file = upload[0]
        types = uploaded_file.content_type.split('/')
        if types[1] != 'css':
            uploaded_file.delete()
            self.response.out.write('error')
            return
        
        if uploaded_file.size > 1*1024*1024:
            uploaded_file.delete()
            self.response.out.write('error')
            return

        self.response.out.write(str(uploaded_file.key()))

    @login_required
    def reset(self):
        user = self.user
        self.response.headers['Content-Type'] = 'application/json'

        if user.css_file != None:
            models.blobstore.BlobInfo(user.css_file).delete()
            user.css_file = None

        user.spacename = ''
        user.put()
        self.response.out.write(json.dumps({
            'error': False,
        }))

class SpaceCSS(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = models.blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)
        