from views import *
from google.appengine.api import images
import time
from PIL import Image

class Account(BaseHandler):
    @login_required
    def get(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        context = {'user': user_detail.get_detail_info()}
        self.user = user
        self.render('account')

class History(BaseHandler):
    @login_required
    def get_watch(self):
        self.render('history')

    @login_required_json
    def watch(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        records, cursor, more = models.ViewRecord.query(ancestor=user_key).order(-models.ViewRecord.created).fetch_page(page_size, start_cursor=cursor)
        videos = ndb.get_multi([record.video for record in records])

        context = {
            'videos': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(records)):
            record = records[i]
            video = videos[i]
            if not video:
                video_info = models.Video.get_deleted_video_info()
            else:
                video_info = video.get_basic_info()
            video_info['index'] = record.clip_index
            video_info['last_timestamp'] = record.last_timestamp
            video_info['last_viewed_time'] = record.created.strftime("%Y-%m-%d %H:%M")
            context['videos'].append(video_info)

        self.json_response(False, context)

    @login_required
    def get_comment(self):
        context = {'type': self.request.get('type')}
        self.render('history_comment', context)

    @login_required_json
    def comment(self):
        user_key = self.user_key
        page_size = models.MEDIUM_PAGE_SIZE
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))

        kind = self.request.get('type')
        if kind == 'danmaku':
            records, cursor, more = models.DanmakuRecord.query(ancestor=user_key).order(-models.DanmakuRecord.created).fetch_page(page_size, start_cursor=cursor)
        else:
            records, cursor, more = models.Comment.query(models.Comment.creator==user_key).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)

        context = {
            'comments': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(records)):
            record = records[i]
            video = videos[i]
            comment_info = record.get_content()
            context['comments'].append(comment_info)

        self.json_response(False, context)

class Likes(BaseHandler):
    @login_required
    def get(self):
        self.render('likes')

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        records, cursor, more = models.LikeRecord.query(ancestor=user_key).order(-models.LikeRecord.created).fetch_page(page_size, start_cursor=cursor, projection=['video'])
        videos = ndb.get_multi([record.video for record in records])

        context = {
            'videos': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(records)):
            video = videos[i]
            if not video:
                video_info = models.Video.get_deleted_video_info()
            else:
                video_info = video.get_basic_info()
            context['videos'].append(video_info)

        self.json_response(False, context)

class Unlike(BaseHandler):
    @login_required_json
    def post(self):
        user_key = self.user_key
        try:
            ids = self.get_ids()
        except ValueError:
            self.json_response(True, {'message': 'Invalid id'})
            return

        video_keys = [ndb.Key('Video', identifier) for identifier in ids]
        videos = ndb.get_multi(video_keys)
        records = models.LikeRecord.query(models.LikeRecord.video.IN(video_keys), ancestor=user_key).fetch(keys_only=True)
        put_list = []
        for i in xrange(0, len(records)):
            if record:
                video = videos[i]
                if video:
                    video.likes -= 1
                    video.create_index('videos_by_likes', video.likes) #todo
                    put_list.append(video)
                records[i].delete_async()

        ndb.put_multi_async(put_list)
        self.json_response(False)

class Subscribed(BaseHandler):
    @login_required
    def get(self):
        self.render('subscribed_users')

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.MEDIUM_PAGE_SIZE
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        uper_keys, cursor, more = models.Subscription.query(ancestor=user_key).order(-models.Subscription.score).fetch_page(page_size, start_cursor=cursor, projection=['uper'])
        upers = ndb.get_multi(uper_keys)
        
        context = {
            'upers': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(upers)):
            uper = upers[i]
            uper_info = uper.get_public_info()
            context['upers'].append(uper_info)

        self.json_response(False, context)

class Subscriptions(BaseHandler):
    # @login_required_json
    # def get_count(self):
    #     new_count = self.new_subscription_count()
    #     self.json_response(False,{'count': models.number_upper_limit_99(new_count)})

    @login_required
    def get_page(self):
        self.user = user = self.user_key.get()
        user.new_subscriptions = 0
        user.put_async()
        self.response.set_cookie('new_subscriptions', '', path='/')
        self.render('subscriptions')

    @login_required
    def full_page(self):
        self.user = user = self.user_key.get()
        user.new_subscriptions = 0
        user.put_async()
        self.response.set_cookie('new_subscriptions', '', path='/')
        self.render('subscriptions_quick')

    @login_required_json
    def load_activities(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        uper_keys = models.Subscription.query(ancestor=user_key).order(-models.Subscription.score).fetch(projection=['uper'])
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        videos, cursor, more = models.Video.query(models.Video.uploader.IN(uper_keys)).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
    
        result = {
            'videos': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            result['videos'].append(video_info)

        self.json_response(False, result)

class ChangePassword(BaseHandler):
    @login_required
    def get(self):
        self.render('change_password')

    @login_required_json
    def post(self):
        old_password = self.request.get('cur_password')
        if not old_password:
            self.json_response(True, {'message': 'Please enter your old password.'})
            return

        new_password = self.user_model.validate_password(self.request.get('new_password'))
        if not new_password:
            self.json_response(True, {'message': 'Invalid new password.'})
            return

        user = self.user_key.get()
        try:
            self.user_model.get_by_auth_password(user.email, old_password)
            user.set_password(new_password)
            user.put_async()
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            self.json_response(True, {'message': 'Password incorrect.'})
            return
        except Exception, e:
            logging.info(e)
            self.json_response(True, {'message': e})
            return

        self.json_response(False)

class ChangeInfo(BaseHandler):
    @login_required
    def get(self):
        self.render('change_info')

    @login_required_json
    def post(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        nickname = self.request.get('nickname').strip()
        intro = self.request.get('intro').strip()

        if nickname == user.nickname and intro == user_detail.intro:
            self.json_response(True, {'message': 'Already applied.'})
            return

        if nickname != user.nickname:
            nickname = self.user_model.validate_nickname(nickname)
            if not nickname:
                self.json_response(True, {'message': 'Invalid nickname.'})
                return

            user.nickname = nickname

        if len(intro) > 2000:
            self.json_response(True, {'message': 'Intro can\'t exceed 2000 characters.'})
            return

        user_detail.intro = intro
        user.create_index(intro)
        user.put_async()

        self.json_response(False)

class ChangeAvatar(BaseHandler):
    @login_required
    def get(self):
        self.render('change_avatar')

    @login_required_json
    def post(self):
        try:
            x0 = int(round(float(self.request.get('x0'))))
            y0 = int(round(float(self.request.get('y0'))))
            width = int(round(float(self.request.get('width'))))
            height = int(round(float(self.request.get('height'))))
        except Exception, e:
            self.json_response(True, {'message': 'Crop coordinate error.'})
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
                self.json_response(True, {'message': 'Image crop error.'})
            else:
                output.seek(0)
                form = MultiPartForm()
                # form.add_field('raw_url', raw_url)
                form.add_file('avatarImage', 'avatar.jpg', fileHandle=output)

                # Build the request
                upload_url = models.blobstore.create_upload_url(self.uri_for('avatar_upload', user_id=self.user_key.id()))
                # logging.info(upload_url)
                request = urllib2.Request(upload_url)
                request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
                body = str(form)
                request.add_header('Content-type', form.get_content_type())
                request.add_header('Content-length', len(body))
                request.add_data(body)
                # request.get_data()

                if urllib2.urlopen(request).read() == 'error':
                    self.json_response(True, {'message': 'Image upload error.'})
                else:
                    self.json_response(False)
        else:
            self.json_response(True, {'message': 'Image file doesn\'t exist.'})

class AvatarUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    def post(self, user_id):
        # logging.info(self.request)
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('avatarImage')
        if not upload:
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

        user = self.user_model.get_by_id(int(user_id))
        if user.avatar:
            BlobCollection(blob=user.avatar).put_async()
        user.avatar = uploaded_image.key()
        user.put_async()
        self.response.out.write('success')
        # self.response.out.write(json.dumps({'error':False}))

class SpaceSetting(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    @login_required
    def get(self):
        self.render('space_setting')

    @login_required_json
    def post(self):
        space_name = self.request.get('space-name').strip()
        file_field = self.request.POST.get('css-file')
        user_detail = self.user_detail_key.get()
        
        if file_field == '' and space_name == user_detail.spacename:
            self.json_response(True, {'message': 'Already applied.'})
            return

        if space_name == '':
            self.json_response(True, {'message': 'Please enter a name.'})
            return
        elif len(space_name) > 30:
            self.json_response(True, {'message': 'No longer than 30 characters.'})
            return
        user_detail.spacename = space_name

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
                self.json_response(True, {'message': 'CSS upload error.'})
                return
            else:
                 file_key = models.blobstore.BlobKey(request_res)

        if file_key:
            if user_detail.css_file:
                models.blobstore.BlobInfo(user_detail.css_file).delete()
            user_detail.css_file = file_key

        user_detail.put_async()
        self.json_response(False)

    def css_upload(self):
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('user_style')
        if not upload:
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
        user_detail = self.user_detail_key.get()
        if user_detail.css_file:
            models.blobstore.BlobInfo(user_detail.css_file).delete()
            user_detail.css_file = None

        user_detail.spacename = ''
        user_detail.put_async()
        self.json_response(False)

class SpaceCSS(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = models.blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)
