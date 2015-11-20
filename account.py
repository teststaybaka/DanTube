from views import *
from PIL import Image
from gifimage import writeGifToFile, paletteImage

class Account(BaseHandler):
    @login_required
    def get(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        self.user = user
        context = {'user': user_detail.get_detail_info()}
        self.render('account', context)

class History(BaseHandler):
    @login_required
    def get(self):
        context = {
            'type': self.request.get('type'),
        }
        self.render('history', context)

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))

        kind = self.request.get('type')
        if kind == 'danmaku':
            records, cursor, more = models.DanmakuRecord.query(models.DanmakuRecord.creator==user_key).order(-models.DanmakuRecord.created).fetch_page(page_size, start_cursor=cursor)
        elif kind == 'comment':
            records, cursor, more = models.Comment.query(models.Comment.creator==user_key).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)
        else:
            records, cursor, more = models.ViewRecord.query(models.Subscription.user==user_key).order(-models.ViewRecord.created).fetch_page(page_size, start_cursor=cursor)
            videos = ndb.get_multi([record.video for record in records])

        context = {
            'entries': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(records)):
            record = records[i]
            if kind == 'danmaku' or kind == 'comment':
                comment_info = record.get_content()
                context['entries'].append(comment_info)
            else:
                video = videos[i]
                if record.playlist:
                    video_info = video.get_basic_info(record.playlist.id())
                else:
                    video_info = video.get_basic_info()
                video_info['index'] = record.clip_index
                video_info['timestamp'] = record.timestamp
                video_info['last_viewed_time'] = record.created.strftime("%Y-%m-%d %H:%M")
                context['entries'].append(video_info)

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
        records, cursor, more = models.LikeRecord.query(models.Subscription.user==user_key).order(-models.LikeRecord.created).fetch_page(page_size, start_cursor=cursor, projection=['video', 'created'])
        videos = ndb.get_multi([record.video for record in records])

        context = {
            'videos': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(records)):
            video = videos[i]
            record = records[i]
            video_info = video.get_basic_info()
            video_info['liked'] = record.created.strftime("%Y-%m-%d %H:%M")
            context['videos'].append(video_info)

        self.json_response(False, context)

class Subscribed(BaseHandler):
    @login_required
    def get(self):
        self.render('subscribed_users')

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        subscriptions, cursor, more = models.Subscription.query(models.Subscription.user==user_key).order(-models.Subscription.score).fetch_page(page_size, start_cursor=cursor, projection=['uper'])
        upers = ndb.get_multi([subscription.uper for subscription in subscriptions])
        
        context = {
            'upers': [],
            'cursor': cursor.urlsafe() if more else '',
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
    def get(self):
        self.user = user = self.user_key.get()
        user.new_subscriptions = 0
        user.last_subscription_check = datetime.now()
        user.put()
        self.response.set_cookie('new_subscriptions', '', path='/')

        context = {'kind': self.request.get('type')}
        self.render('subscriptions', context) 

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE
        
        subscriptions = models.Subscription.query(models.Subscription.user==user_key).order(-models.Subscription.score).fetch(projection=['uper'])
        uper_keys = [subscription.uper for subscription in subscriptions]
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        kind = self.request.get('type')
        if uper_keys:
            if kind == 'comments':
                entries, cursor, more = models.Comment.query(ndb.AND(models.Comment.creator.IN(uper_keys), models.Comment.share==True)).order(-models.Comment.created, models.Comment.key).fetch_page(page_size, start_cursor=cursor)
            else:
                entries, cursor, more = models.Video.query(models.Video.uploader.IN(uper_keys)).order(-models.Video.created, models.Video.key).fetch_page(page_size, start_cursor=cursor)
        else:
            entries = []
            more = False
    
        result = {
            'entries': [],
            'cursor': cursor.urlsafe() if more else '',
            'type': kind,
        }
        for i in xrange(0, len(entries)):
            if kind == 'comments':
                comment = entries[i]
                content_info = comment.get_content()
                result['entries'].append(content_info)
            else:
                video = entries[i]
                video_info = video.get_basic_info()
                result['entries'].append(video_info)

        self.json_response(False, result)

class SubscriptionQuick(BaseHandler):
    @login_required
    def get(self):
        self.user = user = self.user_key.get()
        user.new_subscriptions = 0
        user.last_subscription_check = datetime.now()
        user.put()
        self.response.set_cookie('new_subscriptions', '', path='/')

        context = {'kind': self.request.get('type')}
        self.render('subscriptions_quick', context)

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

        new_password = models.User.validate_password(self.request.get('new_password'))
        if not new_password:
            self.json_response(True, {'message': 'Invalid new password.'})
            return

        user = self.user_key.get()
        if not user.auth_password(old_password):
            self.json_response(True, {'message': 'Incorrect password.'})
            return

        user.set_password(new_password)
        user.put()
        self.json_response(False)

class ChangeInfo(BaseHandler):
    @login_required
    def get(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        self.user = user
        context = {'user': user_detail.get_detail_info()}
        self.render('change_info', context)

    @login_required_json
    def post(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        nickname = self.request.get('nickname').strip()
        intro = self.request.get('intro').strip()

        if nickname == user.nickname and intro == user_detail.intro:
            self.json_response(True, {'message': 'Already applied.'})
            return

        if len(intro) > 2000:
            self.json_response(True, {'message': 'Intro can\'t exceed 2000 characters.'})
            return

        if nickname != user.nickname:
            nickname = models.User.validate_nickname(nickname)
            if not nickname:
                self.json_response(True, {'message': 'Invalid nickname.'})
                return

            if not models.User.create_unique('nickname', nickname):
                self.json_response(True, {'message': 'Nickname already exist.'})
                return

            models.User.delete_unique('nickname', user.nickname)
            user.nickname = nickname
            user_detail.nickname = nickname

        user_detail.intro = intro
        user.create_index(intro)
        ndb.put_multi([user, user_detail])

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
        if avatar_field == '':
            self.json_response(True, {'message': 'Image file doesn\'t exist.'})
            return

        try:
            im = Image.open(avatar_field.file)
            bucket_name = 'dantube-avatar'
            if im.mode =='P':
                logging.info(im.info)
                standard_file = gcs.open('/'+bucket_name+'/standard-'+str(self.user_key.id()), 'w', content_type="image/gif", options={'x-goog-acl': 'public-read'})
                small_file = gcs.open('/'+bucket_name+'/small-'+str(self.user_key.id()), 'w', content_type="image/gif", options={'x-goog-acl': 'public-read'})
                seq_standard = []
                seq_small = []
                durations = []
                xys = []
                disposes = []
                i = 0
                # base_im = Image.new("RGB", im.size, (255,255,255))
                # base_im.paste(im)
                try:
                    while 1:
                        nim = Image.new("RGB", im.size, (255,255,255))
                        # nim.paste(base_im)
                        nim.paste(im)
                        nim = nim.crop((x0, y0, x0+width-1, y0+height-1))
                        im_standard = nim.resize((128, 128), Image.NEAREST)
                        im_standard = im_standard.quantize(palette=paletteImage(im.getpalette()))
                        seq_standard.append(im_standard)
                        im_small = nim.resize((64, 64), Image.NEAREST)
                        im_small = im_small.quantize(palette=paletteImage(im.getpalette()))
                        seq_small.append(im_small)
                        # logging.info(im.info)
                        try:
                            durations.append(im.info['duration']/1000.0)
                        except Exception:
                            durations.append(0.1)
                        xys.append((0,0))
                        disposes.append(2)

                        i += 1
                        im.seek(im.tell()+1)
                except EOFError:
                    pass
                
                writeGifToFile(standard_file, seq_standard, durations=durations, loops=0, xys=xys, disposes=disposes)
                writeGifToFile(small_file, seq_small, durations=durations, loops=0, xys=xys, disposes=disposes)
            else:
                standard_file = gcs.open('/'+bucket_name+'/standard-'+str(self.user_key.id()), 'w', content_type="image/jpeg", options={'x-goog-acl': 'public-read'})
                small_file = gcs.open('/'+bucket_name+'/small-'+str(self.user_key.id()), 'w', content_type="image/jpeg", options={'x-goog-acl': 'public-read'})
                if im.mode == "RGBA" or "transparency" in im.info:
                    resized_im = im.crop((x0, y0, x0+width-1, y0+height-1)).resize((128,128), Image.ANTIALIAS)
                    new_im = Image.new("RGB", (128,128), (255,255,255))
                    new_im.paste(resized_im, resized_im)
                    new_im.save(standard_file, format='jpeg', quality=95, optimize=True)
                    new_im = new_im.resize((64, 64), Image.ANTIALIAS)
                    new_im.save(small_file, format='jpeg', quality=95, optimize=True)
                else:
                    resized_im = im.crop((x0, y0, x0+width-1, y0+height-1)).resize((128,128), Image.ANTIALIAS)
                    resized_im.save(standard_file, format='jpeg', quality=95, optimize=True)
                    resized_im = resized_im.resize((64, 64), Image.ANTIALIAS)
                    resized_im.save(small_file, format='jpeg', quality=95, optimize=True)

            standard_file.close()
            small_file.close()
        except Exception, e:
            logging.info(str(e))
            self.json_response(True, {'message': 'Image crop error.'})
            return

        self.json_response(False)

class SpaceSetting(BaseHandler):
    @login_required
    def get(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        self.user = user
        context = {'user': user_detail.get_detail_info()}
        self.render('space_setting', context)

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
        elif len(space_name) > 50:
            self.json_response(True, {'message': 'No longer than 50 characters.'})
            return
        elif user_detail.spacename != space_name:
            user_detail.spacename = space_name
            user_detail.put()

        file_key = None
        if file_field != '':
            css_file = gcs.open('/dantube-css/'+str(self.user_key.id()), 'w', content_type="text/css", options={'x-goog-acl': 'public-read'})
            css_file.write(file_field.file.read())
            css_file.close()

        self.json_response(False)

class SpaceSettingReset(BaseHandler):
    @login_required_json
    def post(self):
        gcs.delete('/dantube-css/'+str(self.user_key.id()))
        user_detail = self.user_detail_key.get()
        user_detail.spacename = ''
        user_detail.put()
        self.json_response(False)
