from views import *

class VideoPageTest(webapp2.RequestHandler):
    def get(self):
        query = models.Video.query()
        for entry in query:
            entry.key.delete()

        models.Video.Create('https://www.youtube.com/watch?v=wknTl2ZMkzg', 'test_user_name', 'aaa', 'Test', 'Anime', 'Continuing Anime')
        models.Video.Create('https://www.youtube.com/watch?v=M7lc1UVf-VE', 'test_user_name', 'aaa', 'Test', 'Anime', 'Continuing Anime')

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Data initialized.')

class DanmakuTest(webapp2.RequestHandler):
    def get(self):
        query = models.Video.query()
        for entry in query:
            entry.key.delete()
        danmaku = models.Danmaku.query()
        for entry in danmaku:
            entry.key.delete()

        v1 = models.Video.Create('https://www.youtube.com/watch?v=wknTl2ZMkzg', 'test_user_name', 'aaa', 'Test', 'Anime', 'Continuing Anime')
        models.Video.Create('https://www.youtube.com/watch?v=M7lc1UVf-VE', 'test_user_name', 'aaa', 'Test', 'Anime', 'Continuing Anime')

        for i in xrange(0, 1000):
            # logging.info(i)
            v1.danmaku_counter += 1
            v1.put()
            content = '233'
            length = random.random()*15
            for j in xrange(0, int(length)):
                content += '3'
            # for j in xrange(0, 100):
            #     if random.random() > 0.4:
            #         content += '3'
            models.Danmaku(video=v1.key, timestamp=random.random()*840, content=content, protected=False, creator='test_user_name').put();
        
        # logging.info(models.Danmaku.query(models.Danmaku.order==5000).get().content)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Data initialized.')

class Notify(webapp2.RequestHandler):
    def get(self):
        # ns = models.Notification.query().fetch()
        # for n in ns:
        #     n.key.delete()

        user = ndb.Key('User', 6681749341863936).get()
        # n = models.Notification(receiver=user.key, note_type='warning', title='SDFsdf', content='XXXXXXXXXXXXXXXXXX')
        # n.put()
        user.notification_counter = 2
        user.new_notifications = 2
        user.put()

class Home(webapp2.RequestHandler):
    def get(self):
        template = env.get_template('template/admin.html')
        self.response.write(template.render())

class Feedbacks(webapp2.RequestHandler):
    def get(self):
        feedbacks = models.Feedback.query().fetch()
        for feedback in feedbacks:
            feedback.created_time = feedback.created.strftime("%Y-%m-%d %H:%M")

        context = {'feedbacks': feedbacks}
        template = env.get_template('template/admin_feedbacks.html')
        self.response.write(template.render(context))

class Reports(webapp2.RequestHandler):
    def get(self):
        reports = models.Report.query().fetch()
        for report in reports:
            report.created_time = report.created.strftime("%Y-%m-%d %H:%M")

        context = {'reports': reports}
        template = env.get_template('template/admin_reports.html')
        self.response.write(template.render(context))

def delete_multi(entities):
    for e in entities:
        e.delete()

def delete_search_multi(doc_index):
    while True:
        # Get a list of documents populating only the doc_id field and extract the ids.
        document_ids = [document.doc_id for document in doc_index.get_range(ids_only=True)]
        if not document_ids:
            break
        # Delete the documents for the given ids from the Index.
        doc_index.delete(document_ids)

class DeleteVideos(webapp2.RequestHandler):
    def get(self):
        delete_search_multi(search.Index(name='videos_by_created'))
        delete_search_multi(search.Index(name='videos_by_likes'))
        delete_search_multi(search.Index(name='videos_by_hits'))
        delete_search_multi(search.Index(name='playlists_by_modified'))
        
        delete_multi(models.Video.query().fetch(keys_only=True))
        delete_multi(models.VideoClip.query().fetch(keys_only=True))
        delete_multi(models.VideoClipList.query().fetch(keys_only=True))
        delete_multi(models.VideoIDFactory.query().fetch(keys_only=True))
        delete_multi(models.LikeRecord.query().fetch(keys_only=True))
        delete_multi(models.ViewRecord.query().fetch(keys_only=True))
        delete_multi(models.DanmakuRecord.query().fetch(keys_only=True))
        delete_multi(models.MentionedRecord.query().fetch(keys_only=True))
        delete_multi(models.Comment.query().fetch(keys_only=True))
        delete_multi(models.Subscription.query().fetch(keys_only=True))
        delete_multi(models.Notification.query().fetch(keys_only=True))
        delete_multi(models.Playlist.query().fetch(keys_only=True))
        delete_multi(models.PlaylistDetail.query().fetch(keys_only=True))
        
        user_detail = models.User.get_detail_key(ndb.Key('User', 5730082031140864)).get()
        logging.info(user_detail.space_visited)
        logging.info(user_detail.videos_submitted)
        logging.info(user_detail.videos_watched)

        user_detail.space_visited = 0
        user_detail.videos_submitted = 0
        user_detail.videos_watched = 0
        user_detail.playlists_created = 0
        user_detail.put()

class DeleteSearch(webapp2.RequestHandler):
    def get(self):
        doc_index  = search.Index(name='videos_by_hits')
        # looping because get_range by default returns up to 100 documents at a time
        while True:
            # Get a list of documents populating only the doc_id field and extract the ids.
            document_ids = [document.doc_id
                            for document in doc_index.get_range(ids_only=True)]
            if not document_ids:
                break
            # Delete the documents for the given ids from the Index.
            doc_index.delete(document_ids)
        user_detail = models.User.get_detail_key(ndb.Key('User', 5730082031140864)).get()
        logging.info(user_detail.space_visited)
        logging.info(user_detail.videos_submitted)
        logging.info(user_detail.videos_watched)

        user_detail.space_visited = 0
        user_detail.videos_submitted = 0
        user_detail.videos_watched = 0
        user_detail.put()

class DeleteAll(webapp2.RequestHandler):
    def get(self):
        delete_search_multi(search.Index(name='videos_by_created'))
        delete_search_multi(search.Index(name='videos_by_likes'))
        delete_search_multi(search.Index(name='videos_by_hits'))
        delete_search_multi(search.Index(name='playlists_by_modified'))
        
        delete_multi(models.Video.query().fetch(keys_only=True))
        delete_multi(models.VideoClip.query().fetch(keys_only=True))
        delete_multi(models.VideoClipList.query().fetch(keys_only=True))
        delete_multi(models.VideoIDFactory.query().fetch(keys_only=True))
        delete_multi(models.LikeRecord.query().fetch(keys_only=True))
        delete_multi(models.ViewRecord.query().fetch(keys_only=True))
        delete_multi(models.DanmakuRecord.query().fetch(keys_only=True))
        delete_multi(models.MentionedRecord.query().fetch(keys_only=True))
        delete_multi(models.Comment.query().fetch(keys_only=True))
        delete_multi(models.Subscription.query().fetch(keys_only=True))
        delete_multi(models.Notification.query().fetch(keys_only=True))
        delete_multi(models.Playlist.query().fetch(keys_only=True))
        delete_multi(models.PlaylistDetail.query().fetch(keys_only=True))
        delete_multi(models.UserToken.query().fetch(keys_only=True))
        delete_multi(models.User.query().fetch(keys_only=True))
        delete_multi(models.Unique.query().fetch(keys_only=True))
        delete_multi(models.UserDetail.query().fetch(keys_only=True))
        delete_multi(models.ReportComment.query().fetch(keys_only=True))
        delete_multi(models.MessageThread.query().fetch(keys_only=True))
        
class Nickname(webapp2.RequestHandler):
    def get(self):
        users = models.User.query().fetch()
        user_details = ndb.get_multi([models.User.get_detail_key(user.key) for user in users])
        for i in xrange(0, len(users)):
            user_details[i].nickname = users[i].nickname
        ndb.put_multi(user_details)

class TestCounter(webapp2.RequestHandler):
    def get(self):
        user = ndb.Key('User', 5865619656278016).get()
        logging.info(user.new_messages)
        user.new_messages -= 11
        logging.info(user.new_messages)
        user.put()
        logging.info(user.new_messages)