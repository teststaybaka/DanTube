# -*- coding: utf-8 -*-
from views import *

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
            if clip_index >= len(clip_list.clips):
                self.redirect(self.uri_for('watch', video_id=video_id))
                return

            cur_clip = clip_list.clips[clip_index].get()
            video_info = video.get_full_info()
            video_info.update({
                'cur_clip_id': cur_clip.key.id(),
                'cur_vid': cur_clip.vid,
                'cur_subintro': cur_clip.subintro,
                'cur_index': clip_index,
                'clip_titles': clip_list.titles,
                'clip_range': range(0, len(clip_list.clips)),
            })
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
        uploader_detail = models.User.get_detail_key(video.uploader).get()
        uploader_info = models.User.get_snapshot_info(uploader_detail.nickname, video.uploader)
        uploader_info.update(uploader_detail.get_detail_info())
        change_snapshot = False
        if video.uploader_name != uploader_detail.nickname:
            video.uploader_name = uploader_detail.nickname
            change_snapshot = True

        # check video status for user
        is_watched = True
        video_info['liked'] = False
        uploader_info['subscribed'] = False
        if self.user_info:
            self.user = user = self.user_key.get()
            record, is_new_hit = models.ViewRecord.get_or_create(user.key, video.key)
            if list_id and playlist:
                if record.playlist != playlist.key:
                    record.playlist = playlist.key
                    record.put()
            else:
                if record.playlist:
                    record.playlist = None
                    record.put()

            # let browser use cookies to figure out where to continue
            if not self.request.cookies.get(video_id):
                self.response.set_cookie(video_id, str(record.clip_index)+'|'+str(record.timestamp), path='/')

            is_watched = not is_new_hit
            video_info['liked'] = models.LikeRecord.has_liked(self.user_key, video.key)
            uploader_info['subscribed'] = models.Subscription.has_subscribed(self.user_key, video.uploader)

        # update video entity
        if not is_watched:
            q = taskqueue.Queue('UpdateIndex')
            payload = {'video': video.key.id(), 'kind': 'hit'}
            q.add(taskqueue.Task(payload=json.dumps(payload), method='PULL'))
            video.hits += 1
            uploader_detail.videos_watched += 1
            ndb.put_multi([video, uploader_detail])
        elif change_snapshot:
            video.put()

        context = {
            'video': video_info,
            'uploader': uploader_info,
            'playlist': playlist_info,
            'video_issues': models.Video_Issues,
            'comment_issues': models.Comment_Issues,
            'danmaku_issues': models.Danmaku_Issues,
            'danmaku_list': json.dumps([danmaku.format() for danmaku in cur_clip.danmaku_buffer]),
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
    @classmethod
    def check_comment_floor(cls, comments, more):
        if not comments:
            return

        if not comments[-1].floorth and not more:
            comments[-1].floorth = 1
            comments[-1].put()
        if comments[-1].floorth:
            for i in reversed(xrange(0, len(comments)-1)):
                if not comments[i].floorth:
                    comments[i].floorth = comments[i+1].floorth + 1
                    comments[i].put()

    def get_comment(self, video_id):
        try:
            comment_id = int(self.request.get('comment_id'))
        except Exception:
            comment_id = ''

        video_key = ndb.Key('Video', video_id)
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        comments, cursor, more = models.Comment.query(ancestor=video_key).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)
        self.check_comment_floor(comments, more)

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
        comment = models.Comment(parent=video.key, video=video.key, video_title=video.title, creator=user.key, creator_name=user.nickname, content=content, share=allow_share)
        video.comment_counter += 1
        video.updated = datetime.now()
        ndb.put_multi([video, comment])

        q = taskqueue.Queue('UpdateIndex')
        payload = {'video': video.key.id(), 'kind': 'comment'}
        q.add(taskqueue.Task(payload=json.dumps(payload), method='PULL'))

        if users:
            deferred.defer(models.MentionedRecord.Create, users, comment.key)
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
        inner_comment = models.Comment(parent=ndb.Key('Comment', comment.key.id()), video=comment.key.parent(), video_title=comment.video_title, creator=user.key, creator_name=user.nickname, content=content, share=allow_share)
        comment.inner_comment_counter += 1
        ndb.put_multi([comment, inner_comment])

        if users:
            deferred.defer(models.MentionedRecord.Create, users, inner_comment.key)
        self.json_response(False)

def video_clip_exist_required_json(handler):
    def check_exist(self, video_id, clip_id):
        clip = ndb.Key('VideoClip', int(clip_id)).get()
        if not clip:
            self.json_response(True, {'message': 'Video not found.'})
            return

        return handler(self, clip)

    return check_exist

def flush_danmaku_pool(clip_key, new_danmaku_list, kind):
    danmaku_list = models.VideoClip.load_cloud_danmaku(clip_key, kind)
    if kind == 'danmaku':
        danmaku_list += [danmaku.format() for danmaku in new_danmaku_list]
    elif kind == 'advanced':
        danmaku_list += [danmaku.format() for danmaku in new_danmaku_list]
    elif kind == 'subtitles':
        danmaku_list += [danmaku.format() for danmaku in new_danmaku_list]
    else: # code
        danmaku_list += [danmaku.format() for danmaku in new_danmaku_list]
    models.VideoClip.save_cloud_danmaku(clip_key, kind, danmaku_list)

class Danmaku(BaseHandler):
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
                reply_to = models.User.get_by_id(int(reply_to))
                if not reply_to:
                    raise ValueError('Not found.')
            except ValueError:
                self.json_response(True, {'message': 'Invalid user.'})
                return

            content = u'←' + content
            if reply_to.key not in users:
                users.append(reply_to.key)

        danmaku = models.Danmaku(index=clip.danmaku_counter, timestamp=timestamp, content=content, position=position, size=size, color=color, creator=self.user_key, created=datetime.now())
        clip.danmaku_buffer.append(danmaku)
        clip.danmaku_counter += 1
        clip.danmaku_num += 1

        if len(clip.danmaku_buffer) > 50:
            danmaku_list = clip.danmaku_buffer
            clip.danmaku_buffer = []
            deferred.defer(flush_danmaku_pool, clip.key, danmaku_list, 'danmaku')

        user, video = ndb.get_multi([user_key, clip.video])
        danmaku_record = models.DanmakuRecord(creator=user_key, creator_name=user.nickname, content=content, danmaku_type='danmaku', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        ndb.put_multi([clip, danmaku_record])

        if users:
            deferred.defer(models.MentionedRecord.Create, users, danmaku_record.key)
        self.json_response(False, {'entry': danmaku.format()})

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

        danmaku = models.AdvancedDanmaku(index=clip.advanced_danmaku_counter, timestamp=timestamp, content=content, birth_x=birth_pos[0], birth_y=birth_pos[1], death_x=death_pos[0], death_y=death_pos[1], speed_x=speed[0], speed_y=speed[1], longevity=longevity, css=custom_css, as_percent=as_percent, relative=relative, creator=user_key, created=datetime.now())
        clip.advanced_danmaku_buffer.append(danmaku)
        clip.advanced_danmaku_counter += 1
        clip.advanced_danmaku_num += 1

        if len(clip.advanced_danmaku_buffer) > 10:
            danmaku_list = clip.advanced_danmaku_buffer
            clip.advanced_danmaku_buffer = []
            deferred.defer(flush_danmaku_pool, clip.key, danmaku_list, 'advanced')

        user, uploader, video = ndb.get_multi([user_key, clip.uploader, clip.video])
        danmaku_record = models.DanmakuRecord(creator=user_key, creator_name=user.nickname, content=content, danmaku_type='advanced', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        notification = models.Notification(receiver=uploader.key, subject='An advanced danmaku was posted.', content='An advanced danmaku was posted to your video, '+video.title+' ('+video.key.id()+'), by '+user.nickname+'. Please confirm or delete it if contains improper content.', note_type='info')
        uploader.new_notifications += 1
        ndb.put_multi([clip, uploader, danmaku_record, notification])

        self.json_response(False)
    
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

        danmaku = models.CodeDanmaku(index=clip.code_danmaku_counter, timestamp=timestamp, content=content, creator=user_key, created=datetime.now())
        clip.code_danmaku_counter += 1
        clip.code_danmaku_num += 1

        user, uploader, video = ndb.get_multi([user_key, clip.uploader, clip.video])
        danmaku_record = models.DanmakuRecord(creator=user_key, creator_name=user.nickname, content=content, danmaku_type='code', video=video.key, clip_index=clip.index, video_title=video.title, timestamp=timestamp)
        notification = models.Notification(receiver=uploader.key, subject='A code danmaku was posted.', content='A code danmaku was posted to your video, '+video.title+' ('+video.key.id()+'), by '+user.nickname+'. Please confirm carefully or delete it if it does something unknown/harmful to you/other users.', note_type='info')
        uploader.new_notifications += 1
        ndb.put_multi([clip, uploader, danmaku_record, notification])

        flush_danmaku_pool(clip.key, [danmaku], 'code')
        self.json_response(False)

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

        danmaku = models.SubtitlesDanmaku(index=clip.subtitles_counter, name=name, content=subtitles, creator=user_key, created=datetime.now())
        clip.subtitles_counter += 1
        clip.subtitles_num += 1

        user, uploader, video = ndb.get_multi([user_key, clip.uploader, clip.video])
        danmaku_record = models.DanmakuRecord(creator=user_key, creator_name=user.nickname, content=subtitles, danmaku_type='subtitles', video=video.key, clip_index=clip.index, video_title=video.title)
        notification = models.Notification(receiver=uploader.key, subject='A new subtitles was submitted.', content='A new subtitles, '+name+', was submitted to your video, '+video.title+' ('+video.key.id()+'), by '+user.nickname+'. Please confirm or delete it if improper.', note_type='info')
        uploader.new_notifications += 1
        ndb.put_multi([clip, uploader, danmaku_record, notification])

        flush_danmaku_pool(clip.key, [danmaku], 'subtitles')
        self.json_response(False)

class Like(BaseHandler):
    @login_required_json
    def post(self, video_id):
        video = ndb.Key('Video', video_id).get()
        if not video or video.deleted:
            self.json_response(True, {'message': 'Video not found.'})
            return

        is_new = models.LikeRecord.unique_create(self.user_key, video.key)
        if is_new:
            video.likes += 1
            video.updated = datetime.now()
            video.put()
            
            q = taskqueue.Queue('UpdateIndex')
            payload = {'video': video.key.id(), 'kind': 'like'}
            q.add(taskqueue.Task(payload=json.dumps(payload), method='PULL'))

            self.json_response(False)
        else:
            self.json_response(True)

class Unlike(BaseHandler):
    @login_required_json
    def post(self, video_id):
        video_key = ndb.Key('Video', video_id)
        delete = models.LikeRecord.dislike(self.user_key, video_key)
        if delete:
            video = video_key.get()
            if video and not video.deleted:
                video.likes -= 1
                video.put()

                q = taskqueue.Queue('UpdateIndex')
                payload = {'video': video.key.id(), 'kind': 'like'}
                q.add(taskqueue.Task(payload=json.dumps(payload), method='PULL'))

            self.json_response(False)
        else:
            self.json_response(True)

class Watched(BaseHandler):
    @login_required_json
    def post(self, video_id):
        watched = models.ViewRecord.has_viewed(self.user_key, ndb.Key('Video', video_id))
        self.json_response(False, {'watched': watched})

class UpdatePeak(BaseHandler):
    def post(self, clip_id):
        api_key = self.request.get('API_Key')
        if api_key != self.app.config.get('API_Key'):
            self.json_response(True, {'message': 'Unauthorized request.'})
            return

        try:
            peak = int(self.request.get('peak'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid peak value.'})
            return

        clip = ndb.Key('VideoClip', int(clip_id)).get()
        if not clip:
            self.json_response(True, {'message': 'Target video not existed.'})
            return

        clip.peak = peak
        clip.put()
        self.json_response(False)

class Test(BaseHandler):
    def get(self):
        Expiration = str(models.time_to_seconds(datetime.now()) + 120)
        StringToSign = 'GET\n'+\
                        '\n'+\
                        '\n'+\
                        Expiration+'\n'+\
                        '/dantube-videos/test.mp4';
        # logging.info(StringToSign)
        signed = app_identity.sign_blob(StringToSign)
        # logging.info(signed[0])
        # logging.info(app_identity.get_service_account_name())
        url = 'https://storage.googleapis.com/dantube-videos/test.mp4' + "?GoogleAccessId=" + app_identity.get_service_account_name() + "&Expires=" + Expiration + "&Signature=" + urllib.quote(base64.b64encode(signed[1]), safe='')
        # logging.info(url);

        self.render('test', {'video_source': url})
