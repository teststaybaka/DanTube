# -*- coding: utf-8 -*-
from views import *
import math

HOT_SCORE_PER_HIT = 5
HOT_SCORE_PER_DANMAKU = 5
HOT_SCORE_PER_COMMENT = 10
HOT_SCORE_PER_LIKE = 10

SUBTITLE_REG = re.compile(r'^\[\d+:\d{1,2}.\d{1,2}\].*$')
CODE_REG = re.compile(r'(^|.*[^a-zA-Z_$])(document|window|location|oldSetInterval|oldSetTimeout|XMLHttpRequest|XDomainRequest|jQuery|\$)([^a-zA-Z_$].*|$)')

class Video(BaseHandler):
    def get(self, video_id):
        video_key = ndb.('Video', video_id)
        try:
            clip_index = int(self.request.get('index')) - 1
        except ValueError:
            clip_index = 0

        cur_clip = models.VideoClip.query(models.VideoClip.index==clip_index, ancestor=video_key).get()
        if not cur_clip:
            self.notify('Video not found or deleted.')
            return

        if self.user_info:
            user, video = ndb.get_multi([self.user_key, video_key])
            self.user = user
            try:
                record, is_new_hit = models.ViewRecord.get_or_create(user.key, video.key)
                if record.clip_index < clip_index:
                    record.clip_index = clip_index
                    record.put_async()
            except Exception, e:
                logging.warning('View record get/create failed!')
        else:
            video = video_key.get()

        video_info = video.get_full_info()
        video_info['cur_vid'] = cur_clip.vid
        video_info['cur_subintro'] = cur_clip.subintro
        video_info['cur_index'] = clip_index

        clip_titles = models.VideoClip.query(ancestor=video_key).order(models.VideoClip.index).fetch(projection=['title'])
        video_info['clip_titles'] = clip_titles
        video_info['clip_range'] = range(0, len(clip_titles))
        if clip_index == 0:
            video_info['clip_range_min'] = 0
            video_info['clip_range_max'] = min(2, len(clip_titles))
        elif clip_index == len(clip_titles) - 1:
            video_info['clip_range_min'] = max(0, len(clip_titles) - 2)
            video_info['clip_range_max'] = len(clip_titles)
        else:
            video_info['clip_range_min'] = clip_index - 1
            video_info['clip_range_max'] = clip_index + 1

        playlist_info = {}
        if video.playlist_belonged:
            uploader, uploader_detail, playlist, list_detail = ndb.get_multi([video.uploader, models.UserDetail.get_key(video.uploader), video.playlist_belonged, models.PlayList.get_detail_key(video.playlist_belonged)])
            playlist_info = playlist.get_info()
            idx = list_detail.videos.index(video.key)
            playlist_info['cur_index'] = idx
            playlist_info['videos'] = []
            videos = ndb.get_multi(list_detail.videos)
            for i in xrange(0, len(videos)):
                playlist_info['videos'].append(videos[i].get_basic_info())
        else:
            uploader, uploader_detail = ndb.get_multi([video.uploader, models.UserDetail.get_key(video.uploader)])

        if self.user_info and is_new_hit:
            video.hits += 1
            video.update_hot_score(HOT_SCORE_PER_HIT)
            uploader_detail.videos_watched += 1
            ndb.put_multi_async([video, uploader_detail])
            video.create_index('videos_by_hits', video.hits)

        uploader_info = uploader.get_public_info()
        uploader_info.update(uploader_detail.get_detail_info())
        if self.user_info:
            uploader_info['subscribed'] = bool(models.Subscription.query(models.Subscription.uper==uploader.key, ancestor=self.user_key).get(keys_only=True))
        else:
            uploader_info['subscribed'] = False

        context = {
            'video': video_info,
            'uploader': uploader_info,
            'playlist': playlist_info,
            'subtitle_names': cur_clip.subtitle_names,
            'subtitle_pool_ids': [pool.id() for pool in cur_clip.subtitle_danmaku_pools],
            'video_issues': models.Video_Issues,
            'comment_issues': models.Comment_Issues,
            'danmaku_issues': models.Danmaku_Issues,
        }
        self.render('video', context)

class Comment(BaseHandler):
    def get_comment(self, video_id):
        video_key = ndb.Key('Video', video_id)
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        comments, cursor, more = models.Comment.query(ancestor=video_key).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)
        
        result = {
            'comments': [],
            'cursor': cursor.urlsafe() if cursor else None
        }
        for i in xrange(0, len(comments)):
            comment = comments[i]
            info = comment.get_content()
            info['inner_comments'] = []

            inner_comments = models.Comment.query(ancestor=comment.key).order(-models.Comment.created).fetch(limit=3)
            for j in reversed(xrange(0, len(inner_comments))):
                inner_comment = inner_comments[j]
                inner_info = inner_comment.get_content()
                info['inner_comments'].append(inner_info)
            result['comments'].append(info)

        self.json_response(False, result)

    def get_inner_comment(self, video_id):
        video_key = ndb.Key('Video', video_id)
        page_size = models.STANDARD_PAGE_SIZE
        try:
            comment_id = int(self.request.get('comment_id'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid id.'})
            return
        comment_key = ndb.Key('Comment', comment_id, parent=video_key)

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        inner_comments, cursor, more = models.Comment.query(ancestor=comment_key).order(models.Comment.created).fetch_page(page_size, start_cursor=cursor)
        
        result = {
            'inner_comments': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(inner_comments)):
            inner_comment = inner_comments[i]
            info = inner_comment.get_content()
            result['inner_comments'].append(info)

        self.json_response(False, result)

    @login_required_json
    def comment_post(self, video_id):
        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'No content.'})
            return
        elif len(content) > 2000:
            self.json_response(True, {'message': 'Comment is too long.'})
            return
        content, users = self.at_users_content(content, True)

        user, video = ndb.get_multi([self.user_key, ndb.Key('Video', video_id)])
        if not video:
            self.json_response(True, {'message': 'Video not found.'})
            return

        try:
            comment = models.Comment.CreateComment(user=user, video=video, content=content)
        except Exception, e:
            logging.warning('Commne post failed!!!!!')
            self.json_response(True, {'message': 'Post failed. Please try again.'})
            return

        video.comment_counter = comment.floorth
        video.update_hot_score(HOT_SCORE_PER_COMMENT)
        video.updated = datetime.now()
        video.put_async()

        models.MentionedRecord.Create(users, comment)
        self.json_response(False)

    @login_required_json
    def reply_post(self, video_id):
        try:
            comment_id = int(self.request.get('comment_id'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid id.'})
            return

        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'No content.'})
            return
        elif len(content) > 2000:
            self.json_response(True, {'message': 'Comment too long.'})
            return
        content, users = self.at_users_content(content, True)

        user, comment = ndb.get_multi([self.user_key, ndb.Key('Comment', comment_id, parent=ndb.Key('Video', video_id))])
        if not comment:
            self.json_response(True, {'message': 'Comment not found.'})
            return

        try:
            inner_comment = models.Comment.CreateInnerComment(user=user, comment=comment, content=content)
        except Exception, e:
            logging.warning('Commne post failed!!!!!')
            self.json_response(True, {'message': 'Post failed. Please try again.'})
            return

        models.MentionedRecord.Create(users, inner_comment)
        self.json_response(False)

def video_clip_exist_required_json(handler):
    def check_exist(self, video_id):
        video_key = ndb.Key('Video', video_id)
        try:
            clip_index = int(self.request.get('index')) - 1
        except ValueError:
            clip_index = 0
        
        clip = models.VideoClip.query(models.VideoClip.index==clip_index, ancestor=video_key).get()
        if not clip:
            self.json_response(True, {'message': 'Video not found.'})
            return

        return handler(self, clip)

    return check_exist

class Danmaku(BaseHandler):
    @video_clip_exist_required_json
    def get(self, clip):
        danmaku_list = []
        danmaku_num = 0
        danmaku_pools = ndb.get_multi(clip.danmaku_pools)
        for danmaku_pool in danmaku_pools:
            danmaku_num += len(danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_danmaku(danmaku, danmaku_pool) for danmaku in danmaku_pool.danmaku_list]

        advanced_danmaku_num = 0
        if clip.advanced_danmaku_pool:
            advanced_danmaku_pool = clip.advanced_danmaku_pool.get()
            advanced_danmaku_num += len(advanced_danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool) for danmaku in advanced_danmaku_pool.danmaku_list]

        code_danmaku_num = 0
        if clip.code_danmaku_pool:
            code_danmaku_pool = clip.code_danmaku_pool.get()
            code_danmaku_num += len(code_danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_code_danmaku(danmaku, code_danmaku_pool) for danmaku in code_danmaku_pool.danmaku_list]

        if not clip.refresh and (clip.danmaku_num != danmaku_num or clip.advanced_danmaku_num != advanced_danmaku_num or clip.code_danmaku_num != code_danmaku_num):
            clip.refresh = True
            clip.put_async()

        self.json_response(False, {'danmaku_list': danmaku_list})

    @login_required_json
    @video_clip_exist_required_json
    def post(self, clip):
        user_key = self.user_key
        try:
            timestamp = float(self.request.get('timestamp'))
        except Exception, e:
            self.json_response(True, {'message': 'Invalid timestamp.'})
            return

        try:
            size = int(self.request.get('size'))
        except Exception, e:
            self.json_response(True, {'message': 'Invalid font size.'})
            return

        try:
            color = int(self.request.get('color'), 16)
        except Exception, e:
            self.json_response(True, {'message': 'Invalid color.'})
            return

        position = self.request.get('type')
        if position not in models.Danmaku_Positions:
            self.json_response(True, {'message': 'Invalid danmaku type.'})
            return

        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'Can not be empty.'})
            return
        elif len(content) > 350:
            self.json_response(True, {'message': 'Comment is too long.'})
            return
        content, users = self.at_users_content(content, False)

        reply_to = self.request.get('reply-to')
        if reply_to:
            try:
                reply_to = self.user_model.get_by_id(int(reply_to))
                if not reply_to:
                    raise ValueError('Not found.')
            except ValueError:
                self.json_response(True, {'message': 'Invalid user.'})
                return

            content = u'←' + content
            if reply_to.key not in users: # TODO: Risk of empty user key
                users.append(reply_to.key)

        try:
            danmaku_pool = clip.get_lastest_danmaku_pool()
        except Exception, e:
            self.json_response(True, {'message', 'Danmaku post error. Please try again.'})
            return

        danmaku = models.Danmaku(index=danmaku_pool.counter, timestamp=timestamp, content=content, position=position, size=size, color=color, creator=user.key)
        danmaku_pool.danmaku_list.append(danmaku)
        danmaku_pool.counter += 1

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        video.update_hot_score(HOT_SCORE_PER_DANMAKU)
        video.updated = datetime.now()
        danmaku_record = models.DanmakuRecord(parent=user_key, creator_snapshot=user.create_snapshot(), content=content, record_type='danmaku', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        ndb.put_multi_async([danmaku_pool, video, danmaku_record])

        models.MentionedRecord.Create(users, danmaku_record)
        self.json_response(False, Danmaku.format_danmaku(danmaku, danmaku_pool))

    @classmethod
    def format_danmaku(cls, danmaku, danmaku_pool):
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
    def post_advanced(self, clip):
        user_key = self.user_key
        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'Can not be empty.'})
            return
        elif len(content) > 350:
            self.json_response(True, {'message': 'Comment is too long.'})
            return
        content = cgi.escape(content)

        try:
            birth_pos = (float(self.request.get('birth-position-X')), float(self.request.get('birth-position-Y')))
        except Exception, e:
            self.json_response(True, {'message': 'Invalid birth position.'})
            return

        try:
            death_pos = (float(self.request.get('death-position-X')), float(self.request.get('death-position-Y')))
        except Exception, e:
            self.json_response(True, {'message': 'Invalid death position.'})
            return

        try:
            speed = (float(self.request.get('speed-X')), float(self.request.get('speed-Y')))
            if speed[0] < 0 or speed[1] < 0:
                raise ValueError('Negative speed')
        except Exception, e:
            self.json_response(True, {'message': 'Invalid speed.'})
            return

        try:
            longevity = float(self.request.get('longevity'))
            if longevity < 0:
                raise ValueError('Negative longevity')
        except Exception, e:
            longevity = 0

        if (birth_pos[0] != death_pos[0] and speed[0] == 0) or (birth_pos[1] != death_pos[1] and speed[1] == 0):
            self.json_response(True, {'message': 'Please specify speed for moving danmaku.'})
            return

        try:
            timestamp = float(self.request.get('timestamp'))
        except Exception, e:
            self.json_response(True, {'message': 'Invalid timestamp.'})
            return

        as_percent = bool(self.request.get('as-percent'))
        relative = bool(self.request.get('relative'))

        custom_css = self.request.get('danmaku-css').strip()
        if not custom_css:
            self.json_response(True, {'message': 'Empty CSS.'})
            return

        try:
            advanced_danmaku_pool = clip.get_advanced_danmaku_pool()
        except Exception, e:
            self.json_response(True, {'message', 'Advanced danmaku post error. Please try again.'})
            return
        if len(advanced_danmaku_pool.danmaku_list) >= 1000:
            self.json_response(True, {'message': 'Advanced danmaku pool is full.'})
            return

        danmaku = models.AdvancedDanmaku(index=advanced_danmaku_pool.counter, timestamp=timestamp, content=content, birth_x=birth_pos[0], birth_y=birth_pos[1], death_x=death_pos[0], death_y=death_pos[1], speed_x=speed[0], speed_y=speed[1], longevity=longevity, css=custom_css, as_percent=as_percent, relative=relative, creator=user.key)
        advanced_danmaku_pool.danmaku_list.append(danmaku)
        advanced_danmaku_pool.counter += 1

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        danmaku_record = models.DanmakuRecord(parent=user_key, create_snapshot=user.create_snapshot(), content=content, record_type='advanced', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        
        ndb.put_multi([advanced_danmaku_pool, danmaku_record])
        self.json_response(False, Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool))

    @classmethod
    def format_advanced_danmaku(cls, advanced_danmaku, danmaku_pool):
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
    def post_code(self, clip):
        user_key = self.user_key
        try:
            timestamp = float(self.request.get('timestamp'))
        except Exception, e:
            self.json_response(True, {'message': 'Invalid timestamp.'})
            return

        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'Can not be empty.'})
            return
        elif CODE_REG.match(content):
            self.json_response(True, {'message': 'Code contains invalid keywords.'})
            return
        content = cgi.escape(content)

        try:
            code_danmaku_pool = clip.get_code_danmaku_pool()
        except Exception, e:
            self.json_response(True, {'message', 'Code danmaku post error. Please try again.'})
            return
        if len(code_danmaku_pool.danmaku_list) >= 1000:
            self.json_response(True, {'message': 'Code danmaku pool is full.'})
            return

        danmaku = models.CodeDanmaku(index=code_danmaku_pool.counter, timestamp=timestamp, content=content, creator=user.key)
        code_danmaku_pool.danmaku_list.append(danmaku)
        code_danmaku_pool.counter += 1

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        danmaku_record = models.DanmakuRecord(parent=user_key, creator_snapshot=user.create_snapshot(), content=content, record_type='code', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        
        ndb.put_multi_async([code_danmaku_pool, danmaku_record])
        self.json_response(False)

    @classmethod
    def format_code_danmaku(cls, code_danmaku, danmaku_pool):
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
    def get(self, subtitles_pool_id):
        try:
            subtitle_danmaku_pool = models.SubtitleDanmakuPool.get_by_id(int(subtitles_pool_id))
            if not subtitle_danmaku_pool:
                raise Exception('Not found.')
        except Exception, e:
            self.json_response(True, {'message': 'Subtitles not found.'})
            return

        self.json_response(False, Subtitles.format_subtitles(subtitle_danmaku_pool))

    @classmethod
    def format_subtitles(cls, subtitle_danmaku_pool):
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
    def post(self, clip):
        user_key = self.user_key
        name = self.request.get('name').strip()
        if not name:
            self.json_response(True, {'message': 'Name cannot be empty.'})
            return
        elif len(name) > 350:
            self.json_response(True, {'message': 'Name is too long.'})
            return

        subtitles = self.request.get('subtitles').replace('\r', '').strip()
        if not subtitles:
            self.json_response(True, {'message': 'Subtitles can not be empty.'})
            return
        subtitles = cgi.escape(subtitles)

        lines = subtitles.split('\n')
        for i in xrange(0, len(lines)):
            if not (lines[i] and SUBTITLE_REG.match(lines[i])):
                self.json_response(True, {'message': 'Subtitles format error.'})
                return

        subtitle_danmaku_pool = SubtitleDanmakuPool(subtitles=subtitles, creator=user_key)
        subtitle_danmaku_pool.put()
        try:
            clip.append_new_subtitles(name, subtitle_danmaku_pool.key)
        except:
            self.json_response(True, {'message': 'Subtitles post error. Please try again.'})
            return

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        danmaku_record = models.DanmakuRecord(parent=user_key, create_snapshot=user.create_snapshot(), content=subtitles, record_type='subtitles', video=video.key, clip_index=clip.index, video_title=video.title)
        danmaku_record.put_async()
        self.json_response(False)

class Like(BaseHandler):
    @login_required_json
    def post(self, video_id):
        user_key = self.user_key
        video = models.Video.get_by_id(video_id)
        if not video:
            self.json_response(True, {'message': 'Video not found.'})
            return

        is_new = models.LikeRecord.unique_create(video.key, user_key)
        if is_new:
            video.likes += 1
            video.updated = datetime.now()
            video.update_hot_score(HOT_SCORE_PER_LIKE)
            video.put_async()
            video.create_index('videos_by_likes', video.likes)
        
        self.json_response(False)

class Unlike(BaseHandler):
    @login_required_json
    def post(self, video_id):
        user_key = self.user_key
        video_key = ndb.Key('Video', video_id)

        record = models.LikeRecord.query(models.LikeRecord.video==video_key, ancestor=user_key).get(keys_only=True)
        if record:
            record.delete_async()
            video = video_key.get()
            if video:
                video.likes -= 1
                video.put_async()
                video.create_index('videos_by_likes', video.likes)
        
        self.json_response(False)
