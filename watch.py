from views import *
import math

HOT_SCORE_PER_HIT = 5
HOT_SCORE_PER_DANMAKU = 10
HOT_SCORE_PER_COMMENT = 15
HOT_SCORE_PER_LIKE = 5

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
            new_history = models.History(video=video.key, clip_index=clip_index)
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
        
        uploader = video.uploader.get()
        context = {'video': video_info, 'uploader': uploader.get_public_info(user), 'playlist': playlist_info}
        self.render('video', context)

def assemble_link(temp, add_link, users):
    if temp != '':
        user = models.User.query(models.User.nickname==temp[1:].strip()).get(keys_only=True)
        if user is not None:
            if add_link:
                temp = '<a class="blue-link" target="_blank" href="/user/' + str(user.id()) + '">' + temp + '</a>'
            users.append(user)

    return temp

def comment_nickname_recognize(user, content, add_link):
    content = cgi.escape(content)
    new_content = ''
    state = 0
    temp = ''
    users = []
    for i in range(0, len(content)):
        if re.match(r".*[@.,?!;:/\\\"'].*", content[i]) and state == 1:
            state = 0
            new_content += assemble_link(temp, add_link, users)
            temp = ''

        if content[i] == '@' and state == 0:
            state = 1
            temp += '@'
        elif state == 0:
            new_content += content[i]
        else: # state == 1
            temp += content[i]
    new_content += assemble_link(temp, add_link, users)

    seen = set()
    return new_content, [ x for x in users if not (x == user.key or x in seen or seen.add(x))]

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
                    'inner_floorth': inner_comment.inner_floorth,
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
                'inner_floorth': inner_comment.inner_floorth,
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
        content, users = comment_nickname_recognize(user, content, True)

        allow_share = self.request.get('allow-post-comment')
        if allow_share == 'on':
            allow_share = True
        else:
            allow_share = False

        comment = models.Comment.Create(video, user, content)
        video.comment_counter = comment.floorth
        video.update_hot_score(HOT_SCORE_PER_COMMENT)
        video.last_updated = datetime.now()
        video.put()

        comment_record = models.ActivityRecord(creator=user.key, activity_type='comment', floorth=comment.floorth, content=comment.content, video=video.key, public=allow_share)
        comment_record.put()
        user.comments_num += 1
        user.put()

        if len(users) != 0:
            mentioned_message = models.MentionedComment(receivers=users, sender=user.key, comment_type='comment', floorth=comment.floorth, content=comment.content, video=video.key)
            mentioned_message.put()

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
        content, users = comment_nickname_recognize(user, content, True)

        allow_share = self.request.get('allow-post-reply')
        if allow_share == 'on':
            allow_share = True
        else:
            allow_share = False

        inner_comment = models.InnerComment.Create(comment, user, content)
        video.last_updated = datetime.now()
        video.put()

        comment_record = models.ActivityRecord(creator=user.key, activity_type='inner_comment', floorth=inner_comment.floorth, inner_floorth=inner_comment.inner_floorth, content=inner_comment.content, video=video.key, public=allow_share)
        comment_record.put()
        user.comments_num += 1
        user.put()

        if len(users) != 0:
            mentioned_message = models.MentionedComment(receivers=users, sender=user.key, comment_type='inner_comment', floorth=inner_comment.floorth, inner_floorth=inner_comment.inner_floorth, content=inner_comment.content, video=video.key)
            mentioned_message.put()
        
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
                    'type': danmaku.position,
                    'size': danmaku.size,
                    'color': danmaku.color,
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
        content, users = comment_nickname_recognize(user, content, False)

        try:
            size = int(self.request.get('size'))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid font size.',
            }))
            return

        try:
            color = int(self.request.get('color'), 16)
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid color.',
            }))
            return

        position = self.request.get('type')
        if not position in models.Danmaku_Positions:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid danmaku type.',
            }))
            return

        allow_share = self.request.get('allow_share')
        if allow_share == 'true':
            allow_share = True
        else:
            allow_share = False

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

        danmaku = models.Danmaku(timestamp=timestamp, content=content, position=position, size=size, color=color, creator=user.key)
        danmaku_pool.danmaku_list.append(danmaku)
        danmaku_pool.put()
        video.update_hot_score(HOT_SCORE_PER_DANMAKU)
        video.last_updated = datetime.now()
        video.put()

        danmaku_record = models.ActivityRecord(creator=user.key, activity_type='danmaku', timestamp=danmaku.timestamp, content=danmaku.content, video=video.key, clip_index=clip_index, public=allow_share)
        danmaku_record.put()
        user.comments_num += 1
        user.put()

        if len(users) != 0:
            mentioned_message = models.MentionedComment(receivers=users, sender=user.key, comment_type='danmaku', timestamp=danmaku.timestamp, content=danmaku.content, video=video.key, clip_index=clip_index)
            mentioned_message.put()
        
        self.response.out.write(json.dumps({
            'content': danmaku.content,
            'timestamp': danmaku.timestamp,
            'created': danmaku.created.strftime("%m-%d %H:%M"),
            'created_seconds': models.time_to_seconds(danmaku.created),
            'creator': danmaku.creator.id(),
            'type': danmaku.position,
            'size': danmaku.size,
            'color': danmaku.color,
        }))
        
class Like(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        video = models.Video.get_by_id('dt'+video_id)
        if video is None:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        video.likes += 1
        video.update_hot_score(HOT_SCORE_PER_LIKE)
        video.last_updated = datetime.now()
        video.put()
        self.response.out.write(json.dumps({
            'error': False,
            'likes': video.likes,
        }))

class Hit(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'

        video = models.Video.get_by_id('dt'+video_id)
        if video is None:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        video.hits += 1
        video.update_hot_score(HOT_SCORE_PER_HIT)
        video.put()
        video.create_index('videos_by_hits', video.hits)
        uploader = video.uploader.get()
        uploader.videos_watched += 1
        uploader.put()

        self.response.out.write(json.dumps({
            'error': False,
            'hits': video.hits,
        }))
