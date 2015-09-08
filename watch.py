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
        video_key = ndb.Key('Video', video_id)
        try:
            clip_index = int(self.request.get('index')) - 1
        except ValueError:
            clip_index = 0

        try:
            list_id = int(self.request.get('list'))
        except ValueError:
            list_id = None

        video, clip_list = ndb.get_multi([video_key, models.VideoClipList.get_key(video_id)])
        if not video:
            self.notify('Video not found.')
            return

        # load video/clip info
        if video.deleted:
            video_info = video.get_basic_info()
            video_info['deleted'] = True
        else:
            cur_clip = clip_list.clips[clip_index].get()
            video_info = video.get_full_info()
            video_info['cur_clip_id'] = cur_clip.key.id()
            video_info['cur_vid'] = cur_clip.vid
            video_info['cur_subintro'] = cur_clip.subintro
            video_info['cur_index'] = clip_index
            video_info['clip_titles'] = clip_list.titles
            video_info['clip_range'] = range(0, len(clip_list.clips))
            if clip_index == 0:
                video_info['clip_range_min'] = 0
                video_info['clip_range_max'] = min(2, len(clip_list.clips))
            elif clip_index == len(clip_list.clips) - 1:
                video_info['clip_range_min'] = max(0, len(clip_list.clips) - 2)
                video_info['clip_range_max'] = len(clip_list.clips)
            else:
                video_info['clip_range_min'] = clip_index - 1
                video_info['clip_range_max'] = clip_index + 1

        # load playlist info
        if list_id is not None:
            playlist_key = ndb.Key('Playlist', list_id)
        else:
            playlist_key = video.playlist_belonged

        playlist_info = {}
        if playlist_key:
            playlist, list_detail = ndb.get_multi([playlist_key, models.Playlist.get_detail_key(playlist_key)])
            if playlist:
                playlist_info = playlist.get_info()
                idx = list_detail.videos.index(video_key)
                playlist_info['cur_index'] = idx
                min_idx = max(0, idx - 4)
                remain = 4 - (idx - min_idx)
                max_idx = min(len(list_detail.videos), idx + 6 + remain)
                if min_idx > 0:
                    playlist_info['cursor_prev'] = min_idx
                if max_idx < len(list_detail.videos):
                    playlist_info['cursor_next'] = max_idx

                videos = ndb.get_multi(list_detail.videos[min_idx:max_idx])
                playlist_info['videos'] = []
                for i in xrange(0, len(videos)):
                    list_video = videos[i]
                    if list_id is not None:
                        list_video_info = list_video.get_basic_info(list_id)
                    else:
                        list_video_info = list_video.get_basic_info()
                    list_video_info['index'] = min_idx + i
                    playlist_info['videos'].append(list_video_info)

                if list_id is not None:
                    video_info['list_id'] = list_id

        if video.deleted:
            context = {
                'video': video_info,
                'playlist': playlist_info,
            }
            self.render('video', context)
            return

        # update uploader info
        uploader, uploader_detail = ndb.get_multi([video.uploader, models.User.get_detail_key(video.uploader)])
        snapshot = uploader.create_snapshot()
        uploader_info = uploader.get_public_info()
        uploader_info.update(uploader_detail.get_detail_info())
        change_snapshot = False
        if video.uploader_snapshot.to_dict() != snapshot.to_dict():
            video.uploader_snapshot = snapshot
            change_snapshot = True

        # check video status for user
        if self.user_info:
            self.user = user = self.user_key.get()
            try:
                record, is_new_hit = models.ViewRecord.get_or_create(user.key, video.key)
            except TransactionFailedError, e:
                is_new_hit = False
                logging.error('View record get/create failed!')
            else:
                record.clip_index = clip_index
                if not is_new_hit:
                    record.created = datetime.now()
                if list_id and playlist:
                    record.playlist = playlist.key
                else:
                    record.playlist = None
                record.put()

            video_info['watched'] = not is_new_hit
            video_info['liked'] = bool(models.LikeRecord.query(models.LikeRecord.video==video.key, ancestor=self.user_key).get(keys_only=True))
            uploader_info['subscribed'] = bool(models.Subscription.query(models.Subscription.uper==uploader.key, ancestor=self.user_key).get(keys_only=True))
        else:
            video_info['watched'] = True
            video_info['liked'] = False
            uploader_info['subscribed'] = False

        # update video entity
        if not video_info['watched']:
            video.hits += 1
            video.update_hot_score(HOT_SCORE_PER_HIT)
            uploader_detail.videos_watched += 1
            ndb.put_multi([video, uploader_detail])
            video.create_index('videos_by_hits', video.hits)
        elif change_snapshot:
            video.put()

        context = {
            'video': video_info,
            'uploader': uploader_info,
            'playlist': playlist_info,
            'subtitle_names': [cur_clip.subtitle_names[i] for i in xrange(0, len(cur_clip.subtitle_danmaku_pools)) if cur_clip.subtitle_approved[i]],
            'subtitle_pool_ids': [cur_clip.subtitle_danmaku_pools[i].id() for i in xrange(0, len(cur_clip.subtitle_danmaku_pools)) if cur_clip.subtitle_approved[i]],
            'video_issues': models.Video_Issues,
            'comment_issues': models.Comment_Issues,
            'danmaku_issues': models.Danmaku_Issues,
        }
        self.render('video', context)

class GetPlaylistVideo(BaseHandler):
    def post(self, video_id, playlist_id):
        page_size = models.STANDARD_PAGE_SIZE
        playlist_id = int(playlist_id)
        list_detail = models.Playlist.get_detail_key(ndb.Key('Playlist', playlist_id)).get()
        if not list_detail:
            self.json_response(True, {'message': 'Playlist not found.'})
            return

        playlist_type = self.request.get('playlist_type')
        try:
            cursor = int(self.request.get('cursor'))
        except Exception:
            self.json_response(True, {'message': 'Invalid cursor'})
            return

        result = {}
        if self.request.get('type') == 'next':
            min_idx = cursor
            max_idx = min(len(list_detail.videos), cursor + page_size)
            if max_idx < len(list_detail.videos):
                result['cursor'] = max_idx
        else: # prev
            min_idx = max(0, cursor - page_size)
            max_idx = cursor
            if min_idx > 0:
                result['cursor'] = min_idx

        videos = ndb.get_multi(list_detail.videos[min_idx:max_idx])
        result['videos'] = []
        for i in xrange(0, len(videos)):
            video = videos[i]
            if playlist_type == 'Primary':
                video_info = video.get_basic_info()
            else:
                video_info = video.get_basic_info(playlist_id)
            video_info['index'] = i + min_idx
            result['videos'].append(video_info)

        self.json_response(False, result)

class CheckComment(BaseHandler):
    def post(self, video_id):
        try:
            comment_id = int(self.request.get('comment_id'))
        except Exception:
            comment_id = ''

        try:
            inner_comment_id = int(self.request.get('inner_comment_id'))
        except Exception:
            inner_comment_id = ''

        result = {}
        if comment_id:
            comment = ndb.Key('Comment', comment_id, parent=ndb.Key('Video', video_id)).get()
            if comment:
                comment_info = comment.get_content()
                comment_info['inner_comments'] = []

                if inner_comment_id:
                    inner_comment = ndb.Key('Comment', inner_comment_id, parent=ndb.Key('Comment', comment_id)).get()
                    if inner_comment:
                        inner_info = inner_comment.get_content()
                        comment_info['inner_comments'].append(inner_info)

                inner_comments = models.Comment.query(ancestor=ndb.Key('Comment', comment_id)).order(-models.Comment.created).fetch(limit=3)
                for j in xrange(0, len(inner_comments)):
                    inner_comment = inner_comments[j]
                    if len(comment_info['inner_comments']) >= 3 or (inner_comment_id and inner_comment_id == inner_comment.key.id()):
                        continue

                    inner_info = inner_comment.get_content()
                    comment_info['inner_comments'].append(inner_info)

                result['comment'] = comment_info

        if not result:
            self.json_response(True, {'message': 'No comment found'})
        else:
            self.json_response(False, result)

class Comment(BaseHandler):
    def get_comment(self, video_id):
        try:
            comment_id = int(self.request.get('comment_id'))
        except Exception:
            comment_id = ''

        video_key = ndb.Key('Video', video_id)
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        comments, cursor, more = models.Comment.query(ancestor=video_key).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)
        
        result = {
            'comments': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(comments)):
            comment = comments[i]
            if comment.key.id() == comment_id:
                continue

            info = comment.get_content()
            info['inner_comments'] = []

            inner_comments = models.Comment.query(ancestor=ndb.Key('Comment', comment.key.id())).order(-models.Comment.created).fetch(limit=3)
            for j in xrange(0, len(inner_comments)):
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

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        inner_comments, cursor, more = models.Comment.query(ancestor=ndb.Key('Comment', comment_id)).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)
        
        result = {
            'inner_comments': [],
            'cursor': cursor.urlsafe() if more else '',
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
        if not video or video.deleted:
            self.json_response(True, {'message': 'Video not found.'})
            return

        allow_share = bool(self.request.get('allow-post-comment'))
        try:
            comment = models.Comment.CreateComment(user=user, video=video, content=content, allow_share=allow_share)
        except TransactionFailedError, e:
            logging.error('Comment post failed!!!!!')
            self.json_response(True, {'message': 'Post failed. Please try again.'})
            return

        video.comment_counter = comment.floorth
        video.update_hot_score(HOT_SCORE_PER_COMMENT)
        video.updated = datetime.now()
        video.put()

        models.MentionedRecord.Create(users, comment.key)
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

        allow_share = bool(self.request.get('allow-post-reply'))
        try:
            inner_comment = models.Comment.CreateInnerComment(user=user, comment=comment, content=content, allow_share=allow_share)
        except TransactionFailedError, e:
            logging.error('Comment reply post failed!!!!!')
            self.json_response(True, {'message': 'Post failed. Please try again.'})
            return

        models.MentionedRecord.Create(users, inner_comment.key)
        self.json_response(False)

def video_clip_exist_required_json(handler):
    def check_exist(self, video_id, clip_id):
        clip = ndb.Key('VideoClip', int(clip_id), parent=ndb.Key('Video', video_id)).get()
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
            danmaku_list += [Danmaku.format_advanced_danmaku(danmaku, advanced_danmaku_pool) for danmaku in advanced_danmaku_pool.danmaku_list if danmaku.approved]

        code_danmaku_num = 0
        if clip.code_danmaku_pool:
            code_danmaku_pool = clip.code_danmaku_pool.get()
            code_danmaku_num += len(code_danmaku_pool.danmaku_list)
            danmaku_list += [Danmaku.format_code_danmaku(danmaku, code_danmaku_pool) for danmaku in code_danmaku_pool.danmaku_list if danmaku.approved]

        if not clip.refresh and (clip.danmaku_num != danmaku_num or clip.advanced_danmaku_num != advanced_danmaku_num or clip.code_danmaku_num != code_danmaku_num):
            clip.refresh = True
            clip.put()

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
        except TransactionFailedError, e:
            logging.error('Danmaku post failed!!!')
            self.json_response(True, {'message': 'Danmaku post error. Please try again.'})
            return

        danmaku = models.Danmaku(index=danmaku_pool.counter, timestamp=timestamp, content=content, position=position, size=size, color=color, creator=self.user_key)
        danmaku_pool.danmaku_list.append(danmaku)
        danmaku_pool.counter += 1

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        video.update_hot_score(HOT_SCORE_PER_DANMAKU)
        video.updated = datetime.now()
        danmaku_record = models.DanmakuRecord(parent=user_key, creator_snapshot=user.create_snapshot(), content=content, danmaku_type='danmaku', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        ndb.put_multi([danmaku_pool, video, danmaku_record])

        models.MentionedRecord.Create(users, danmaku_record.key)
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
        except TransactionFailedError, e:
            logging.error('Advanced danmaku post failed!!!')
            self.json_response(True, {'message': 'Advanced danmaku post error. Please try again.'})
            return
        if len(advanced_danmaku_pool.danmaku_list) >= 1000:
            self.json_response(True, {'message': 'Advanced danmaku pool is full.'})
            return

        danmaku = models.AdvancedDanmaku(index=advanced_danmaku_pool.counter, timestamp=timestamp, content=content, birth_x=birth_pos[0], birth_y=birth_pos[1], death_x=death_pos[0], death_y=death_pos[1], speed_x=speed[0], speed_y=speed[1], longevity=longevity, css=custom_css, as_percent=as_percent, relative=relative, creator=user_key)
        advanced_danmaku_pool.danmaku_list.append(danmaku)
        advanced_danmaku_pool.counter += 1

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        danmaku_record = models.DanmakuRecord(parent=user_key, creator_snapshot=user.create_snapshot(), content=content, danmaku_type='advanced', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        notification = models.Notification(receiver=user_key, subject='An advanced danmaku was posted.', content='An advanced danmaku was posted to your video: '+video.title+' ('+video.key.id()+') by '+user.nickname+'. Please confirm or delete it if contains improper content.', note_type='info')
        user.new_notifications += 1
        ndb.put_multi([user, advanced_danmaku_pool, danmaku_record, notification])
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
                    'approved': advanced_danmaku.approved,
                }

    @login_required_json
    @video_clip_exist_required_json
    def post_code(self, clip):
        user_key = self.user_key
        try:
            timestamp = float(self.request.get('timestamp'))
        except ValueError, e:
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
        except TransactionFailedError, e:
            logging.error('Code danmaku post failed!!!')
            self.json_response(True, {'message': 'Code danmaku post error. Please try again.'})
            return
        if len(code_danmaku_pool.danmaku_list) >= 100:
            self.json_response(True, {'message': 'Code danmaku pool is full.'})
            return

        danmaku = models.CodeDanmaku(index=code_danmaku_pool.counter, timestamp=timestamp, content=content, creator=user_key)
        code_danmaku_pool.danmaku_list.append(danmaku)
        code_danmaku_pool.counter += 1

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        danmaku_record = models.DanmakuRecord(parent=user_key, creator_snapshot=user.create_snapshot(), content=content, danmaku_type='code', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        notification = models.Notification(receiver=user_key, subject='A code danmaku was posted.', content='A code danmaku was posted to your video: '+video.title+' ('+video.key.id()+') by '+user.nickname+'. Please confirm carefully or delete it if it does something unknown/harmful to you/other users.', note_type='info')
        user.new_notifications += 1
        ndb.put_multi([user, code_danmaku_pool, danmaku_record, notification])
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
                    'approved': code_danmaku.approved,
                }

    @login_required_json
    @video_clip_exist_required_json
    def post_subtitles(self, clip):
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

        subtitle_danmaku_pool = models.SubtitleDanmakuPool(subtitles=subtitles, creator=user_key)
        subtitle_danmaku_pool.put()
        try:
            clip.append_new_subtitles(name, subtitle_danmaku_pool.key)
        except TransactionFailedError, e:
            logging.error('Subtitles post failed!!!')
            subtitle_danmaku_pool.key.delete_async()
            self.json_response(True, {'message': 'Subtitles submit error. Please try again.'})
            return

        user, video = ndb.get_multi([user_key, clip.key.parent()])
        danmaku_record = models.DanmakuRecord(parent=user_key, creator_snapshot=user.create_snapshot(), content=subtitles, danmaku_type='subtitles', video=video.key, clip_index=clip.index, video_title=video.title)
        notification = models.Notification(receiver=user_key, subject='A new subtitles was submitted.', content='A new subtitles, '+name+', was submitted to your video: '+video.title+' ('+video.key.id()+') by '+user.nickname+'. Please confirm or delete it if improper.', note_type='info')
        user.new_notifications += 1
        ndb.put_multi([user, danmaku_record, notification])
        self.json_response(False)

class Subtitles(BaseHandler):
    def get(self, subtitles_pool_id):
        subtitle_danmaku_pool = models.SubtitleDanmakuPool.get_by_id(int(subtitles_pool_id))
        if not subtitle_danmaku_pool:
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

class Like(BaseHandler):
    @login_required_json
    def post(self, video_id):
        video = ndb.Key('Video', video_id).get()
        if not video or video.deleted:
            self.json_response(True, {'message': 'Video not found.'})
            return
        try:
            is_new = models.LikeRecord.unique_create(video.key, self.user_key)
        except TransactionFailedError, e:
            logging.error('Like unique creation failed!!!')
            self.json_response(True, {'message': 'Like error. Please try again.'})
            return

        if is_new:
            video.likes += 1
            video.updated = datetime.now()
            video.update_hot_score(HOT_SCORE_PER_LIKE)
            video.put()
            video.create_index('videos_by_likes', video.likes)
            self.json_response(False)
        else:
            self.json_response(True)

class Unlike(BaseHandler):
    @login_required_json
    def post(self, video_id):
        user_key = self.user_key
        video_key = ndb.Key('Video', video_id)

        record = models.LikeRecord.query(models.LikeRecord.video==video_key, ancestor=user_key).get(keys_only=True)
        if record:
            record.delete()
            video = video_key.get()
            if video:
                video.likes -= 1
                video.put()
                video.create_index('videos_by_likes', video.likes)
            self.json_response(False)
        else:
            self.json_response(True)
