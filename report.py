from views import *
from watch import video_clip_exist_required_json, video_exist_required_json

class Feedback(BaseHandler):
    @login_required
    def get(self):
        self.render('feedback', {'feedback_category': models.Feedback_Category})

    @login_required_json
    def post(self):
        user = self.user
        category = self.request.get('category').strip()
        if not category:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Category must not be empty!',
            }))
            return
        elif not (category in models.Feedback_Category):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Category mismatch!'
            }))
            return

        subject = self.request.get('subject').strip()
        if not subject:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subject must not be empty!'
            }))
            return
        elif len(subject) > 400:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subject is too long!'
            }))
            return

        description = self.request.get('description').strip()
        if not description:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Description must not be empty!'
            }))
            return
        elif len(description) > 2000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Description is too long!'
            }))
            return

        feedback = models.Feedback(
            category = category,
            subject = subject,
            description = description,
            sender = user.key,
            sender_nickname = user.nickname,
        )
        feedback.put()
        
        self.response.out.write(json.dumps({
            'error': False
        }))

class Report(BaseHandler):
    @login_required_json
    @video_clip_exist_required_json
    def video(self, video, clip_index):
        user = self.user
        issue = self.request.get('issue').strip()
        if not issue:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Issue must not be empty!'
            }))
            return
        elif issue not in models.Video_Issues:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid issues!'
            }))
            return

        description = self.request.get('description').strip()

        report = models.ReportVideo(
            video = video.key,
            video_title = video.title,
            clip = video.video_clips[clip_index-1],
            clip_index = clip_index,
            issue = issue,
            description = description,
            reporter_nickname = user.nickname,
            reporter = user.key,
        )
        report.put()
        self.response.out.write(json.dumps({
            'error': False,
        }))

    @login_required_json
    @video_exist_required_json
    def comment(self, video):
        user = self.user
        issue = self.request.get('issue').strip()
        if not issue:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Issue must not be empty!'
            }))
            return
        elif issue not in models.Comment_Issues:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid issues!'
            }))
            return

        try:
            comment_id = int(self.request.get('comment_id').strip())
        except Exception:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid id!'
            }))
            return

        is_inner = self.request.get('is_inner').strip()
        if not is_inner:
            comment = models.Comment.get_by_id(comment_id, video.key)
            if not comment:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Comment not found!'
                }))
                return
        else:

            try:
                inner_comment_id = int(self.request.get('inner_comment_id').strip())
            except Exception:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Invalid id!'
                }))
                return

            inner_comment = models.InnerComment.get_by_id(inner_comment_id, ndb.Key('Comment', comment_id, parent=video.key))
            if not inner_comment:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Comment not found!'
                }))
                return

        description = self.request.get('description').strip()

        if not is_inner:
            report = models.ReportComment(
                video = video.key, 
                video_title = video.title, 
                issue = issue, 
                description = description,
                reporter_nickname = user.nickname,
                reporter = user.key,
                comment = comment.key,
                content = comment.content,
                floorth = comment.floorth,
            )
        else:
            report = models.ReportComment(
                video = video.key, 
                video_title = video.title, 
                issue = issue, 
                description = description,
                reporter_nickname = user.nickname,
                reporter = user.key,
                comment = inner_comment.key,
                content = inner_comment.content,
                floorth = inner_comment.floorth,
                inner_floorth = inner_comment.inner_floorth,
            )
        report.put()
        self.response.out.write(json.dumps({
            'error': False,
        }))

    @login_required_json
    @video_clip_exist_required_json
    def danmaku(self, video, clip_index):
        user = self.user
        issue = self.request.get('issue').strip()
        if not issue:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Issue must not be empty!'
            }))
            return
        elif issue not in models.Danmaku_Issues:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid issues!'
            }))
            return

        try:
            pool_id = int(self.request.get('pool_id').strip())
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid id!'
            }))
            return

        pool_type = self.request.get('pool_type').strip()
        if pool_type == 'danmaku':
            pool_key = ndb.Key('DanmakuPool', pool_id)
        elif pool_type == 'advanced':
            pool_key = ndb.Key('AdvancedDanmakuPool', pool_id)
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid type.'
            }))
            return

        pool = pool_key.get()
        if not pool:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Pool not found.'
            }))
            return

        try:
            danmaku_index = int(self.request.get('danmaku_index').strip())
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid index!'
            }))
            return

        find = False
        for i in xrange(0, len(pool.danmaku_list)):
            danmaku = pool.danmaku_list[i]
            if danmaku.index == danmaku_index:
                find = True
                break
        if not find:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Danmaku not found!'
            }))
            return

        description = self.request.get('description').strip()

        report = models.ReportDanmaku(
            video = video.key,
            video_title = video.title,
            clip = video.video_clips[clip_index-1],
            clip_index = clip_index,
            issue = issue,
            description = description,
            reporter_nickname = user.nickname,
            reporter = user.key,
            pool = pool.key,
            danmaku_index = danmaku.index,
            timestamp = danmaku.timestamp,
            content = danmaku.content,
        )
        report.put()
        self.response.out.write(json.dumps({
            'error': False,
        }))
