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
        user, video = ndb.get_multi([self.user_key, ndb.Key('Video', video_id)])
        self.user = user
        if not video or video.uploader != user.key:
            self.notify('You are not allowed to edit this video.')
            return

        return handler(self, video, user)

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
    def edit(self, video):
        clips = models.VideoClip.query(models.VideoClip.video==video.key).order(models.VideoClip.index).fetch()
        context = video.get_full_info()
        context['clips'] = []
        for i in xrange(0, len(clips)):
            clip = clips[i]
            clip_info = {
                'index': clip.index,
                'title': clip.title,
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
        elif len(self.title) > 400:
            raise Exception('Title is too long!')

        self.category = self.request.get('category')
        if not self.category:
            raise Exception('Category must not be empty!')

        self.subcategory = self.request.get('subcategory')
        if not self.subcategory:
            raise Exception('Subcategory must not be empty!')
            
        if not ((self.category in models.Video_Category) and (self.subcategory in models.Video_SubCategory[self.category])):
            raise Exception('Category mismatch!')

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
            if tag:
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
        self.sources = []
        self.vids = []
        self.raw_urls = self.request.POST.getall('video-url[]')
        if len(self.raw_urls) == 0:
            raise Exception('You must submit at least one video!')
        elif len(self.raw_urls) > 1000:
            raise Exception('message': 'Too many parts!')

        for i in xrange(0, len(self.raw_urls)):
            self.raw_urls[i] = self.raw_urls[i].strip();
            raw_url = self.raw_urls[i]
            if not raw_url:
                raise Exception('invalid url:'+str(i))
            else:
                res = models.VideoClip.parse_url(raw_url)
                youtube_api_url = YOUTUBE_API_URL + '/videos?key=' + YOUTUBE_API_KEY + '&id=' + res['vid'] + '&part=contentDetails'
                if i == 0:
                    youtube_api_url += ',snippet'
                vlist = json.load(urllib2.urlopen(youtube_api_url))['items']
                if len(vlist) == 0:
                    raise Exception('invalid url:'+str(i))
                self.sources.append(res['source'])
                self.vids.append(res['vid'])
                vinfo = vlist[0]
                duration = ISO_8601_to_seconds(vinfo['contentDetails']['duration'])
                self.durations.append(duration)
                if i == 0:
                    self.default_thumbnail = res['vid']
                    thumbnails = vinfo['snippet']['thumbnails']
                    if thumbnails.get('maxres'):
                        self.default_thumbnail += ':maxres'
                    elif thumbnails.get('standard'):
                        self.default_thumbnail += ':sd'
                    elif thumbnails.get('high'):
                        self.default_thumbnail += ':hq'
                    else:
                        self.default_thumbnail += ':mq'

        self.clip_titles = self.request.POST.getall('sub-title[]')
        for i in xrange(0, len(self.clip_titles)):
            self.clip_titles[i] = self.clip_titles[i].strip()
            if len(self.clip_titles[i]) > 400:
                raise Exception('Sub title too long!')

        self.subintros = self.request.POST.getall('sub-intro[]')
        for i in xrange(0, len(self.subintros)):
            self.subintros[i] = self.subintros[i].strip()
            if len(subintro) > 2000:
                raise Exception('Sub intro too long!')

        self.indices = self.request.POST.getall('index[]')
        for i in xrange(0, len(self.indices)):
            try:
                self.indices[i] = int(self.indices[i].strip())
            except Exception, e:
                raise Exception('Index error.')

    def thumbnail_upload(self):
        self.thumbnail_field = self.request.POST.get('thumbnail')
        self.thumbnail_key = None
        if not self.thumbnail_field:
            return

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

            output = cStringIO.StringIO()
            if im.mode == "RGBA" or "transparency" in im.info:
                rgba_im = Image.new("RGBA", (512,288))
                resized_im = im.resize((512,288), Image.ANTIALIAS)
                rgba_im.paste(resized_im)
                new_im = Image.new("RGB", (512,288), (255,255,255))
                new_im.paste(rgba_im, rgba_im)
                new_im.save(output, format='jpeg', quality=90)
            else:
                rgb_im = Image.new("RGB", (512,288))
                resized_im = im.resize((512,288), Image.ANTIALIAS)
                rgb_im.paste(resized_im)
                rgb_im.save(output, format='jpeg', quality=90)
        except Exception, e:
            # logging.info('image process failed')
            raise Exception('Image process failed.')
        else:
            output.seek(0)
            form = MultiPartForm()
            # form.add_field('raw_url', raw_url)
            form.add_file('coverImage', 'cover.jpg', fileHandle=output)

            # Build the request
            upload_url = models.blobstore.create_upload_url(self.uri_for('cover_upload'))
            request = urllib2.Request(upload_url)
            request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
            body = str(form)
            request.add_header('Content-type', form.get_content_type())
            request.add_header('Content-length', len(body))
            request.add_data(body)
            # request.get_data()
            request_res = urllib2.urlopen(request).read()
            if request_res == 'error':
                raise Exception('Image upload error.')
            else:
                self.thumbnail_key = models.blobstore.BlobKey(request_res)

    @login_required_json
    def submit_post(self):
        try:
            self.field_check()
            self.thumbnail_upload()
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
                thumbnail=self.thumbnail_key,
                default_thumbnail=self.default_thumbnail,
                tags=self.tags,
                allow_tag_add=self.allow_tag_add
            )
        except Exception, e:
            self.json_response(True, {'message': str(e)})
            return

        video_clips = []
        for i in xrange(0, len(self.raw_urls)):
            video_clip = models.VideoClip(
                parent=video.key,
                index=i,
                title=self.clip_titles[i],
                subintro=self.subintros[i],
                duration=self.durations[i],
                raw_url=self.raw_urls[i],
                source=self.sources[i],
                vid=self.vids[i]
            )
            video_clips.append(video_clip)

        models.video.create_index('videos_by_created', time_to_seconds(video.created))
        models.video.create_index('videos_by_hits', video.hits)
        models.video.create_index('videos_by_likes', video.likes)

        user_detail.videos_submitted += 1
        subscriptions = models.Subscription.query(models.Subscription.uper==self.user_key).fetch(keys_only=True)
        subscribers = [subscription.parent() for subscription in subscriptions]
        for i in xrange(0, len(subscribers)):
            subscribers[i].new_subscriptions += 1
            
        ndb.put_multi_async([user_detail] + subscribers + video_clips)
        self.json_response(False)

    @login_required_json
    def edit_post(self, video_id):
        video = models.Video.get_by_id(video_id)
        if not video or video.uploader != user_key:
            self.json_response(True, {'message': 'You are not allowed to edit this video.'})
            return

        self.allow_post = bool(self.request.get('allow-post'))
        try:
            self.field_check()
            self.thumbnail_upload()
        except Exception, e:
            self.json_response(True, {'message': str(e)})
            return

        reindex = False
        if video.title != self.title:
            video.title = self.title
            reindex = True

        if video.intro != self.intro:
            video.intro = self.intro
            reindex = True

        if video.category != self.category:
            video.category = self.category
            reindex = True

        if video.subcategory != self.subcategory:
            video.subcategory = self.subcategory
            reindex = True

        if video.video_type != self.video_type:
            video.video_type = self.video_type

        if video.tags != self.tags:
            video.tags = self.tags
            reindex = True

        if video.allow_tag_add != self.allow_tag_add:
            video.allow_tag_add = self.allow_tag_add

        if self.thumbnail_key:
            if video.thumbnail:
                images.delete_serving_url(video.thumbnail)
                models.blobstore.BlobInfo(video.thumbnail).delete()
            video.thumbnail = self.thumbnail_key
            if video.playlist_belonged:
                playlist = video.playlist_belonged.get()
                if playlist.first_video == video.key:
                    playlist.set_first_video(video)
                    playlist.put_async()

        ori_clips = models.VideoClip.query(models.VideoClip.video==video.key).order(models.VideoClip.index).fetch()
        new_clips = []
        used_clips = {}
        video_duration = 0
        for i in xrange(0, len(self.indices)):
            index = self.indices[i]
            if index != -1:
                clip = ori_clips[index]
                clip.index = i
                clip.title = self.clip_titles[i]
                clip.subintro = self.subintros[i]
                clip.raw_url = self.raw_urls[i]
                clip.source = self.sources[i]
                clip.vid = self.vids[i]
                clip.duration = self.durations[i]

                video_duration += clip.duration
                used_clips[index] = 1
                new_clips.append(clip)
            else:
                clip = models.VideoClip(
                    parent=video.key,
                    index=i,
                    title=self.clip_titles[i],
                    subintro=self.subintros[i],
                    duration=self.durations[i],
                    raw_url=self.raw_urls[i],
                    source=self.sources[i],
                    vid=self.vids[i]
                )
                video_duration += clip.duration
                new_clips.append(clip)

        if ori_clips != new_clips:
            for i in xrange(0, len(ori_clips)):
                if not used_clips.get(i):
                    ori_clips[i].Delete()

        video.duration = video_duration
        if self.allow_post:
            video.created = datetime.now()
            subscriptions = models.Subscription.query(models.Subscription.uper==self.user_key).fetch(keys_only=True)
            subscribers = [subscription.parent() for subscription in subscriptions]
            for i in xrange(0, len(subscribers)):
                subscribers[i].new_subscriptions += 1
        else:
            subscribers = []
        ndb.put_multi_async([video] + subscribers + new_clips)

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
        if not video:
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
        elif new_tag in video.tags:
            self.json_response(True, {'message': 'Tag already existed.'})
            return

        if len(video.tags) >= 10:
            self.json_response(True, {'message': 'Can not add more tags.'})
            return

        video.tags.append(new_tag)
        video.put_async()
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

        videos = ndb.get_multi([ndb.Key('Video', identifier) for identifier in ids])
        deleted_ids = []
        for i in xrange(0, len(ids)):
            video = videos[i]
            if not video or video.uploader != self.user_key:
                continue

            video.Delete()
            deleted_ids.append(video_id)

        user_detail = self.user_detail_key.get()
        user_detail.videos_submitted -= len(deleted_ids)
        user_detail.put_async()
        self.json_response(False)

class ManageVideo(BaseHandler):
    @login_required:
    def get(self):
        context = {
            'order': self.request.get('order'),
            'video_keywords': self.get_keywords(),
        }
        self.render('manage_video', context)

    @login_required
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        cursor_string = self.request.get('cursor')
        keywords = self.get_keywords()
        order = self.request.get('order')
        context = {'videos': []}
        if order != 'created' or keywords:
            if order == 'hits':
                index = search.Index(name='videos_by_hits')
            elif order == 'likes':
                index = search.Index(name='videos_by_likes')
            elif order == 'created':
                index = search.Index(name='videos_by_created')
            else:
                self.json_response(True, {'message': 'Invalid order.'})
                return

            if keywords:
                query_string = 'content: ' + keywords + ' AND uper: "' + str(user_key.id()) + '"'
            else:
                query_string = 'uper: "' + str(user_key.id()) + '"'

            try:
                cursor = search.Cursor(web_safe_string=cursor_string)
                options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
                query = search.Query(query_string=query_string, options=options)
                result = index.search(query)

                cursor = result.cursor
                context['cursor'] = cursor.web_safe_string if cursor else None
                videos = ndb.get_multi([ndb.Key(urlsafe=video_doc.doc_id) for video_doc in result.results])
            except Exception, e:
                self.json_response(True, 'Search error.')
                return
        else:
            cursor = models.Cursor(urlsafe=cursor_string)
            videos, cursor, more = models.Video.query(models.Video.uploader==user_key).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
            context['cursor'] = cursor.urlsafe() if cursor else None
        
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            if video.playlist_belonged:
                playlist = video.playlist_belonged.get()
                video_info['playlist_title'] = playlist.title
            context['videos'].append(video_info)

        self.json_response(False, context)

class ManageDanmaku(BaseHandler):
    @login_required
    @video_author_required
    def get(self, video):
        clips = models.VideoClip.query(ancestor=video.key).order(models.VideoClip.index).fetch()
        if not clips:
            self.notify('Video not found')
            return

        context = video.get_basic_info()
        context{'clips': []}
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
                'title': clip.title,
                'danmaku_num': clip.danmaku_num,
                'advanced_danmaku_num': clip.advanced_danmaku_num,
                'subtitles_num': len(clip.subtitle_danmaku_pools),
                'code_num': clip.code_danmaku_num,
            })

        ndb.put_multi_async(put_list)
        self.render('manage_danmaku', context)

def pool_required_json(handler):
    def check_index(self, video_id):
        video = models.Video.get_by_id(video_id)
        if not video or video.uploader != self.user_key:
            self.json_response(True, {'message': 'You are not allowed to edit this video.',})
            return

        clip = models.VideoClip.query(models.VideoClip.index==clip_index, ancestor=video.key).get()
        if not clip:
            self.json_response(True, {'message': 'Video not found or deleted.'})
            return

        try:
            pool_index = int(self.request.get('pool_index')) - 1
        except ValueError:
            pool_index = 0

        return handler(self, video, clip, pool_index)

    return check_index

class ManageDanmakuDetail(BaseHandler):
    @login_required
    @video_author_required
    def get(self, video):
        try:
            clip_index = int(self.request.get('index')) - 1
        except ValueError:
            clip_index = 0

        clip = models.VideoClip.query(models.VideoClip.index==clip_index, ancestor=video.key).get()
        if not clip:
            self.notify('Video not found or deleted.')
            return

        context = {
            'id': video.key.id(),
            'url': Video.get_video_url(video.key.id()),
            'title': video.title,
            'clip_index': clip_index,
            'clip_title': clip.title,
            'danmaku_num': clip.danmaku_num,
            'danmaku_list_range': range(0, len(clip.danmaku_pools)),
            'advanced_danmaku_pool': clip.advanced_danmaku_pool,
            'subtitles_num': len(clip.subtitle_danmaku_pools),
            'subtitle_names': clip.subtitle_names,
            'code_danmaku_pool': clip.code_danmaku_pool,
        }
        self.render('manage_danmaku_detail', context)

    @login_required_json
    @pool_required_json
    def post(self, video, clip, pool_index):
        pool_type = self.request.get('pool_type')
        try:
            if pool_type == 'danmaku':
                danmaku_pool = clip.danmaku_pools[pool_index-1].get()
                self.json_response(False,  {
                    'danmaku_list': [Danmaku.format_danmaku(danmaku, danmaku_pool) for danmaku in danmaku_pool.danmaku_list]
                })
            elif pool_type == 'advanced':
                advanced_danmaku_pool = clip.advanced_danmaku_pool.get()
                self.json_response(False, {
                    'danmaku_list': [Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool) for danmaku in advanced_danmaku_pool.danmaku_list]
                })
            elif pool_type == 'subtitles':
                subtitle_danmaku_pool = clip.subtitle_danmaku_pools[pool_index-1].get()
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
    def drop(self, video, clip, pool_index):
        pool_type = self.request.get('pool_type')
        try:
            if pool_type == 'danmaku':
                danmaku_pool = clip.danmaku_pools.pop(pool_index-1)
                danmaku_pool.delete_async()
            elif pool_type == 'advanced':
                clip.advanced_danmaku_pool.delete_async()
                clip.advanced_danmaku_pool = None
            elif pool_type == 'subtitles':
                subtitle_danmaku_pool = clip.subtitle_danmaku_pools.pop(pool_index-1)
                subtitle_danmaku_pool.delete_async()
                clip.subtitle_names.pop(pool_index-1)
            elif pool_type == 'code':
                clip.code_danmaku_pool.delete_async()
                clip.code_danmaku_pool = None
            clip.put_async()
            self.json_response(False)
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})

    @login_required_json
    @pool_required_json
    def delete(self, video, clip, pool_index):
        try:
            idxs = [int(index) for index in self.request.POST.getall('danmaku_index[]')]
        except ValueError:
            self.json_response(True, {'message': 'Invalid indices.'})
            return
        idxs.sort(reverse=True)

        pool_type = self.request.get('pool_type')
        if pool_type == 'danmaku':
            danmaku_pool = clip.danmaku_pools[pool_index-1].get()
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
            danmaku_pool.put_async()
            self.json_response(False, {'message': 'Danmaku deleted.'})
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})
