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

        for i in range(0, 1000):
            # logging.info(i)
            v1.danmaku_counter += 1
            v1.put()
            content = '233'
            length = random.random()*15
            for j in range(0, int(length)):
                content += '3'
            # for j in range(0, 100):
            #     if random.random() > 0.4:
            #         content += '3'
            models.Danmaku(video=v1.key, timestamp=random.random()*840, content=content, protected=False, creator='test_user_name').put();
        
        # logging.info(models.Danmaku.query(models.Danmaku.order==5000).get().content)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Data initialized.')
