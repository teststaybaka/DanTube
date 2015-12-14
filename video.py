from views import *
from PIL import Image

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
        if not video or video.uploader != user.key:
            self.notify('You are not allowed to edit this video.')
            return

        return handler(self, video, clip_list)

    return check_author

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

        self.tags_ori = self.request.POST.getall('tags[]')
        self.tags = []
        for i in xrange(0, len(self.tags_ori)):
            tag = self.tags_ori[i].strip()
            if len(tag) > 100:
                raise Exception('One of tags is too long!')
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
        self.clip_titles = self.request.POST.getall('sub-title[]')
        self.subintros = self.request.POST.getall('sub-intro[]')
        self.indices = self.request.POST.getall('index[]')
        self.sub_changed = self.request.POST.getall('changed[]')
        if len(self.indices) == 0:
            raise Exception('You must submit at least one video!')
        elif len(self.indices) > 500:
            raise Exception('Too many parts!')
        for i in xrange(0, len(self.indices)):
            try:
                self.indices[i] = int(self.indices[i].strip())
            except Exception, e:
                raise Exception('Index error.')

        for i in xrange(0, len(self.sub_changed)):
            if self.sub_changed[i] == 'False':
                self.sub_changed[i] = False
            else:
                self.sub_changed[i] = True

        youtube = build('youtube', 'v3', developerKey=self.app.config.get('API_Key'))
        for i in xrange(0, len(self.indices)):
            if self.indices[i] != -1:
                self.vids.append(-1)
                self.durations.append(-1)
                continue

            raw_url = self.raw_urls[i] = self.raw_urls[i].strip()
            if not raw_url:
                raise Exception('invalid url:'+str(i))
            else:
                try:
                    res = models.VideoClip.parse_url(raw_url, self.sources[i])
                except Exception:
                    raise Exception('invalid url:'+str(i))

                if i == 0:
                    vlist = youtube.videos().list(id=res['vid'], part='contentDetails,snippet').execute()['items']
                else:
                    vlist = youtube.videos().list(id=res['vid'], part='contentDetails').execute()['items']
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

        for i in xrange(0, len(self.clip_titles)):
            self.clip_titles[i] = self.clip_titles[i].strip()
            if len(self.clip_titles[i]) > 400:
                raise Exception('Sub title too long!')

        for i in xrange(0, len(self.subintros)):
            self.subintros[i] = self.subintros[i].strip()
            if len(self.subintros[i]) > 2000:
                raise Exception('Sub intro too long!')

    def upload_default_thumbnail(self, video_id):
        im = Image.open(cStringIO.StringIO(urllib2.urlopen('http://img.youtube.com/vi/'+self.default_thumbnail+'default.jpg').read()))
        bucket_name = 'dantube-thumbnail'
        large_file = gcs.open('/'+bucket_name+'/large-'+video_id, 'w', content_type="image/jpeg", options={'x-goog-acl': 'public-read'})
        standard_file = gcs.open('/'+bucket_name+'/standard-'+video_id, 'w', content_type="image/jpeg", options={'x-goog-acl': 'public-read'})
        resized_im = im.resize((512,288), Image.ANTIALIAS)
        resized_im.save(large_file, format='jpeg', quality=90, optimize=True)
        resized_im = resized_im.resize((208,117), Image.ANTIALIAS)
        resized_im.save(standard_file, format='jpeg', quality=90, optimize=True)
        large_file.close()
        standard_file.close()

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
            large_file = gcs.open('/'+bucket_name+'/large-'+video_id, 'w', content_type="image/jpeg", options={'x-goog-acl': 'public-read'})
            standard_file = gcs.open('/'+bucket_name+'/standard-'+video_id, 'w', content_type="image/jpeg", options={'x-goog-acl': 'public-read'})

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
        except models.TransactionFailedError:
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
                video=video.key,
                uploader=user.key,
                title=self.clip_titles[i],
                index=i,
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
        ndb.put_multi([user_detail, clip_list])

        q = taskqueue.Queue('Activity')
        q.add(taskqueue.Task(payload=str(self.user_key.id()), method='PULL'))
            
        self.json_response(False)

    @login_required_json
    def edit_post(self, video_id):
        video, clip_list = ndb.get_multi([ndb.Key('Video', video_id), models.VideoClipList.get_key(video_id)])
        if not video or video.uploader != self.user_key:
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

        changed = 0
        if video.title != self.title:
            video.title = self.title
            changed |= 3

        if video.intro != self.intro:
            video.intro = self.intro
            changed |= 3

        if video.category != self.category:
            video.category = self.category
            changed |= 3

        if video.subcategory != self.subcategory:
            video.subcategory = self.subcategory
            changed |= 3

        if video.video_type != self.video_type:
            video.video_type = self.video_type
            changed |= 3

        if video.tags != self.tags:
            video.tags = self.tags
            changed |= 3

        if video.allow_tag_add != self.allow_tag_add:
            video.allow_tag_add = self.allow_tag_add
            changed |= 1

        ori_clips = clip_list.clips
        new_clips = []
        used_clips = set()
        video_duration = 0
        for i in xrange(0, len(self.indices)):
            index = self.indices[i]
            if index != -1:
                clip_key = ori_clips[index]
                if self.sub_changed[i] or index != i:
                    clip = clip_key.get()
                    clip.index = i
                    clip.title = self.clip_titles[i]
                    clip.subintro = self.subintros[i]
                    clip.put()
                    changed |= 1
                    logging.info(str(i)+' '+str(index)+' '+str(changed))

                used_clips.add(index)
                new_clips.append(clip_key)
            else:
                clip = models.VideoClip(
                    video=video.key,
                    uploader=self.user_key,
                    title=self.clip_titles[i],
                    index=i,
                    subintro=self.subintros[i],
                    duration=self.durations[i],
                    raw_url=self.raw_urls[i],
                    source=self.sources[i],
                    vid=self.vids[i]
                )
                clip.put()
                video_duration += clip.duration
                new_clips.append(clip.key)
                changed |= 1
                logging.info(changed)

        for index in xrange(0, len(ori_clips)):
            if index not in used_clips:
                clip = ori_clips[index].get()
                video_duration -= clip.duration
                models.VideoClip.Delete(clip.key)
                changed |= 1

        if not (changed & 1):
            if self.thumbnail_field != '':
                self.json_response(False)
            else:
                self.json_response(True, {'message': 'Nothing changed.'})
            return
                
        clip_list.clips = new_clips
        clip_list.titles = self.clip_titles
        video.duration += video_duration
        if self.allow_post:
            video.created = datetime.now()
            video.is_edited = True
            q = taskqueue.Queue('Activity')
            q.add(taskqueue.Task(payload=str(self.user_key.id()), method='PULL'))
        ndb.put_multi([video, clip_list])

        if changed & 2:
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

        videos = ndb.get_multi([ndb.Key('Video', identifier) for identifier in ids])
        deleted_counter = 0
        for i in xrange(0, len(ids)):
            video = videos[i]
            if not video or video.uploader != self.user_key:
                continue

            video.Delete()
            deleted_counter += 1

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
        for i in xrange(0, len(clips)):
            clip = clips[i]
            context['clips'].append({
                'id': clip.key.id(),
                'title': clip.title,
                'danmaku_num': clip.danmaku_num,
                'advanced_danmaku_num': clip.advanced_danmaku_num,
                'subtitles_num': clip.subtitles_num,
                'code_num': clip.code_danmaku_num,
            })

        self.render('manage_danmaku', context)

def clip_required_json(handler):
    def check_index(self, video_id, clip_id):
        clip = ndb.Key('VideoClip', int(clip_id)).get()
        if not clip or clip.uploader != self.user_key:
            self.json_response(True, {'message': 'You are not allowed to edit this video.',})
            return

        return handler(self, clip)

    return check_index

class ManageDanmakuDetail(BaseHandler):
    @login_required
    def get(self, video_id, clip_id):
        video_key = ndb.Key('Video', video_id)
        clip_key = ndb.Key('VideoClip', int(clip_id))
        
        video, clip = ndb.get_multi([video_key, clip_key])
        if not video or video.uploader != self.user_key:
            self.notify('You are not allowed to edit this video.')
            return

        danmaku_list = models.VideoClip.load_cloud_danmaku(clip_key, 'danmaku')
        danmaku_list += [danmaku.format() for danmaku in clip.danmaku_buffer]
        advanced_danmaku_list = models.VideoClip.load_cloud_danmaku(clip_key, 'advanced')
        advanced_danmaku_list += [danmaku.format() for danmaku in clip.advanced_danmaku_buffer]
        subtitles_list = models.VideoClip.load_cloud_danmaku(clip_key, 'subtitles')
        code_danmaku_list = models.VideoClip.load_cloud_danmaku(clip_key, 'code')

        if clip.danmaku_num != len(danmaku_list) or clip.advanced_danmaku_num != len(advanced_danmaku_list) or clip.subtitles_num != len(subtitles_list) or clip.code_danmaku_num != len(code_danmaku_list):
            clip.danmaku_num = len(danmaku_list)
            clip.advanced_danmaku_num = len(advanced_danmaku_list)
            clip.subtitles_num = len(subtitles_list)
            clip.code_danmaku_num = len(code_danmaku_list)
            clip.put()

        context = {
            'id': video.key.id(),
            'video_url': models.Video.get_video_url(video.key.id()),
            'title': video.title,
            'clip_id': clip.key.id(),
            'clip_index': clip.index,
            'clip_title': clip.title,
            'danmaku_num': clip.danmaku_num,
            'danmaku_list': json.dumps(danmaku_list),
            'advanced_danmaku_num': clip.advanced_danmaku_num,
            'advanced_danmaku_list': json.dumps(advanced_danmaku_list),
            'subtitles_num': clip.subtitles_num,
            'subtitles_list': json.dumps(subtitles_list),
            'code_danmaku_num': clip.code_danmaku_num,
            'code_danmaku_list': json.dumps(code_danmaku_list),
        }
        self.render('manage_danmaku_detail', context)

    @login_required_json
    @clip_required_json
    def confirm(self, clip):
        try:
            index = int(self.request.get('index'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid index.'})
            return

        pool_type = self.request.get('pool_type')
        danmaku_list = []
        if pool_type == 'advanced':
            danmaku_list = [danmaku.format() for danmaku in clip.advanced_danmaku_buffer]
            clip.advanced_danmaku_buffer = []
            clip.put()
        elif pool_type != 'subtitles' and pool_type != 'code':
            self.json_response(True, {'message': 'Invalid type.'})
            return
        danmaku_list += models.VideoClip.load_cloud_danmaku(clip.key, pool_type)
        
        try:
            danmaku_list[index]['approved']= True
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})
            return
        models.VideoClip.save_cloud_danmaku(clip.key, pool_type, danmaku_list)

        self.json_response(False)

    @login_required_json
    @clip_required_json
    def delete(self, clip):
        try:
            idxs = [int(index) for index in self.request.POST.getall('index[]')]
            if not idxs:
                raise ValueError('Empty')
        except ValueError:
            self.json_response(True, {'message': 'Invalid indices.'})
            return
        idxs.sort(reverse=True)

        pool_type = self.request.get('pool_type')
        danmaku_list = []
        if pool_type == 'danmaku':
            danmaku_list = [danmaku.format() for danmaku in clip.danmaku_buffer]
            clip.danmaku_buffer = []
            clip.put()
        elif pool_type == 'advanced':
            danmaku_list = [danmaku.format() for danmaku in clip.advanced_danmaku_buffer]
            clip.advanced_danmaku_buffer = []
            clip.put()
        elif pool_type != 'subtitles' and pool_type != 'code':
            self.json_response(True, {'message': 'Invalid type.'})
            return
        danmaku_list += models.VideoClip.load_cloud_danmaku(clip.key, pool_type)

        try:
            j = idxs[-1]
            for i in xrange(idxs[-1], len(danmaku_list)):
                if idxs and i == idxs[-1]:
                    idxs.pop()
                else:
                    danmaku_list[j] = danmaku_list[i]
                    j += 1
            del danmaku_list[j:]
        except IndexError:
            self.json_response(True, {'message': 'Index out of range.'})
            return
        models.VideoClip.save_cloud_danmaku(clip.key, pool_type, danmaku_list)

        self.json_response(False)
