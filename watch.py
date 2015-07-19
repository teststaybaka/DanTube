# -*- coding: utf-8 -*-
from views import *
import math

HOT_SCORE_PER_HIT = 5
HOT_SCORE_PER_DANMAKU = 5
HOT_SCORE_PER_COMMENT = 10
HOT_SCORE_PER_LIKE = 10

SUBTITLE_REG = re.compile(r'^\[\d+:\d{1,2}.\d{1,2}\].*$')
CODE_REG = re.compile(r'(^|.*[^a-zA-Z_$])(document|window|location|oldSetInterval|oldSetTimeout|XMLHttpRequest|XDomainRequest|jQuery|\$)([^a-zA-Z_$].*|$)')

def video_clip_exist_required(handler):
    def check_exist(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.notify('Video not found or deleted.', 404)
            return

        try:
            clip_index = int(self.request.get('index'))
        except ValueError:
            clip_index = 1
        if clip_index < 1 or clip_index > len(video.video_clips):
            self.notify('Video not found or deleted.', 404)
            return

        return handler(self, video, clip_index)

    return check_exist

def video_exist_required_json(handler):
    def check_exist(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        return handler(self, video)

    return check_exist

def video_clip_exist_required_json(handler):
    def check_exist(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if not video:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        try:
            clip_index = int(self.request.get('index'))
        except ValueError:
            clip_index = 1
        if clip_index < 1 or clip_index > len(video.video_clips):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video not found.'
            }))
            return

        return handler(self, video, clip_index)

    return check_exist

class Video(BaseHandler):
    @video_clip_exist_required
    def get(self, video, clip_index):
        user = self.user
        if user is not None:
            videos = [h.video for h in user.history]
            try:
                idx = videos.index(video.key)
                user.history.pop(idx)
            except ValueError:
                logging.info('not found')
            new_history = models.History(video=video.key, clip_index=clip_index)
            user.history.append(new_history)
            if len(user.history) > 100:
                user.history.pop(0)
            user.put()

        cur_clip, uploader = ndb.get_multi([video.video_clips[clip_index-1], video.uploader])
        video_info = video.get_basic_info()
        video_info['cur_vid'] = cur_clip.vid
        video_info['cur_subintro'] = cur_clip.subintro
        video_info['cur_index'] = clip_index
        video_info['clip_titles'] = video.video_clip_titles
        video_info['clip_range'] = range(0, len(video.video_clip_titles))
        if clip_index == 1:
            video_info['clip_range_min'] = 1
            video_info['clip_range_max'] = min(3, len(video.video_clip_titles))
        elif clip_index == len(video.video_clip_titles):
            video_info['clip_range_min'] = max(1, len(video.video_clip_titles) - 2)
            video_info['clip_range_max'] = len(video.video_clip_titles)
        else:
            video_info['clip_range_min'] = clip_index - 1
            video_info['clip_range_max'] = clip_index + 1

        subtitle_names = []
        for i in xrange(0, len(cur_clip.subtitle_names)):
            subtitle_names.append(cur_clip.subtitle_names[i])

        playlist_info = {}
        if video.playlist_belonged != None:
            playlist = video.playlist_belonged.get()
            playlist_info = playlist.get_basic_info()
            idx = playlist.videos.index(video.key)
            playlist_info['cur_index'] = idx
            playlist_info['videos'] = []
            videos = ndb.get_multi(playlist.videos)
            for i in xrange(0, len(videos)):
                playlist_info['videos'].append(videos[i].get_basic_info())
        context = {'video': video_info, 'uploader': uploader.get_public_info(user), 'playlist': playlist_info, 'subtitle_names': subtitle_names, 'video_issues': models.Video_Issues, 'comment_issues': models.Comment_Issues, 'danmaku_issues': models.Danmaku_Issues}
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
    for i in xrange(0, len(content)):
        if models.ILLEGAL_LETTER.match(content[i]) and state == 1:
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
    @video_exist_required_json
    def get_comment(self, video):
        page_size = 20
        page = self.get_page_number()

        offset = (page-1)*page_size
        comments = models.Comment.query(ancestor=video.key).order(-models.Comment.created).fetch(offset=offset, limit=page_size)
        result = {'error': False, 'comments':[], 'total_comments': video.comment_counter}
        creators = ndb.get_multi([comment.creator for comment in comments])
        for i in xrange(0, len(comments)):
            comment = comments[i]
            info = {
                'creator': creators[i].get_public_info(),
                'content': comment.content,
                'created': comment.created.strftime("%Y-%m-%d %H:%M"),
                'deleted': comment.deleted,
                'floorth': comment.floorth,
                'id': comment.key.id(),
                'inner_comment_counter': comment.inner_comment_counter,
                'inner_comments': [],
            }
            inner_comments = models.InnerComment.query(ancestor=comment.key).order(-models.InnerComment.created).fetch(offset=0, limit=3)
            inner_creators = ndb.get_multi([inner_comment.creator for inner_comment in inner_comments])
            for j in reversed(xrange(0, len(inner_comments))):
                inner_comment = inner_comments[j]
                inner_info = {
                    'creator': inner_creators[j].get_public_info(),
                    'content': inner_comment.content,
                    'created': inner_comment.created.strftime("%Y-%m-%d %H:%M"),
                    'deleted': inner_comment.deleted,
                    'inner_floorth': inner_comment.inner_floorth,
                    'id': inner_comment.key.id(),
                }
                info['inner_comments'].append(inner_info)
            result['comments'].append(info)

        result['total_pages'] = math.ceil(video.comment_counter/float(page_size))
        self.response.out.write(json.dumps(result))

    @video_exist_required_json
    def get_inner_comment(self, video):
        try:
            comment = models.Comment.get_by_id(int(self.request.get('comment_id')), video.key)
            if not comment:
                raise Exception('error')
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment not found'
            }))
            return

        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        offset = (page-1)*page_size
        inner_comments = models.InnerComment.query(ancestor=comment.key).order(models.InnerComment.created).fetch(offset=offset, limit=page_size)
        inner_creators = ndb.get_multi([inner_comment.creator for inner_comment in inner_comments])
        result = {'error': False, 'inner_comments': []}
        for i in xrange(0, len(inner_comments)):
            inner_comment = inner_comments[i]
            info = {
                'creator': inner_creators[i].get_public_info(),
                'content': inner_comment.content,
                'created': inner_comment.created.strftime("%Y-%m-%d %H:%M"),
                'deleted': inner_comment.deleted,
                'inner_floorth': inner_comment.inner_floorth,
                'id': inner_comment.key.id(),
            }
            result['inner_comments'].append(info)

        result['total_pages'] = math.ceil(comment.inner_comment_counter/float(page_size))
        self.response.out.write(json.dumps(result))

    @login_required_json
    @video_exist_required_json
    def comment_post(self, video):
        user = self.user
        content = self.request.get('content').strip()
        if not content:
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

        allow_share = self.request.get('allow-post-comment').strip()
        if allow_share:
            allow_share = True
        else:
            allow_share = False

        put_list = []
        comment = models.Comment.Create(video, user, content)
        video.comment_counter = comment.floorth
        video.update_hot_score(HOT_SCORE_PER_COMMENT)
        video.last_updated = datetime.now()
        put_list.append(video)

        comment_record = models.ActivityRecord(creator=user.key, activity_type='comment', floorth=comment.floorth, content=comment.content, video=video.key, video_title=video.title, public=allow_share)
        put_list.append(comment_record)
        user.comments_num += 1
        put_list.append(user)

        user_entries = []
        if len(users) != 0:
            mentioned_message = models.MentionedComment(receivers=users, sender=user.key, comment_type='comment', floorth=comment.floorth, content=comment.content, video=video.key, video_title=video.title)
            put_list.append(mentioned_message)

            user_entries = ndb.get_multi(users)
            for i in xrange(0, len(user_entries)):
                user_entries[i].new_mentions += 1
        ndb.put_multi(put_list + user_entries)

        self.response.out.write(json.dumps({
            'error': False,
        }))

    @login_required_json
    @video_exist_required_json
    def reply_post(self, video):
        try:
            comment = models.Comment.get_by_id(int(self.request.get('comment_id')), video.key)
            if not comment:
                raise Exception('error')
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Comment not found'
            }))
            return

        user = self.user
        content = self.request.get('content').strip()
        if not content:
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

        allow_share = self.request.get('allow-post-reply').strip()
        if allow_share:
            allow_share = True
        else:
            allow_share = False

        put_list = []
        inner_comment = models.InnerComment.Create(comment, user, content)
        video.last_updated = datetime.now()
        put_list.append(video)

        comment_record = models.ActivityRecord(creator=user.key, activity_type='inner_comment', floorth=inner_comment.floorth, inner_floorth=inner_comment.inner_floorth, content=inner_comment.content, video=video.key, video_title=video.title, public=allow_share)
        put_list.append(comment_record)
        user.comments_num += 1
        put_list.append(user)

        user_entries = []
        if len(users) != 0:
            mentioned_message = models.MentionedComment(receivers=users, sender=user.key, comment_type='inner_comment', floorth=inner_comment.floorth, inner_floorth=inner_comment.inner_floorth, content=inner_comment.content, video=video.key, video_title=video.title)
            put_list.append(mentioned_message)

            user_entries = ndb.get_multi(users)
            for i in xrange(0, len(user_entries)):
                user_entries[i].new_mentions += 1
        ndb.put_multi(put_list + user_entries)
        
        self.response.out.write(json.dumps({
            'error': False,
            'total_pages': math.ceil(comment.inner_comment_counter/float(models.DEFAULT_PAGE_SIZE)),
        }))

class Danmaku(BaseHandler):
    @video_clip_exist_required_json
    def get(self, video, clip_index):
        clip = video.video_clips[clip_index-1].get()
        danmaku_list = []
        danmaku_num = 0
        danmaku_pools = ndb.get_multi(clip.danmaku_pools)
        for danmaku_pool in danmaku_pools:
            danmaku_num += len(danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_danmaku(danmaku, danmaku_pool) for danmaku in danmaku_pool.danmaku_list]
        clip.danmaku_num = danmaku_num

        advanced_danmaku_num = 0
        if clip.advanced_danmaku_pool:
            advanced_danmaku_pool = clip.advanced_danmaku_pool.get()
            advanced_danmaku_num += len(advanced_danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool) for danmaku in advanced_danmaku_pool.danmaku_list]
        clip.advanced_danmaku_num = advanced_danmaku_num

        code_danmaku_num = 0
        if clip.code_danmaku_pool:
            code_danmaku_pool = clip.code_danmaku_pool.get()
            code_danmaku_num += len(code_danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_code_danmaku(danmaku, code_danmaku_pool) for danmaku in code_danmaku_pool.danmaku_list]
        clip.code_danmaku_num = code_danmaku_num
        clip.put()

        self.response.out.write(json.dumps({
            'error': False,
            'danmaku_list': danmaku_list,
        }))

    @login_required_json
    @video_clip_exist_required_json
    def post(self, video, clip_index):
        user = self.user
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

        position = self.request.get('type').strip()
        if not position in models.Danmaku_Positions:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid danmaku type.',
            }))
            return

        allow_share = self.request.get('allow-share').strip()
        if allow_share:
            allow_share = True
        else:
            allow_share = False

        reply_to = self.request.get('reply-to').strip()
        if reply_to:
            content = u'←' + content
            reply_to_key = ndb.Key('User', long(reply_to))
            if reply_to_key not in users: # TODO: Risk of empty user key
                users.append(reply_to_key)

        put_list = []
        clip = video.video_clips[clip_index-1].get()
        if len(clip.danmaku_pools) == 0:
            danmaku_pool = models.DanmakuPool()
            danmaku_pool.put()
            clip.danmaku_pools.append(danmaku_pool.key)
            put_list.append(clip)
        else:
            danmaku_pool = clip.danmaku_pools[-1].get()
            if len(danmaku_pool.danmaku_list) >= 1000:
                danmaku_pool = models.DanmakuPool()
                danmaku_pool.put()
                clip.danmaku_pools.append(danmaku_pool.key)
                if len(clip.danmaku_pools) > 20:
                    clip.danmaku_pools.pop(0).delete()
                put_list.append(clip)

        danmaku = models.Danmaku(index=danmaku_pool.counter, timestamp=timestamp, content=content, position=position, size=size, color=color, creator=user.key)
        danmaku_pool.danmaku_list.append(danmaku)
        danmaku_pool.counter += 1
        put_list.append(danmaku_pool)
        video.update_hot_score(HOT_SCORE_PER_DANMAKU)
        video.last_updated = datetime.now()
        put_list.append(video)

        danmaku_record = models.ActivityRecord(creator=user.key, activity_type='danmaku', timestamp=danmaku.timestamp, content=danmaku.content, video=video.key, video_title=video.title, clip_index=clip_index, public=allow_share)
        put_list.append(danmaku_record)
        user.comments_num += 1
        put_list.append(user)

        user_entries = []
        if len(users) != 0:
            mentioned_message = models.MentionedComment(receivers=users, sender=user.key, comment_type='danmaku', timestamp=danmaku.timestamp, content=danmaku.content, video=video.key, video_title=video.title, clip_index=clip_index)
            put_list.append(mentioned_message)

            user_entries = ndb.get_multi(users)
            for i in xrange(0, len(user_entries)):
                if user_entries[i]:
                    user_entries[i].new_mentions += 1
        ndb.put_multi(put_list + user_entries)
        
        self.response.out.write(json.dumps(Danmaku.format_danmaku(danmaku, danmaku_pool)))

    @staticmethod
    def format_danmaku(danmaku, danmaku_pool):
        return {
                    'content': danmaku.content,
                    'timestamp': danmaku.timestamp,
                    'created': danmaku.created.strftime("%m-%d %H:%M"),
                    'created_year': danmaku.created.strftime("%Y-%m-%d %H:%M"),
                    'created_seconds': models.time_to_seconds(danmaku.created),
                    'creator': danmaku.creator.id(),
                    'type': danmaku.position,
                    'size': danmaku.size,
                    'color': danmaku.color,
                    'pool_id': danmaku_pool.key.id(),
                    'index': danmaku.index,
                }

    @login_required_json
    @video_clip_exist_required_json
    def post_advanced(self, video, clip_index):
        user = self.user
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
        content = cgi.escape(content)

        try:
            birth_pos = (float(self.request.get('birth-position-X')), float(self.request.get('birth-position-Y')))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid birth position.',
            }))
            return

        try:
            death_pos = (float(self.request.get('death-position-X')), float(self.request.get('death-position-Y')))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid death position.',
            }))
            return

        try:
            speed = (float(self.request.get('speed-X')), float(self.request.get('speed-Y')))
            if speed[0] < 0 or speed[1] < 0:
                raise ValueError('Negative speed')
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid speed.',
            }))
            return

        try:
            longevity = float(self.request.get('longevity'))
            if longevity < 0:
                raise ValueError('Negative longevity')
        except Exception, e:
            longevity = 0

        if birth_pos[0] == death_pos[0] and birth_pos[1] == death_pos[1] and longevity == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Please specify longevity for static danmaku.',
            }))
            return
        if (birth_pos[0] != death_pos[0] and speed[0] == 0) or (birth_pos[1] != death_pos[1] and speed[1] == 0):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Please specify speed for moving danmaku.',
            }))
            return

        try:
            timestamp = float(self.request.get('timestamp'))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid timestamp.',
            }))

        if self.request.get('as-percent'):
            as_percent = True
        else:
            as_percent = False

        if self.request.get('relative'):
            relative = True
        else:
            relative = False

        custom_css = self.request.get('danmaku-css').strip()
        if not custom_css:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Empty CSS.',
            }))
            return

        clip = video.video_clips[clip_index-1].get()
        if not clip.advanced_danmaku_pool:
            advanced_danmaku_pool = models.AdvancedDanmakuPool()
        else:
            advanced_danmaku_pool = clip.advanced_danmaku_pool.get()

        if len(advanced_danmaku_pool.danmaku_list) >= 1000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Advanced danmaku pool is full.',
            }))
            return

        danmaku = models.AdvancedDanmaku(index=advanced_danmaku_pool.counter, timestamp=timestamp, content=content, birth_x=birth_pos[0], birth_y=birth_pos[1], death_x=death_pos[0], death_y=death_pos[1], speed_x=speed[0], speed_y=speed[1], longevity=longevity, css=custom_css, as_percent=as_percent, relative=relative, creator=user.key)
        advanced_danmaku_pool.danmaku_list.append(danmaku)
        advanced_danmaku_pool.counter += 1
        danmaku_record = models.ActivityRecord(creator=user.key, activity_type='danmaku', timestamp=danmaku.timestamp, content=danmaku.content, video=video.key, video_title=video.title, clip_index=clip_index, public=False)
        user.comments_num += 1

        ndb.put_multi([advanced_danmaku_pool, danmaku_record, user])
        if not clip.advanced_danmaku_pool:
            clip.advanced_danmaku_pool = advanced_danmaku_pool.key
            clip.put()
        
        self.response.out.write(json.dumps(Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool)))

    @staticmethod
    def format_advanced_danmaku(advanced_danmaku, danmaku_pool):
        return {
                    'content': advanced_danmaku.content,
                    'timestamp': advanced_danmaku.timestamp,
                    'created': advanced_danmaku.created.strftime("%m-%d %H:%M"),
                    'created_year': advanced_danmaku.created.strftime("%Y-%m-%d %H:%M"),
                    'created_seconds': models.time_to_seconds(advanced_danmaku.created),
                    'creator': advanced_danmaku.creator.id(),
                    'birth_x': advanced_danmaku.birth_x,
                    'birth_y': advanced_danmaku.birth_y,
                    'death_x': advanced_danmaku.death_x,
                    'death_y': advanced_danmaku.death_y,
                    'speed_x': advanced_danmaku.speed_x,
                    'speed_y': advanced_danmaku.speed_y,
                    'longevity': advanced_danmaku.longevity,
                    'css': advanced_danmaku.css,
                    'as_percent': advanced_danmaku.as_percent,
                    'relative': advanced_danmaku.relative,
                    'type': 'Advanced',
                    'pool_id': danmaku_pool.key.id(),
                    'index': advanced_danmaku.index,
                }

    @login_required_json
    @video_clip_exist_required_json
    def post_code(self, video, clip_index):
        user = self.user
        try:
            timestamp = float(self.request.get('timestamp'))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid timestamp.',
            }))

        content = self.request.get('content').strip()
        if not content:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Can not be empty.',
            }))
            return
        elif CODE_REG.match(content):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Code contains invalid keywords.',
            }))
            return
        content = cgi.escape(content)

        clip = video.video_clips[clip_index-1].get()
        if not clip.code_danmaku_pool:
            code_danmaku_pool = models.CodeDanmakuPool()
        else:
            code_danmaku_pool = clip.code_danmaku_pool.get()

        danmaku = models.CodeDanmaku(index=code_danmaku_pool.counter, timestamp=timestamp, content=content, creator=user.key)
        code_danmaku_pool.danmaku_list.append(danmaku)
        code_danmaku_pool.counter += 1
        danmaku_record = models.ActivityRecord(creator=user.key, activity_type='code', timestamp=danmaku.timestamp, content=danmaku.content, video=video.key, video_title=video.title, clip_index=clip_index, public=False)
        user.comments_num += 1

        ndb.put_multi([code_danmaku_pool, danmaku_record, user])
        if not clip.code_danmaku_pool:
            clip.code_danmaku_pool = code_danmaku_pool.key
            clip.put()

        self.response.out.write(json.dumps({
            'error': False,
        }))

    @staticmethod
    def format_code_danmaku(code_danmaku, danmaku_pool):
        return {
                    'content': code_danmaku.content,
                    'timestamp': code_danmaku.timestamp,
                    'created': code_danmaku.created.strftime("%m-%d %H:%M"),
                    'created_year': code_danmaku.created.strftime("%Y-%m-%d %H:%M"),
                    'created_seconds': models.time_to_seconds(code_danmaku.created),
                    'creator': code_danmaku.creator.id(),
                    'type': 'Code',
                    'pool_id': danmaku_pool.key.id(),
                    'index': code_danmaku.index,
                }

class Subtitles(BaseHandler):
    @video_clip_exist_required_json
    def get(self, video, clip_index):
        clip = video.video_clips[clip_index-1].get()
        try:
            s_index = int(self.request.get('subtitle_index'))
            if s_index < 1 or s_index > len(clip.subtitle_danmaku_pools):
                raise ValueError('Negative')
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subtitles not found.',
            }))
            return
            
        subtitle_danmaku_pool = clip.subtitle_danmaku_pools[s_index-1].get()
        self.response.out.write(json.dumps(Subtitles.format_subtitles(subtitle_danmaku_pool)))

    @staticmethod
    def format_subtitles(subtitle_danmaku_pool):
        return {
            'subtitles': subtitle_danmaku_pool.subtitles,
            'creator': subtitle_danmaku_pool.creator.id(),
            'created': subtitle_danmaku_pool.created.strftime("%m-%d %H:%M"),
            'created_year': subtitle_danmaku_pool.created.strftime("%Y-%m-%d %H:%M"),
            'created_seconds': models.time_to_seconds(subtitle_danmaku_pool.created),
            'pool_id': subtitle_danmaku_pool.key.id(),
        }

    @login_required_json
    @video_clip_exist_required_json
    def post(self, video, clip_index):
        user = self.user
        name = self.request.get('name').strip()
        if not name:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Name cannot be empty.',
            }))
            return
        elif len(name) > 350:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Name is too long.',
            }))
            return

        subtitles = self.request.get('subtitles').replace('\r', '').strip()
        if not subtitles:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subtitles can not be empty.',
            }))
            return
        subtitles = cgi.escape(subtitles)

        lines = subtitles.split('\n')
        for i in xrange(0, len(lines)):
            if not (lines[i] and SUBTITLE_REG.match(lines[i])):
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Subtitles format error.',
                }))
                return

        clip = video.video_clips[clip_index-1].get()
        subtitle_danmaku_pool = models.SubtitleDanmakuPool(subtitles=subtitles, creator=user.key)
        subtitle_danmaku_pool.put()
        clip.subtitle_names.append(name)
        clip.subtitle_danmaku_pools.append(subtitle_danmaku_pool.key)
        danmaku_record = models.ActivityRecord(creator=user.key, activity_type='subtitles', content=subtitles, video=video.key, video_title=video.title, clip_index=clip_index, public=False)
        user.comments_num += 1
        ndb.put_multi([clip, danmaku_record, user])

        self.response.out.write(json.dumps({
            'error': False,
        }))

class Like(BaseHandler):
    @login_required_json
    @video_exist_required_json
    def post(self, video):
        user = self.user
        video.likes += 1
        video.update_hot_score(HOT_SCORE_PER_LIKE)
        video.last_updated = datetime.now()
        video.put()

        self.response.out.write(json.dumps({
            'error': False,
            'likes': video.likes,
        }))

class Hit(BaseHandler):
    @login_required_json
    @video_exist_required_json
    def post(self, video):
        video.hits += 1
        video.update_hot_score(HOT_SCORE_PER_HIT)
        video.create_index('videos_by_hits', video.hits)
        uploader = video.uploader.get()
        uploader.videos_watched += 1

        ndb.put_multi([video, uploader])

        self.response.out.write(json.dumps({
            'error': False,
            'hits': video.hits,
        }))
