from views import *
from google.appengine.api import images
import time
from PIL import Image

class Account(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        context = {}
        context['user'] = user.get_statistic_info()
        self.render('account', context)

class History(BaseHandler):
    @login_required
    def watch(self):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        context['videos'] = []
        requested_history = []

        base = len(user.history) - 1 - (page - 1)*page_size;
        for i in range(0, page_size):
            if base - i < 0:
                break
            requested_history.append(user.history[base - i])

        videos = ndb.get_multi([f.video for f in requested_history])
        uploader_keys = []
        for i in range(0, len(requested_history)):
            video = videos[i]
            if video is None:
                continue

            video_info = video.get_basic_info()
            video_info['index'] = requested_history[i].clip_index
            uploader_keys.append(video.uploader)
            video_info['last_viewed_time'] = requested_history[i].last_viewed_time.strftime("%Y-%m-%d %H:%M")
            context['videos'].append(video_info)

        uploaders = ndb.get_multi(uploader_keys)
        for i in range(0, len(uploaders)):
            uploader = uploaders[i]
            context['videos'][i]['uploader'] = uploader.get_public_info()

        context.update(self.get_page_range(page, math.ceil(len(user.history)/float(page_size))) )
        self.render('history', context)

    @login_required
    def comment(self):
        user = self.user
        page_size = 20
        page = self.get_page_number()

        context = {}
        context['user'] = user.get_public_info()
        context['comments'] = []

        total_pages = min(10, math.ceil(user.comments_num/float(page_size)))
        if page <= total_pages:
            comment_keys = models.ActivityRecord.query(
                ndb.AND(models.ActivityRecord.creator==user.key, 
                    ndb.OR(models.ActivityRecord.activity_type=='comment', 
                            models.ActivityRecord.activity_type=='inner_comment', 
                            models.ActivityRecord.activity_type=='danmaku'))
            ).order(-models.ActivityRecord.created).fetch(keys_only=True, offset=(page-1)*page_size, limit=page_size)

            comments = ndb.get_multi(comment_keys)
            videos= ndb.get_multi([comment.video for comment in comments])
            for i in range(0, len(comments)):
                comment = comments[i]
                video = videos[i]
                comment_info = {
                    'type': comment.activity_type,
                    'timestamp': comment.timestamp,
                    'floorth': comment.floorth,
                    'inner_floorth': comment.inner_floorth,
                    'video': video.get_basic_info(),
                    'content': comment.content,
                    'created': comment.created.strftime("%Y-%m-%d %H:%M"),
                    'clip_index': comment.clip_index,
                }
                context['comments'].append(comment_info)

        context.update(self.get_page_range(page, total_pages))
        self.render('history_comment', context)

class Favorites(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        context['videos'] = []

        requested_favorites = []
        base = len(user.favorites) - 1 - (page - 1)*page_size;
        for i in range(0, page_size):
            if base - i < 0:
                break
            requested_favorites.append(user.favorites[base - i])

        video_keys = [f.video for f in requested_favorites]
        videos = ndb.get_multi(video_keys)
        for i in range(0, len(requested_favorites)):
            video = videos[i]
            if video is None:
                video_info = {}
                video_info['title'] = 'Video deleted';
                video_info['thumbnail_url'] = '/static/img/video_deleted.png'
                video_info['thumbnail_url_hq'] = '/static/img/video_deleted.png'
                video_info['id_num'] = video_keys[i].id().replace('dt', '')
                video_info['url'] = '/video/'+ video_keys[i].id()
                video_info['category'] = 'None'
                video_info['subcategory'] = 'None'
            else:
                video_info = video.get_basic_info()
            video_info['favored_time'] = requested_favorites[i].favored_time.strftime("%Y-%m-%d %H:%M")
            context['videos'].append(video_info)

        context['favorites_counter'] = len(user.favorites)
        context['favorites_limit'] = user.favorites_limit
        context.update(self.get_page_range(page, math.ceil(len(user.favorites)/float(page_size))) )
        self.render('favorites', context)

class Favor(BaseHandler):
    @login_required_json
    def post(self, video_id):
        user = self.user
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        if video.key in [f.video for f in user.favorites]:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'This video is already one of your favorites.'
            }))
            return

        if len(user.favorites) >= user.favorites_limit:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You have reached the limit for your favorite videos.'
            }))
            return

        new_favorite = models.Favorite(video=video.key)
        user.favorites.append(new_favorite)

        video.favors += 1
        video.last_updated = datetime.now()
        video.create_index('videos_by_favors', video.favors)

        uploader = video.uploader.get()
        uploader.videos_favored += 1

        ndb.put_multi([user, video, uploader])

        self.response.out.write(json.dumps({
            'error': False,
            'favors': video.favors,
        }))         

class Unfavor(BaseHandler):
    @login_required_json
    def post(self):
        user = self.user
        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video selected.'
            }))
            return

        deleted_ids = []
        put_list = []
        uploader_keys = []
        for i in range(0, len(ids)):
            video_id = ids[i]
            # video = models.Video.get_by_id('dt'+video_id)
            video_key = ndb.Key('Video', 'dt'+video_id)
            video_keys = [f.video for f in user.favorites]
            try:
                idx = video_keys.index(video_key)
            except Exception, e:
                continue

            user.favorites.pop(idx)
            deleted_ids.append(video_id)
            video = video_key.get()
            if video is None:
                continue

            video.favors -= 1
            video.create_index('videos_by_favors', video.favors)
            put_list.append(video)
            uploader_keys.append(video.uploader)

        uploaders = ndb.get_multi(uploader_keys)
        for i in range(0, len(uploaders)):
            uploader = uploaders[i]
            uploader.videos_favored -= 1
            put_list.append(uploader)
        
        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video removed.'
            }))
            return
        ndb.put_multi([user] + put_list)

        self.response.out.write(json.dumps({
            'error': False, 
            'message': deleted_ids
        }))

class Subscribed(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        page_size = 20
        page = self.get_page_number()

        context = {}
        context['upers'] = []

        requested_upers = []
        base = len(user.subscriptions) - 1 - (page - 1)*page_size;
        for i in range(0, page_size):
            if base - i < 0:
                break
            requested_upers.append(user.subscriptions[base - i])

        upers = ndb.get_multi(requested_upers)
        for i in range(0, len(upers)):
            uper = upers[i]
            uper_info = uper.get_public_info()
            context['upers'].append(uper_info)

        context['subscription_counter'] = len(user.subscriptions)
        context['subscription_limit'] = 1000
        context.update(self.get_page_range(page, math.ceil(len(user.subscriptions)/float(page_size))) )
        self.render('subscribed_users', context)

class Subscriptions(BaseHandler):
    def new_subscription_count(self):
        user = self.user
        if len(user.subscriptions) > 1:
            operation = ndb.OR(models.ActivityRecord.creator==user.subscriptions[0], models.ActivityRecord.creator==user.subscriptions[1])
            for i in range(2, len(user.subscriptions)):
                operation = ndb.OR(models.ActivityRecord.creator==user.subscriptions[i], operation)
            new_activities = models.ActivityRecord.query(ndb.AND(operation, models.ActivityRecord.public==True, models.ActivityRecord.created > user.last_subscription_check)).count()
        elif len(user.subscriptions) == 1:
            new_activities = models.ActivityRecord.query(ndb.AND(models.ActivityRecord.creator==user.subscriptions[0], models.ActivityRecord.public==True, models.ActivityRecord.created > user.last_subscription_check)).count()
        else:
            new_activities = 0
        return new_activities

    @login_required_json
    def get_count(self):
        new_count = self.new_subscription_count()
        self.response.out.write(json.dumps({
            'error': False,
            'count': models.number_upper_limit_99(new_count),
        }))

    @login_required
    def get_page(self):
        user = self.user
        user.last_subscription_check = datetime.now()
        user.put()
        self.response.set_cookie('new_subscriptions', '', path='/')
        self.render('subscriptions')

    @login_required
    def full_page(self):
        user = self.user
        user.last_subscription_check = datetime.now()
        user.put()
        self.response.set_cookie('new_subscriptions', '', path='/')
        self.render('subscriptions_quick')

    @login_required_json
    def load_activities(self):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE

        result = {'error': False}
        result['activities'] = []

        uploads_only = self.request.get('uploads').strip()
        if uploads_only == '1':
            uploads_only = True
        else:
            uploads_only = False

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        if len(user.subscriptions) > 1:
            condition = ndb.OR(models.ActivityRecord.creator==user.subscriptions[0], models.ActivityRecord.creator==user.subscriptions[1])
            for i in range(2, len(user.subscriptions)):
                condition = ndb.OR(models.ActivityRecord.creator==user.subscriptions[i], condition)
            if uploads_only:
                records, cursor, more = models.ActivityRecord.query(
                    ndb.AND(condition, 
                        models.ActivityRecord.public==True, 
                        ndb.OR(models.ActivityRecord.activity_type=='upload', 
                            models.ActivityRecord.activity_type=='edit')
                        )
                    ).order(-models.ActivityRecord.created, models.ActivityRecord.key).fetch_page(page_size, start_cursor=cursor)
            else:
                records, cursor, more = models.ActivityRecord.query(
                    ndb.AND(condition, 
                        models.ActivityRecord.public==True)
                    ).order(-models.ActivityRecord.created, models.ActivityRecord.key).fetch_page(page_size, start_cursor=cursor)
        elif len(user.subscriptions) == 1:
            if uploads_only:
                records, cursor, more = models.ActivityRecord.query(
                    ndb.AND(models.ActivityRecord.creator==user.subscriptions[0], 
                        models.ActivityRecord.public==True,
                        ndb.OR(models.ActivityRecord.activity_type=='upload', 
                            models.ActivityRecord.activity_type=='edit')
                        )
                    ).order(-models.ActivityRecord.created, models.ActivityRecord.key).fetch_page(page_size, start_cursor=cursor)
            else:
                records, cursor, more = models.ActivityRecord.query(
                    ndb.AND(models.ActivityRecord.creator==user.subscriptions[0], 
                        models.ActivityRecord.public==True)
                    ).order(-models.ActivityRecord.created, models.ActivityRecord.key).fetch_page(page_size, start_cursor=cursor)
        else:
            records = []
            cursor = ''

        videos = ndb.get_multi([record.video for record in records])
        creators = ndb.get_multi([record.creator for record in records])
        for i in range(0, len(records)):
            record = records[i]
            video = videos[i]
            creator = creators[i]
            record_info = {
                'creator': creator.get_public_info(),
                'type': record.activity_type,
                'timestamp': record.timestamp,
                'floorth': record.floorth,
                'inner_floorth': record.inner_floorth,
                'content': record.content,
                'created': record.created.strftime("%Y-%m-%d %H:%M"),
                'video': video.get_basic_info(),
                'clip_index': record.clip_index,
            }
            result['activities'].append(record_info)
        if not cursor:
            result['cursor'] = ''
        else:
            result['cursor'] = cursor.urlsafe()
        
        self.response.out.write(json.dumps(result))

    @login_required_json
    def load_upers(self):
        user = self.user
        page_size = 10
        page = self.get_page_number()

        result = {'error': False}
        result['upers'] = []

        requested_upers = []
        base = len(user.subscriptions) - 1 - (page - 1)*page_size;
        for i in range(0, page_size):
            if base - i < 0:
                break
            requested_upers.append(user.subscriptions[base - i])

        upers = ndb.get_multi(requested_upers)
        for i in range(0, len(upers)):
            uper = upers[i]
            uper_info = uper.get_public_info()
            result['upers'].append(uper_info)

        result['total_pages'] = math.ceil(len(user.subscriptions)/float(page_size))
        self.response.out.write(json.dumps(result))

class Verification(BaseHandler):
    def get(self, user_id, signup_token):
        # user = self.user
        # if user and user.verified:
        #     self.render('verification', {'error':False, 'message':"Your account %s has been activated!" % (user.email)})
        #     return
                
        user = None
        user_id = int(user_id)
        user, ts = self.user_model.get_by_auth_token(user_id, signup_token, 'signup')

        if not user:
            logging.info('Could not find any user with id "%s" and token "%s"', user_id, signup_token)
            self.notify("Url not found.")
            return
        
        time_passed = time.mktime(datetime.now().timetuple()) - ts
        if time_passed > 24 * 60 * 60: # 24 hours
            self.user_model.delete_signup_token(user_id, signup_token)
            self.notify("Url has expired. Please make a new request.")
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
    @login_required_json
    def post(self):
        user = self.user
        if user.verified:
            self.response.out.write(json.dumps({'error':True,'message': 'Your account has been activated.'}))
            return

        user_id = user.get_id()

        token = self.user_model.create_signup_token(user_id)
 
        verification_url = self.uri_for('verification', user_id=user_id,
          signup_token=token, _full=True)

        message = mail.EmailMessage(sender="DanTube Support <dan-tube@appspot.gserviceaccount.com>",
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

    @login_required_json
    def post(self):
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

    @login_required_json
    def post(self):
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

        if len(intro) > 2000:
            self.response.out.write(json.dumps({'error':True,'message': 'Intro can\'t exceed 2000 characters.'}))
            return
        elif intro != user.intro:
            user.intro = intro

        user.create_index()
        user.put()
        self.response.out.write(json.dumps({'error':False}))

class ChangeAvatar(BaseHandler):
    @login_required
    def get(self):
        self.render('change_avatar')

    @login_required_json
    def post(self):
        user = self.user
        try:
            x0 = int(round(float(self.request.get('x0'))))
            y0 = int(round(float(self.request.get('y0'))))
            width = int(round(float(self.request.get('width'))))
            height = int(round(float(self.request.get('height'))))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Crop coordinate error.',
            }))
            return

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

    @login_required_json
    def post(self):
        user = self.user

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

    @login_required_json
    def reset(self):
        user = self.user

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
