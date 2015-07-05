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