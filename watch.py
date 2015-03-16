from views import *
import math

class Video(BaseHandler):
    def get(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.notify('Video not found or deleted.', 404)
            return

        try:
            clip_index = int(self.request.get('index'))
        except ValueError:
            clip_index = 1
        if clip_index < 1 or clip_index > len(video.video_clips):
            self.notify('Video not found.', 404)
            return

        video.hits += 1
        video.put()
        video.create_index('videos_by_hits', video.hits)
        uploader = video.uploader.get()
        uploader.videos_watched += 1
        uploader.put()

        user = self.user
        if user is not None:
            l = len(user.history)
            videos = [h.video for h in user.history]
            try:
                idx = videos.index(video.key)
                user.history.pop(idx)
            except ValueError:
                logging.info('not found')
                l += 1
            if l > 100:
                user.history.pop(0)
            new_history = models.History(video=video.key)
            user.history.append(new_history)
            user.put()

        video_info = video.get_basic_info()
        cur_clip = video.video_clips[clip_index-1].get()
        video_info['cur_vid'] = cur_clip.vid
        video_info['cur_subintro'] = cur_clip.subintro
        video_info['cur_index'] = clip_index
        video_info['clip_titles'] = video.video_clip_titles
        video_info['clip_range'] = range(0, len(video.video_clip_titles))
        if clip_index == 1:
            video_info['clip_range_min'] = 0
            video_info['clip_range_max'] = min(2, len(video.video_clip_titles) - 1)
        elif clip_index == len(video.video_clip_titles):
            video_info['clip_range_min'] = max(0, len(video.video_clip_titles) - 3)
            video_info['clip_range_max'] = len(video.video_clip_titles) - 1
        else:
            video_info['clip_range_min'] = clip_index - 2
            video_info['clip_range_max'] = clip_index

        playlist_info = {}
        if video.playlist_belonged != None:
            playlist = video.playlist_belonged.get()
            playlist_info = playlist.get_basic_info()
            idx = playlist.videos.index(video.key)
            playlist_info['cur_index'] = idx
            playlist_info['videos'] = []
            videos = ndb.get_multi(playlist.videos)
            for i in range(0, len(videos)):
                playlist_info['videos'].append(videos[i].get_basic_info())
        
        context = {'video': video_info, 'uploader': uploader.get_public_info(), 'playlist': playlist_info}
        self.render('video', context)

class Comment(BaseHandler):
    def get_comment(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        page_size = 20
        try:
            page = int(self.request.get('page') )
            if page < 1:
                raise ValueError('Negative')
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Page invalid.'
            }))
            return

        offset = (page-1)*page_size
        comments = models.Comment.query(ancestor=video.key).order(-models.Comment.created).fetch(offset=offset, limit=page_size)
        result = {'error': False, 'comments':[], 'total_comments': video.comment_counter}
        for i in range(0, len(comments)):
            comment = comments[i]
            info = {
                'creator': comment.creator.get().get_public_info(),
                'content': comment.content,
                'created': comment.created.strftime("%Y-%m-%d %H:%M"),
                'deleted': comment.deleted,
                'floorth': comment.floorth,
                'id': comment.key.id(),
                'inner_comment_counter': comment.inner_comment_counter,
                'inner_comments': [],
            }
            inner_comments = models.InnerComment.query(ancestor=comment.key).order(-models.InnerComment.created).fetch(offset=0, limit=3)
            for j in range(0, len(inner_comments)):
                inner_comment = inner_comments[len(inner_comments) - j - 1]
                inner_info = {
                    'creator': inner_comment.creator.get().get_public_info(),
                    'content': inner_comment.content,
                    'created': inner_comment.created.strftime("%Y-%m-%d %H:%M"),
                    'deleted': inner_comment.deleted,
                }
                info['inner_comments'].append(inner_info)
            result['comments'].append(info)

        result['total_pages'] = math.ceil(video.comment_counter/float(page_size))
        self.response.out.write(json.dumps(result))

    def get_inner_comment(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        comment_id = self.request.get('comment_id')
        if not comment_id:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment not found'
            }))
            return
        else:
            comment = models.Comment.get_by_id(int(comment_id), video.key)
            if not comment:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Comment not found'
                }))
                return

        page_size = models.DEFAULT_PAGE_SIZE
        try:
            page = int(self.request.get('page') )
            if page < 1:
                raise ValueError('Negative')
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Page invalid.'
            }))
            return

        offset = (page-1)*page_size
        inner_comments = models.InnerComment.query(ancestor=comment.key).order(models.InnerComment.created).fetch(offset=offset, limit=page_size)
        result = {'error': False, 'inner_comments': []}
        for i in range(0, len(inner_comments)):
            inner_comment = inner_comments[i]
            info = {
                'creator': inner_comment.creator.get().get_public_info(),
                'content': inner_comment.content,
                'created': inner_comment.created.strftime("%Y-%m-%d %H:%M"),
                'deleted': inner_comment.deleted,
            }
            result['inner_comments'].append(info)

        result['total_pages'] = math.ceil(comment.inner_comment_counter/float(page_size))
        self.response.out.write(json.dumps(result))

    @login_required
    def comment_post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        user = self.user
        content = self.request.get('content')
        if not content.strip():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No content.'
            }))
            return
        elif len(content) > 2000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment too long.'
            }))
            return

        at_users = self.request.POST.getall('ats[]')

        comment = models.Comment.Create(video, user, content)
        video.comment_counter = comment.floorth
        video.last_updated = datetime.now()
        video.put()

        self.response.out.write(json.dumps({
            'error': False,
        }))

    @login_required
    def reply_post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        comment_id = self.request.get('comment_id')
        if not comment_id:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment not found'
            }))
            return
        else:
            comment = models.Comment.get_by_id(int(comment_id), video.key)
            if not comment:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Comment not found'
                }))
                return

        user = self.user
        content = self.request.get('content')
        if not content.strip():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No content.'
            }))
            return
        elif len(content) > 2000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment too long.'
            }))
            return

        at_users = self.request.POST.getall('ats[]')

        inner_comment = models.InnerComment.Create(comment, user, content)
        video.last_updated = datetime.now()
        video.put()
        
        self.response.out.write(json.dumps({
            'error': False,
            'total_pages': math.ceil(comment.inner_comment_counter/float(models.DEFAULT_PAGE_SIZE)),
        }))

class Danmaku(BaseHandler):
    def get(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.',
            }))

        try:
            clip_index = int(self.request.get('index') )
        except ValueError:
            clip_index = 1
        if clip_index < 1 or clip_index > len(video.video_clips):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.',
            }))
            return

        clip = video.video_clips[clip_index-1].get()
        danmaku_list = []
        danmaku_pools = ndb.get_multi(clip.danmaku_pools)
        for i in range(0, len(danmaku_pools)):
            danmaku_pool = danmaku_pools[i]
            for j in range(0, len(danmaku_pool.danmaku_list)):
                danmaku = danmaku_pool.danmaku_list[j]
                danmaku_list.append({
                    'content': danmaku.content,
                    'timestamp': danmaku.timestamp,
                    'created': danmaku.created.strftime("%m-%d %H:%M"),
                    'created_seconds': models.time_to_seconds(danmaku.created),
                    'creator': danmaku.creator.id(),
                })

        self.response.out.write(json.dumps(danmaku_list))

    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.',
            }))

        try:
            clip_index = int(self.request.get('index'))
        except ValueError:
            clip_index = 1
        if clip_index < 1 or clip_index > len(video.video_clips):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.',
            }))
            return

        try:
            timestamp = float(self.request.get('timestamp'))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid timestamp.',
            }))
            return

        content = self.request.get('content').strip()
        if not content:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Can not be empty.',
            }))
            return
        elif len(content) > 350:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment is too long.',
            }))
            return

        clip = video.video_clips[clip_index-1].get()
        if len(clip.danmaku_pools) == 0:
            danmaku_pool = models.DanmakuPool()
            danmaku_pool.put()
            clip.danmaku_pools.append(danmaku_pool.key)
            clip.put()
        else:
            danmaku_pool = clip.danmaku_pools[-1].get()
            if len(danmaku_pool.danmaku_list) >= 1000:
                danmaku_pool = models.DanmakuPool()
                danmaku_pool.put()
                clip.danmaku_pools.append(danmaku_pool.key)
                if len(clip.danmaku_pools) > 20:
                    clip.danmaku_pools.pop(0).delete()
                clip.put()

        danmaku = models.Danmaku(timestamp=timestamp, creator=user.key, content=content)
        danmaku.put()
        danmaku_pool.danmaku_list.append(danmaku)
        danmaku_pool.put()
        video.last_updated = datetime.now()
        video.put()
        
        self.response.out.write(json.dumps({
            'content': danmaku.content,
            'timestamp': danmaku.timestamp,
            'created': danmaku.created.strftime("%m-%d %H:%M"),
            'created_seconds': models.time_to_seconds(danmaku.created),
            'creator': danmaku.creator.id(),
        }))
        
class Like(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        video = models.Video.get_by_id('dt'+video_id)
        if video is not None:
            video.likes += 1
            video.last_updated = datetime.now()
            video.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
