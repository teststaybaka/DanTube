from views import *
from PIL import Image
from google.appengine.api import images
import urlparse

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"
YOUTUBE_API_KEY = "AIzaSyBbf3cs6Nw483po40jw7hZLejmdrgwozWc"
                
def ISO_8601_to_seconds(duration):
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

class CoverUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('coverImage')
        if upload == []:
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
    def edit(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if video is None or video.uploader.id() != self.user.key.id():
            self.notify('You are not allowed to edit this video.')
        else:
            self.render('edit_video', {'video':video.get_full_info()})

    def field_check(self):
        self.title = self.request.get('total-title').strip()
        if not self.title:
            return {
                'error': True,
                'message': 'Title must not be empty!'
            }
        elif len(self.title) > 400:
            return {
                'error': True,
                'message': 'Title is too long!'
            }

        self.category = self.request.get('category').strip()
        if not self.category:
            return {
                'error': True,
                'message': 'Category must not be empty!'
            }
        self.subcategory = self.request.get('subcategory').strip()
        if not self.subcategory:
            return {
                'error': True,
                'message': 'Subcategory must not be empty!'
            }
        if not ((self.category in models.Video_Category) and (self.subcategory in models.Video_SubCategory[self.category])):
            return {
                'error': True,
                'message': 'Category mismatch!'
            }

        self.description = self.request.get('description')
        if not self.description.strip():
            return {
                'error': True,
                'message': 'Description must not be empty!'
            }
        elif len(self.description) > 2000:
            return {
                'error': True,
                'message': 'Description is too long!'
            }

        self.video_type = self.request.get('video-type-option').strip()
        if not self.video_type:
            return {
                'error': True,
                'message': 'Video type must not be empty!'
            }

        self.tags_ori = self.request.get('tags').split(',')
        self.tags = []
        for i in range(0, len(self.tags_ori)):
            tag = self.tags_ori[i].strip()
            if tag != '':
                if len(tag) > 100:
                    return {
                        'error': True,
                        'message': 'Tags are too long!'
                    }
                self.tags.append(self.tags_ori[i].strip())
        if len(self.tags) == 0:
            return {
                'error': True,
                'message': 'Tags must not be empty!'
            }
        elif len(self.tags) > 20:
            return {
                'error': True,
                'message': 'Too many tags!'
            }

        self.allow_tag_add = self.request.get('allow-add')
        if self.allow_tag_add == 'on':
            self.allow_tag_add = True
        else:
            self.allow_tag_add = False

        self.durations = []
        self.sources = []
        self.vids = []
        self.raw_urls = self.request.POST.getall('video-url[]')
        if len(self.raw_urls) == 0:
            return {
                'error': True,
                'message': 'You must submit at least one video!'
            }
        elif len(self.raw_urls) > 500:
            return {
                'error': True,
                'message': 'Too many parts!'
            }
        for i in range(0, len(self.raw_urls)):
            raw_url = self.raw_urls[i].strip();
            if not raw_url:
                return {
                    'error': True,
                    'message': 'invalid url',
                    'index': i,
                }
            else:
                res = models.VideoClip.parse_url(raw_url)
                youtube_api_url = YOUTUBE_API_URL + '/videos?key=' + YOUTUBE_API_KEY + '&id=' + res['vid'] + '&part=contentDetails'
                if i == 0:
                    youtube_api_url += ',snippet'
                vlist = json.load(urllib2.urlopen(youtube_api_url))['items']
                if len(vlist) < 1:
                    return {
                        'error': True,
                        'message': 'invalid url',
                        'index': i,
                    }
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


        self.subtitles = self.request.POST.getall('sub-title[]')
        for i in range(0, len(self.subtitles)):
            subtitle = self.subtitles[i].strip()
            if len(subtitle) > 400:
                return {
                    'error': True,
                    'message': 'Sub title too long!',
                }

        self.subintros = self.request.POST.getall('sub-intro[]')
        for i in range(0, len(self.subintros)):
            subintro = self.subintros[i]
            if len(subintro) > 2000:
                return {
                    'error': True,
                    'message': 'Sub intro too long!',
                }

        self.indices = self.request.POST.getall('index[]')
        for i in range(0, len(self.indices)):
            try:
                index = int(self.indices[i])
            except Exception, e:
                return {
                    'error': True,
                    'message': 'Index error.',
                }

        return {'error': False}

    def thumbnail_upload(self):
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

    @login_required
    def submit_post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        res = self.field_check()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        self.thumbnail_field = self.request.POST.get('thumbnail')
        self.thumbnail_key = None
        if self.thumbnail_field != '':
            try:
                self.thumbnail_upload()
            except Exception, e:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': str(e),
                }))
                return

        try:
            self.video_clips = []
            for i in range(0, len(self.raw_urls)):
                video_clip = models.VideoClip.Create(
                    subintro=self.subintros[i], 
                    duration=self.durations[i], 
                    raw_url=self.raw_urls[i],
                    source=self.sources[i],
                    vid=self.vids[i]
                )
                self.video_clips.append(video_clip.key)
        except Exception, e: # TODO: a regular thread is required to remove unused clip
            for i in range(0, len(self.video_clips)):
                self.video_clips[i].delete()
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e),
            }))
            return

        try:
            video = models.Video.Create(
                user = user,
                description = self.description,
                title = self.title,
                category = self.category,
                subcategory = self.subcategory,
                video_type = self.video_type,
                duration = sum(self.durations),
                tags = self.tags,
                allow_tag_add = self.allow_tag_add,
                thumbnail = self.thumbnail_key,
                default_thumbnail = self.default_thumbnail,
                subtitles = self.subtitles,
                video_clips = self.video_clips,
            )
        except Exception, e:
            for i in range(0, len(self.video_clips)):
                self.video_clips[i].delete()
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e),
            }))
            return

        upload_record = models.ActivityRecord(creator=user.key, activity_type='upload', video=video.key)
        upload_record.put()

        user.videos_submitted += 1
        user.put()
        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video submitted successfully!'
        }))

    @login_required
    def edit_post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        user = self.user

        if video is None or video.uploader.id() != user.key.id():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You are not allowed to edit this video.',
            }))
            return

        res = self.field_check()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        self.thumbnail_field = self.request.POST.get('thumbnail')
        self.thumbnail_key = None
        if self.thumbnail_field != '':
            try:
                self.thumbnail_upload()
            except Exception, e:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': str(e),
                }))
                return

        try:
            changed = False
            if video.description != self.description:
                video.description = self.description
                changed = True

            if video.title != self.title:
                video.title = self.title
                changed = True

            if video.category != self.category:
                video.category = self.category
                changed = True

            if video.subcategory != self.subcategory:
                video.subcategory = self.subcategory
                changed = True

            if video.video_type != self.video_type:
                video.video_type = self.video_type

            if video.tags != self.tags:
                video.tags = self.tags
                changed = True

            if video.allow_tag_add != self.allow_tag_add:
                video.allow_tag_add = self.allow_tag_add

            if self.thumbnail_key != None:
                if video.thumbnail != None:
                    images.delete_serving_url(video.thumbnail)
                    models.blobstore.BlobInfo(video.thumbnail).delete()
                video.thumbnail = self.thumbnail_key

            if video.video_clip_titles != self.subtitles:
                video.video_clip_titles = self.subtitles

            new_clips = []
            ori_clips = ndb.get_multi(video.video_clips)
            used_clips = {}
            video_duration = 0
            for i in range(0, len(self.indices)):
                index = int(self.indices[i])
                if index != -1:
                    clip = ori_clips[index]
                    if clip.subintro != self.subintros[i]:
                        clip.subintro = self.subintros[i]
                    if clip.raw_url != self.raw_urls[i]:
                        clip.raw_url = self.raw_urls[i]
                    if clip.source != self.sources[i]:
                        clip.source = self.sources[i]
                    if clip.vid != self.vids[i]:
                        clip.vid = self.vids[i]
                    if clip.duration != self.durations[i]:
                        clip.duration = self.durations[i]
                    clip.put()
                    video_duration += clip.duration
                    new_clips.append(clip.key)
                    used_clips[index] = 1
                else:
                    clip = models.VideoClip.Create(
                        subintro=self.subintros[i], 
                        duration=self.durations[i], 
                        raw_url=self.raw_urls[i],
                        source=self.sources[i],
                        vid=self.vids[i]
                    )
                    video_duration += clip.duration
                    new_clips.append(clip.key)

            if video.video_clips != new_clips:
                # logging.info('not the same')
                for i in range(0, len(ori_clips)):
                    if not used_clips.get(i):
                        ori_clips[i].key.delete()
                video.video_clips = new_clips

            # logging.info('put')
            video.duration = video_duration
            video.put()
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return
        else:
            if changed:
                video.create_index('videos_by_created', models.time_to_seconds(video.created) )
                video.create_index('videos_by_hits', video.hits )
                video.create_index('videos_by_favors', video.favors )
                video.create_index('videos_by_user' + str(video.uploader.id()), models.time_to_seconds(video.created) )

                edit_record = models.ActivityRecord(creator=user.key, activity_type='edit', video=video.key, content='Video edited.')
                edit_record.put()

        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video updated successfully!'
        }))

class AddTag(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return
        if not video.allow_tag_add:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You are not allowed to add more tags to this video.'
            }))
            return

        new_tag = self.request.get('new-tag').strip()
        if not new_tag:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Empty tag.'
            }))
            return
        elif len(new_tag) > 100:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Tag too long.'
            }))
            return
        elif ',' in new_tag:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Can not contain ",".'
            }))
            return
        elif new_tag in video.tags:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Tag already existed.'
            }))
            return

        if len(video.tags) >= 20:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Can not add more tags.'
            }))
            return

        video.tags.append(new_tag)
        video.put()
        video.create_index('videos_by_created', models.time_to_seconds(video.created) )
        video.create_index('videos_by_hits', video.hits )
        video.create_index('videos_by_favors', video.favors )
        video.create_index('videos_by_user' + str(video.uploader.id()), models.time_to_seconds(video.created) )
        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video updated successfully!'
        }))

class DeleteVideo(BaseHandler):
    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
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
            if video is None or video.uploader.id() != self.user.key.id():
                continue

            self.user.videos_favored -= video.favors
            video.Delete()
            deleted_ids.append(video_id)

        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video deleted.'
            }))
            return
        self.user.videos_submitted -= len(deleted_ids)
        self.user.put()

        self.response.out.write(json.dumps({
            'error': False,
            'message': deleted_ids,
        }))

class ManageVideo(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE
        try:
            page = int(self.request.get('page'))
            if page < 1:
                raise ValueError('Negative')
        except ValueError:
            page = 1

        context = {}
        context['videos'] = []

        keywords = self.request.get('keywords').strip().lower()
        order = self.request.get('order')
        if keywords:
            context['order'] = 'created'
            context['video_keywords'] = keywords
            query_string = 'content: ' + keywords
            page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
            offset = (page - 1)*page_size
            try:
                options = search.QueryOptions(offset=offset, limit=page_size)
                query = search.Query(query_string=query_string, options=options)
                index = search.Index(name='videos_by_user' + str(user.key.id()))
                result = index.search(query)                
                total_found = min(result.number_found, models.MAX_QUERY_RESULT)
                total_pages = math.ceil(total_found/float(page_size))

                video_keys = []
                for video_doc in result.results:
                    video_keys.append(ndb.Key(urlsafe=video_doc.doc_id))
                videos = ndb.get_multi(video_keys)
            except Exception, e:
                self.notify('Search error.')
                return
        else:
            context['order'] = order
            context['video_keywords'] = ''
            if order == 'hits': # most viewed
                order = models.Video.hits
            elif order == 'created': # newest uplooad
                order = models.Video.created
            elif order == 'favors': # most favors
                order = models.Video.favors
            else:
                context['order'] = 'created'
                order = models.Video.created
            
            total_found = user.videos_submitted
            total_pages = math.ceil(total_found/float(page_size))
            videos = []
            if total_found != 0 and page <= total_pages:
                offset = (page - 1) * page_size
                videos = models.Video.query(models.Video.uploader==self.user.key).order(-order).fetch(offset=offset, limit=page_size)
        
        # logging.info(videos)
        for i in range(0, len(videos)):
            # logging.info(videos[i])
            video = videos[i]
            video_info = video.get_basic_info()
            if video.playlist_belonged != None:
                playlist = video.playlist_belonged.get()
                video_info['playlist_title'] = playlist.title
            context['videos'].append(video_info)

        context['total_found'] = total_found
        context.update(self.get_page_range(page, total_pages) )
        self.render('manage_video', context)
