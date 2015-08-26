from views import *

class Contact(BaseHandler):
    @login_required
    def get(self):
        self.render('feedback', {'feedback_category': models.Feedback_Category})

    @login_required_json
    def post(self):
        category = self.request.get('category')
        if not category:
            self.json_response(True, {'message': 'Category must not be empty!',})
            return
        elif category not in models.Feedback_Category:
            self.json_response(True, {'message': 'Category invalid!'})
            return

        subject = self.request.get('subject').strip()
        if not subject:
            self.json_response(True, {'message': 'Subject must not be empty!'})
            return
        elif len(subject) > 400:
            self.json_response(True, {'message': 'Subject is too long!'})
            return

        description = self.request.get('description').strip()
        if not description:
            self.json_response(True, {'message': 'Description must not be empty!'})
            return
        elif len(description) > 2000:
            self.json_response(True, {'message': 'Description is too long!'})
            return

        feedback = models.Feedback(
            sender = self.user_key,
            category = category,
            subject = subject,
            description = description,
        )
        feedback.put()
        
        self.json_response(False)

class Report(BaseHandler):
    @login_required_json
    def video(self, video_id, clip_id):
        issue = self.request.get('issue')
        if not issue:
            self.json_response(True, {'message': 'Issue must not be empty!'})
            return
        elif issue not in models.Video_Issues:
            self.json_response(True, {'message': 'Invalid issues!'})
            return

        description = self.request.get('description').strip()
        report = models.ReportVideo(
            video_clip = ndb.Key('VideoClip', int(clip_id), parent=ndb.Key('Video', video_id)),
            issue = issue,
            description = description,
            reporter = self.user_key,
        )
        report.put()

        self.json_response(False)

    @login_required_json
    def comment(self, video_id, clip_id):
        issue = self.request.get('issue')
        if not issue:
            self.json_response(True, {'message': 'Issue must not be empty!'})
            return
        elif issue not in models.Comment_Issues:
            self.json_response(True, {'message': 'Invalid issues!'})
            return

        try:
            comment_id = int(self.request.get('comment_id'))
        except Exception:
            self.json_response(True, {'message': 'Invalid id!'})
            return

        video_key = ndb.Key('Video', video_id)
        comment_key = ndb.Key('Comment', comment_id, parent=video_key)
        is_inner = self.request.get('is_inner')
        if is_inner:
            try:
                inner_comment_id = int(self.request.get('inner_comment_id'))
            except Exception:
                self.json_response(True, {'message': 'Invalid id'})
                return

            comment_key = ndb.Key('Comment', inner_comment_id, parent=ndb.Key('Comment', comment_id))

        comment = comment_key.get()
        if not comment or comment.deleted:
            self.json_response(False)
            return
            
        description = self.request.get('description').strip()
        report = models.ReportComment(
            video = video_key,
            issue = issue,
            description = description,
            reporter = self.user_key,
            comment = comment_key,
            content = comment.content,
            user = comment.creator,
        )
        report.put()

        self.json_response(False)

    @login_required_json
    def danmaku(self, video_id, clip_id):
        issue = self.request.get('issue')
        if not issue:
            self.json_response(True, {'message': 'Issue must not be empty!'})
            return
        elif issue not in models.Danmaku_Issues:
            self.json_response(True, {'message': 'Invalid issues!'})
            return

        try:
            pool_id = int(self.request.get('pool_id'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid id!'})
            return

        pool_type = self.request.get('pool_type')
        if pool_type == 'danmaku':
            pool_key = ndb.Key('DanmakuPool', pool_id)
        elif pool_type == 'advanced':
            pool_key = ndb.Key('AdvancedDanmakuPool', pool_id)
        else:
            self.json_response(True, {'message': 'Invalid type.'})
            return

        try:
            danmaku_index = int(self.request.get('danmaku_index'))
        except ValueError:
            self.json_response(True, {'message': 'Invalid index!'})
            return

        pool = pool_key.get()
        if not pool:
            self.json_response(False)
            return
        else:
            indices = [danmaku.index for danmaku in pool.danmaku_list]
            try:
                i = indices.index(danmaku_index)
                danmaku = pool.danmaku_list[i]
            except ValueError:
                self.json_response(False)
                return

        description = self.request.get('description').strip()
        report = models.ReportDanmaku(
            video_clip = ndb.Key('VideoClip', int(clip_id), parent=ndb.Key('Video', video_id)),
            issue = issue,
            description = description,
            reporter = self.user_key,
            pool = pool_key,
            danmaku_index = danmaku.index,
            content = danmaku.content,
            user = danmaku.creator,
        )
        report.put()

        self.json_response(False)
