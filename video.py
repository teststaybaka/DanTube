from views import *
from watch import Danmaku, Subtitles
from PIL import Image
from google.appengine.api import images
import urlparse

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
YOUTUBE_API_KEY = "AIzaSyBbf3cs6Nw483po40jw7hZLejmdrgwozWc"
ISO_8601_period_rx = re.compile(
    'P'   # designates a period
    '(?:(?P<years>\d+)Y)?'   # years
    '(?:(?P<months>\d+)M)?'  # months
    '(?:(?P<weeks>\d+)W)?'   # weeks
    '(?:(?P<days>\d+)D)?'    # days
    '(?:T' # time part must begin with a T
    '(?:(?P<hours>\d+)H)?'   # hourss
    '(?:(?P<minutes>\d+)M)?' # minutes
    '(?:(?P<seconds>\d+)S)?' # seconds
    ')?'   # end of time part
)

def ISO_8601_to_seconds(duration):
    d = ISO_8601_period_rx.match(duration).groupdict()
    days = 0
    if d['years']:
        days += int(d['years']) * 365
    if d['months']:
        days += int(d['month']) * 30
    if d['weeks']:
        days += int(d['weeks']) * 7
    if d['days']:
        days += int(d['days'])
    seconds = days * 24 * 60 * 60
    if d['hours']:
        seconds += int(d['hours']) * 60 * 60
    if d['minutes']:
        seconds += int(d['minutes']) * 60
    if d['seconds']:
        seconds += int(d['seconds'])

    return seconds

def video_author_required(handler):
    def check_author(self, video_id):
        user, video, clip_list = ndb.get_multi([self.user_key, ndb.Key('Video', video_id), models.VideoClipList.get_key(video_id)])
        self.user = user
        if not video or video.deleted or video.uploader != user.key:
            self.notify('You are not allowed to edit this video.')
            return

        return handler(self, video, clip_list)

    return check_author

class CoverUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('coverImage')
        if not upload:
            self.response.out.write('error')
            return

        uploaded_image = upload[0]
        logging.info("upload content_type:"+uploaded_image.content_type)
        logging.info("upload size:"+str(uploaded_image.size))
        types = uploaded_image.content_type.split('/')
        if types[0] != 'image':
            uploaded_image.delete()
            self.response.out.write('error')
            return
        
        if uploaded_image.size > 50*1024*1024:
            uploaded_image.delete()
            self.response.out.write('error')
            return

        self.response.out.write(str(uploaded_image.key()))

class VideoUpload(BaseHandler):
    @login_required
    def submit(self):
        self.render('submit_multi')

    @login_required
    @video_author_required
    def edit(self, video, clip_list):
        clips = ndb.get_multi(clip_list.clips)
        context = {
            'video': video.get_full_info(),
            'clips': [],
        }
        for i in xrange(0, len(clips)):
            clip = clips[i]
            clip_info = {
                'index': i,
                'title': clip_list.titles[i],
                'raw_url': clip.raw_url,
                'subintro': clip.subintro,
                'source': clip.source,
            }
            context['clips'].append(clip_info)

        self.render('edit_video', context)

    def field_check(self):
        self.title = self.request.get('total-title').strip()
        if not self.title:
            raise Exception('Title must not be empty!')
        elif models.ILLEGAL_REGEX.match(self.title):
            raise Exception('Title contains illegal characters.')
        elif len(self.title) > 400:
            raise Exception('Title is too long!')

        self.category = self.request.get('category')
        self.subcategory = self.request.get('subcategory')
        if not ((self.category in models.Video_Category) and (self.subcategory in models.Video_SubCategory[self.category])):
            raise Exception('Category invalid!')

        self.intro = self.request.get('description').strip()
        if not self.intro:
            raise Exception('Description must not be empty!')
        elif len(self.intro) > 2000:
            raise Exception('Description is too long!')

        self.video_type = self.request.get('video-type-option')
        if not self.video_type:
            raise Exception('Video type must not be empty!')

        self.tags_ori = self.request.get('tags').split(',')
        self.tags = []
        for i in xrange(0, len(self.tags_ori)):
            tag = self.tags_ori[i].strip()
            if tag and tag not in models.Video_Type:
                if len(tag) > 100:
                    raise Exception('Tags are too long!')
                elif models.ILLEGAL_REGEX.match(tag):
                    raise Exception('Tags have illegal letters!')
                self.tags.append(tag)
        if len(self.tags) == 0:
            raise Exception('Tags must not be empty!')
        elif len(self.tags) > 10:
            raise Exception('Too many tags!')

        self.allow_tag_add = bool(self.request.get('allow-add'))

        self.durations = []
        self.vids = []
        self.sources = self.request.POST.getall('source[]')
        self.raw_urls = self.request.POST.getall('video-url[]')
        if len(self.raw_urls) == 0:
            raise Exception('You must submit at least one video!')
        elif len(self.raw_urls) > 500:
            raise Exception('Too many parts!')

        for i in xrange(0, len(self.raw_urls)):
            self.raw_urls[i] = self.raw_urls[i].strip();
            raw_url = self.raw_urls[i]
            if not raw_url:
                raise Exception('invalid url:'+str(i))
            else:
                try:
                    res = models.VideoClip.parse_url(raw_url, self.sources[i])
                except Exception:
                    raise Exception('invalid url:'+str(i))

                youtube_api_url = YOUTUBE_API_URL + '/videos?key=' + YOUTUBE_API_KEY + '&id=' + res['vid'] + '&part=contentDetails'
                if i == 0:
                    youtube_api_url += ',snippet'
                vlist = json.load(urllib2.urlopen(youtube_api_url))['items']
                if not vlist:
                    raise Exception('invalid url:'+str(i))

                self.vids.append(res['vid'])
                vinfo = vlist[0]
                duration = ISO_8601_to_seconds(vinfo['contentDetails']['duration'])
                self.durations.append(duration)
                if i == 0:
                    self.default_thumbnail = res['vid']
                    thumbnails = vinfo['snippet']['thumbnails']
                    if thumbnails.get('maxres'):
                        self.default_thumbnail += '/maxres'
                    elif thumbnails.get('standard'):
                        self.default_thumbnail += '/sd'
                    elif thumbnails.get('high'):
                        self.default_thumbnail += '/hq'
                    else:
                        self.default_thumbnail += '/mq'

        self.clip_titles = self.request.POST.getall('sub-title[]')
        for i in xrange(0, len(self.clip_titles)):
            self.clip_titles[i] = self.clip_titles[i].strip()
            if models.ILLEGAL_REGEX.match(self.clip_titles[i]):
                raise Exception('Sub title contains illegal characters.')
            elif len(self.clip_titles[i]) > 400:
                raise Exception('Sub title too long!')

        self.subintros = self.request.POST.getall('sub-intro[]')
        for i in xrange(0, len(self.subintros)):
            self.subintros[i] = self.subintros[i].strip()
            if len(self.subintros[i]) > 2000:
                raise Exception('Sub intro too long!')

        self.indices = self.request.POST.getall('index[]')
        for i in xrange(0, len(self.indices)):
            try:
                self.indices[i] = int(self.indices[i].strip())
            except Exception, e:
                raise Exception('Index error.')

    def upload_default_thumbnail(self, video_id):
        try:
            im = Image.open(cStringIO.StringIO(urllib2.urlopen('http://img.youtube.com/vi/'+self.default_thumbnail+'default.jpg').read()))
            bucket_name = 'dantube-thumbnail'
            large_file = gcs.open('/'+bucket_name+'/large-'+video_id, 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
            standard_file = gcs.open('/'+bucket_name+'/standard-'+video_id, 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
            resized_im = im.resize((512,288), Image.ANTIALIAS)
            resized_im.save(large_file, format='jpeg', quality=90, optimize=True)
            resized_im = resized_im.resize((208,117), Image.ANTIALIAS)
            resized_im.save(standard_file, format='jpeg', quality=90, optimize=True)
            large_file.close()
            standard_file.close()
        except Exception:
            logging.info('Image process failed')
            raise Exception('Image process failed.')

    def upload_thumbnail(self, video_id):
        try:
            im = Image.open(self.thumbnail_field.file)
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
            bucket_name = 'dantube-thumbnail'
            large_file = gcs.open('/'+bucket_name+'/large-'+video_id, 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
            standard_file = gcs.open('/'+bucket_name+'/standard-'+video_id, 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})

            if im.mode == "RGBA" or "transparency" in im.info:
                resized_im = im.resize((512,288), Image.ANTIALIAS)
                new_im = Image.new("RGB", (512,288), (255,255,255))
                new_im.paste(rgba_im, rgba_im)
                new_im.save(large_file, format='jpeg', quality=90, optimize=True)
                new_im = new_im.resize((208,117), Image.ANTIALIAS)
                new_im.save(standard_file, format='jpeg', quality=90, optimize=True)
            else:
                resized_im = im.resize((512,288), Image.ANTIALIAS)
                resized_im.save(large_file, format='jpeg', quality=90, optimize=True)
                resized_im = resized_im.resize((208,117), Image.ANTIALIAS)
                resized_im.save(standard_file, format='jpeg', quality=90, optimize=True)

            large_file.close()
            standard_file.close()
        except Exception, e:
            logging.info('Image process failed')
            raise Exception('Image process failed.')

    @login_required_json
    def submit_post(self):
        try:
            self.field_check()
        except Exception, e:
            self.json_response(True, {'message': str(e)})
            return

        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        try:
            video = models.Video.Create(
                user=user,
                intro=self.intro,
                title=self.title,
                category=self.category,
                subcategory=self.subcategory,
                video_type=self.video_type,
                duration=sum(self.durations),
                tags=self.tags,
                allow_tag_add=self.allow_tag_add,
            )
        except TransactionFailedError:
            logging.error('Video submitted failed!!!')
            self.json_response(True, {'message': 'Video uploading error. Please try again.'})
            return

        try:
            self.thumbnail_field = self.request.POST.get('thumbnail')
            if self.thumbnail_field != '':
                self.upload_thumbnail(video.key.id())
            else:
                self.upload_default_thumbnail(video.key.id())
        except Exception, e:
            pass

        video_clips = []
        for i in xrange(0, len(self.raw_urls)):
            video_clip = models.VideoClip(
                uploader=user.key,
                title=self.clip_titles[i],
                index=i,
                parent=video.key,
                subintro=self.subintros[i],
                duration=self.durations[i],
                raw_url=self.raw_urls[i],
                source=self.sources[i],
                vid=self.vids[i]
            )
            video_clips.append(video_clip)
        ndb.put_multi(video_clips)

        clip_list = models.VideoClipList(key=models.VideoClipList.get_key(video.key.id()))
        clip_list.clips = [clip.key for clip in video_clips]
        clip_list.titles = self.clip_titles

        user_detail.videos_submitted += 1
        subscriptions = models.Subscription.query(models.Subscription.uper==self.user_key).fetch(keys_only=True)
        subscribers = ndb.get_multi([subscription.parent() for subscription in subscriptions])
        subscribers_put = []
        for i in xrange(0, len(subscribers)):
            subscriber = subscribers[i]
            if not subscriber.check_new_subscription:
                subscriber.check_new_subscription = True
                subscribers_put.append(subscriber)

        ndb.put_multi([user_detail, clip_list] + subscribers_put)
        self.json_response(False)

    @login_required_json
    def edit_post(self, video_id):
        video, clip_list = ndb.get_multi([ndb.Key('Video', video_id), models.VideoClipList.get_key(video_id)])
        if not video or video.deleted or video.uploader != self.user_key:
            self.json_response(True, {'message': 'You are not allowed to edit this video.'})
            return

        self.allow_post = bool(self.request.get('allow-post'))
        try:
            self.field_check()
            self.thumbnail_field = self.request.POST.get('thumbnail')
            if self.thumbnail_field != '':
                self.upload_thumbnail(video.key.id())
        except Exception, e:
            self.json_response(True, {'message': str(e)})
            return

        reindex = False
        changed = False
        if video.title != self.title:
            video.title = self.title
            reindex = True
            changed = True

        if video.intro != self.intro:
            video.intro = self.intro
            reindex = True
            changed = True

        if video.category != self.category:
            video.category = self.category
            reindex = True
            changed = True

        if video.subcategory != self.subcategory:
            video.subcategory = self.subcategory
            reindex = True
            changed = True

        if video.video_type != self.video_type:
            video.video_type = self.video_type
            changed = True

        if video.tags != self.tags:
            video.tags = self.tags
            reindex = True
            changed = True

        if video.allow_tag_add != self.allow_tag_add:
            video.allow_tag_add = self.allow_tag_add
            changed = True

        ori_clips = ndb.get_multi(clip_list.clips)
        new_clips = []
        put_clips = []
        used_clips = set()
        video_duration = 0
        for i in xrange(0, len(self.indices)):
            index = self.indices[i]
            if index != -1:
                clip_changed = False
                clip = ori_clips[index]

                if clip.title != self.clip_titles[i]:
                    clip.title = self.clip_titles[i]
                    clip_changed = True
                if clip.index != i:
                    clip.index = i
                    clip_changed = True
                if clip.subintro != self.subintros[i]:
                    clip.subintro = self.subintros[i]
                    clip_changed = True
                if clip.raw_url != self.raw_urls[i]:
                    clip.raw_url = self.raw_urls[i]
                    clip_changed = True
                if clip.source != self.sources[i]:
                    clip.source = self.sources[i]
                    clip_changed = True
                if clip.vid != self.vids[i]:
                    clip.vid = self.vids[i]
                    clip_changed = True
                if clip.duration != self.durations[i]:
                    clip.duration = self.durations[i]
                    clip_changed = True

                video_duration += clip.duration
                used_clips.add(index)
                new_clips.append(clip)
                if clip_changed:
                    put_clips.append(clip)
                    changed = True
            else:
                clip = models.VideoClip(
                    uploader=self.user_key,
                    title=self.clip_titles[i],
                    index=i,
                    parent=video.key,
                    subintro=self.subintros[i],
                    duration=self.durations[i],
                    raw_url=self.raw_urls[i],
                    source=self.sources[i],
                    vid=self.vids[i]
                )
                video_duration += clip.duration
                new_clips.append(clip)
                put_clips.append(clip)
                changed = True

        if not changed:
            if self.thumbnail_field != '':
                self.json_response(False)
            else:
                self.json_response(True, {'message': 'Nothing changed.'})
            return

        ndb.put_multi(put_clips)
        for i in xrange(0, len(ori_clips)):
            if i not in used_clips:
                ori_clips[i].Delete()
                
        clip_list.clips = [clip.key for clip in new_clips]
        clip_list.titles = self.clip_titles

        subscribers_put = []
        if self.allow_post:
            video.created = datetime.now()
            subscriptions = models.Subscription.query(models.Subscription.uper==self.user_key).fetch(keys_only=True)
            subscribers = ndb.get_multi([subscription.parent() for subscription in subscriptions])
            subscribers_put = []
            for i in xrange(0, len(subscribers)):
                subscriber = subscribers[i]
                if not subscriber.check_new_subscription:
                    subscriber.check_new_subscription = True
                    subscribers_put.append(subscriber)

        video.duration = video_duration
        ndb.put_multi([video, clip_list] + subscribers_put)

        if reindex:
            video.create_index('videos_by_created', models.time_to_seconds(video.created))
            video.create_index('videos_by_hits', video.hits)
            video.create_index('videos_by_likes', video.likes)
        elif self.allow_post:
            video.create_index('videos_by_created', models.time_to_seconds(video.created))

        self.json_response(False)

class AddTag(BaseHandler):
    @login_required_json
    def post(self, video_id):
        video = models.Video.get_by_id(video_id)
        if not video or video.deleted:
            self.json_response(True, {'message': 'Video not found.'})
            return

        if not video.allow_tag_add:
            self.json_response(True, {'message': 'You are not allowed to add more tags to this video.'})
            return

        new_tag = self.request.get('new-tag').strip()
        if not new_tag:
            self.json_response(True, {'message': 'Empty tag.'})
            return
        elif len(new_tag) > 100:
            self.json_response(True, {'message': 'Tag too long.'})
            return
        elif models.ILLEGAL_REGEX.match(new_tag):
            self.json_response(True, {'message': 'Tag has illegal letters.'})
            return
        elif new_tag in video.tags or new_tag in models.Video_Type:
            self.json_response(True, {'message': 'Tag already existed.'})
            return

        if len(video.tags) >= 10:
            self.json_response(True, {'message': 'Can not add more tags.'})
            return

        video.tags.append(new_tag)
        video.put()
        video.create_index('videos_by_created', models.time_to_seconds(video.created))
        video.create_index('videos_by_hits', video.hits)
        video.create_index('videos_by_likes', video.likes)
        
        self.json_response(False)

class DeleteVideo(BaseHandler):
    @login_required_json
    def post(self):
        try:
            ids = self.get_ids()
        except ValueError:
            self.json_response(True, {'message': 'Invalid id.'})
            return

        im = Image.open(cStringIO.StringIO(urllib2.urlopen(self.request.host_url+'/static/img/video_deleted.png').read()))
        resized_im = im.resize((208,117), Image.ANTIALIAS)
        bucket_name = 'dantube-thumbnail'

        videos = ndb.get_multi([ndb.Key('Video', identifier) for identifier in ids])
        deleted_counter = 0
        for i in xrange(0, len(ids)):
            video = videos[i]
            if not video or video.deleted or video.uploader != self.user_key:
                continue

            video.Delete()
            deleted_counter += 1

            large_file = gcs.open('/'+bucket_name+'/large-'+video.key.id(), 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
            standard_file = gcs.open('/'+bucket_name+'/standard-'+video.key.id(), 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
            im.save(large_file, format='png', optimize=True)
            resized_im.save(standard_file, format='png', optimize=True)
            large_file.close()
            standard_file.close()

        user_detail = self.user_detail_key.get()
        user_detail.videos_submitted -= deleted_counter
        user_detail.put()
        self.json_response(False)

class ManageVideo(BaseHandler):
    @login_required
    def get(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        self.user = user
        context = {
            'user': user_detail.get_detail_info(),
            'video_order': self.request.get('order'),
            'video_keywords': self.get_keywords(),
        }
        self.render('manage_video', context)

    @login_required
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        order = self.request.get('order')
        keywords = self.get_keywords()
        res = re.match(r'dt\d+', keywords)
        if res:
            video_id = res.group(0)
            video = models.Video.get_by_id(video_id)
            if video and video.uploader == user_key:
                videos = [video]
            else:
                videos = []
            context = {
                'total_found': 1,
                'cursor': '',
            }
        elif order == 'hits' or order == 'likes' or keywords:
            if order == 'hits':
                index_name = 'videos_by_hits'
            elif order == 'likes':
                index_name = 'videos_by_likes'
            else:
                index_name = 'videos_by_created'

            if keywords:
                query_string = 'content: ' + keywords + ' AND uper: "' + str(user_key.id()) + '"'
            else:
                query_string = 'uper: "' + str(user_key.id()) + '"'

            try:
                context, videos = self.search(query_string, index_name, page_size)
            except Exception, e:
                self.json_response(True, 'Search error.')
                return
        else:
            cursor = models.Cursor(urlsafe=self.request.get('cursor'))
            videos, cursor, more = models.Video.query(models.Video.uploader==user_key).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
            context = {'cursor': cursor.urlsafe() if more else ''}

        context['videos'] = []
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            if video.playlist_belonged:
                playlist = video.playlist_belonged.get()
                video_info['playlist'] = playlist.get_info()
            context['videos'].append(video_info)

        self.json_response(False, context)

class ManageDanmaku(BaseHandler):
    @login_required
    @video_author_required
    def get(self, video, clip_list):
        context = video.get_basic_info()
        context = {
            'id': video.key.id(),
            'video_url': models.Video.get_video_url(video.key.id()),
            'title': video.title,
            'clips': [],
        }

        clips = ndb.get_multi(clip_list.clips)
        put_list = []
        for i in xrange(0, len(clips)):
            clip = clips[i]
            if clip.refresh:
                danmaku_num = 0
                danmaku_pools = ndb.get_multi(clip.danmaku_pools)
                for danmaku_pool in danmaku_pools:
                    danmaku_num += len(danmaku_pool.danmaku_list)
                clip.danmaku_num = danmaku_num

                advanced_danmaku_num = 0
                if clip.advanced_danmaku_pool:
                    advanced_danmaku_pool = clip.advanced_danmaku_pool.get()
                    advanced_danmaku_num += len(advanced_danmaku_pool.danmaku_list)
                clip.advanced_danmaku_num = advanced_danmaku_num

                code_danmaku_num = 0
                if clip.code_danmaku_pool:
                    code_danmaku_pool = clip.code_danmaku_pool.get()
                    code_danmaku_num += len(code_danmaku_pool.danmaku_list)
                clip.code_danmaku_num = code_danmaku_num

                clip.refresh = False
                put_list.append(clip)

            context['clips'].append({
                'id': clip.key.id(),
                'title': clip_list.titles[i],
                'danmaku_num': clip.danmaku_num,
                'advanced_danmaku_num': clip.advanced_danmaku_num,
                'subtitles_num': len(clip.subtitle_danmaku_pools),
                'code_num': clip.code_danmaku_num,
            })

        ndb.put_multi(put_list)
        self.render('manage_danmaku', context)

def pool_required_json(handler):
    def check_index(self, video_id, clip_id):
        clip = ndb.Key('VideoClip', int(clip_id), parent=ndb.Key('Video', video_id)).get()
        if not clip or clip.uploader != self.user_key:
            self.json_response(True, {'message': 'You are not allowed to edit this video.',})
            return

        try:
            pool_index = int(self.request.get('pool_index')) - 1
        except ValueError:
            pool_index = 0

        return handler(self, clip, pool_index)

    return check_index

class ManageDanmakuDetail(BaseHandler):
    @login_required
    def get(self, video_id, clip_id):
        video_key = ndb.Key('Video', video_id)
        clip_key = ndb.Key('VideoClip', int(clip_id), parent=video_key)
        
        video, clip = ndb.get_multi([video_key, clip_key])
        if not video or video.deleted or video.uploader != self.user_key:
            self.notify('You are not allowed to edit this video.')
            return

        context = {
            'id': video.key.id(),
            'video_url': models.Video.get_video_url(video.key.id()),
            'title': video.title,
            'clip_index': clip.index,
            'clip_title': clip.title,
            'danmaku_num': clip.danmaku_num,
            'danmaku_list_range': range(0, len(clip.danmaku_pools)),
            'advanced_danmaku_pool': clip.advanced_danmaku_pool,
            'subtitles_num': len(clip.subtitle_danmaku_pools),
            'subtitle_names': clip.subtitle_names,
            'subtitle_approved': clip.subtitle_approved,
            'code_danmaku_pool': clip.code_danmaku_pool,
        }
        self.render('manage_danmaku_detail', context)

    @login_required_json
    @pool_required_json
    def post(self, clip, pool_index):
        pool_type = self.request.get('pool_type')
        try:
            if pool_type == 'danmaku':
                danmaku_pool = ndb.Key('DanmakuPool', int(pool_id)).get()
                self.json_response(False,  {
                    'danmaku_list': [Danmaku.format_danmaku(danmaku, danmaku_pool) for danmaku in danmaku_pool.danmaku_list]
                })
            elif pool_type == 'advanced':
                advanced_danmaku_pool = clip.advanced_danmaku_pool.get()
                self.json_response(False, {
                    'danmaku_list': [Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool) for danmaku in advanced_danmaku_pool.danmaku_list]
                })
            elif pool_type == 'subtitles':
                subtitle_danmaku_pool = clip.subtitle_danmaku_pools[pool_index].get()
                self.json_response(False, {
                    'subtitles_list': Subtitles.format_subtitles(subtitle_danmaku_pool)
                })
            elif pool_type == 'code':
                code_danmaku_pool = clip.code_danmaku_pool.get()
                self.json_response(False, {
                    'danmaku_list': [Danmaku.format_code_danmaku(danmaku, code_danmaku_pool) for danmaku in code_danmaku_pool.danmaku_list]
                })
            else:
                raise IndexError('Invalid type')
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})

    @login_required_json
    @pool_required_json
    def drop(self, clip, pool_index):
        pool_type = self.request.get('pool_type')
        try:
            if pool_type == 'danmaku':
                danmaku_pool = clip.danmaku_pools.pop(pool_index)
                danmaku_pool.delete()
            elif pool_type == 'advanced':
                clip.advanced_danmaku_pool.delete()
                clip.advanced_danmaku_pool = None
            elif pool_type == 'subtitles':
                subtitle_danmaku_pool = clip.subtitle_danmaku_pools.pop(pool_index)
                subtitle_danmaku_pool.delete()
                clip.subtitle_names.pop(pool_index)
                clip.subtitle_approved.pop(pool_index)
            elif pool_type == 'code':
                clip.code_danmaku_pool.delete()
                clip.code_danmaku_pool = None
            clip.put()
            self.json_response(False)
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})

    @login_required_json
    @pool_required_json
    def confirm(self, clip, pool_index):
        try:
            idx = int(self.request.get('danmaku_index'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid index.'})
            return

        pool_type = self.request.get('pool_type')
        try:
            if pool_type == 'advanced':
                danmaku_pool = clip.advanced_danmaku_pool.get()
                danmaku_pool.danmaku_list[idx].approved = True
                danmaku_pool.put()
            elif pool_type == 'subtitles':
                clip.subtitle_approved[pool_index] = True
                clip.put()
            elif pool_type == 'code':
                danmaku_pool = clip.code_danmaku_pool.get()
                danmaku_pool.danmaku_list[idx].approved = True
                danmaku_pool.put()
            else:
                self.json_response(True, {'message': 'Invalid type.'})
                return
            self.json_response(False)
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})

    @login_required_json
    @pool_required_json
    def delete(self, clip, pool_index):
        try:
            idxs = [int(index) for index in self.request.POST.getall('danmaku_index[]')]
        except ValueError:
            self.json_response(True, {'message': 'Invalid indices.'})
            return
        idxs.sort(reverse=True)

        pool_type = self.request.get('pool_type')
        if pool_type == 'danmaku':
            danmaku_pool = clip.danmaku_pools[pool_index].get()
        elif pool_type == 'advanced':
            danmaku_pool = clip.advanced_danmaku_pool.get()
        elif pool_type == 'code':
            danmaku_pool = clip.code_danmaku_pool.get()
        else:
            self.json_response(True, {'message': 'Invalid type.'})
            return

        try:
            for index in idxs:
                danmaku_pool.danmaku_list.pop(index)
            danmaku_pool.put()
            self.json_response(False, {'message': 'Danmaku deleted.'})
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})
