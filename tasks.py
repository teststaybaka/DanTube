from views import *
from watch import Danmaku

class UpdateIndex(BaseHandler):
    def get(self):
        q = taskqueue.Queue('Update_index')
        videos = {}
        while True:
            tasks = q.lease_tasks(3600, 400)
            for t in tasks:
                data = json.loads(t.payload)
                video_id = data['video']
                if video_id not in videos:
                    videos[video_id] = {
                        'hit': False,
                        'like': False,
                        'hotscore': 0.0,
                        'score_counter': 0,
                    }

                video = videos[video_id]
                if data['kind'] == 'hit':
                    video['hit'] = True
                    video['hotscore'] = video['hotscore']*99/100 + models.time_to_seconds(t.eta)/100
                    video['score_counter'] += 1
                elif data['kind'] == 'comment':
                    video['hotscore'] = video['hotscore']*99/100 + models.time_to_seconds(t.eta)/100
                    video['score_counter'] += 1
                else: # like or dislike
                    video['like'] = True
                
            q.delete_tasks(tasks)
            if len(tasks) < 400:
                break

        for video_id, data in videos.iteritems():
            video = ndb.Key('Video', video_id).get()
            if not video.deleted:
                if data['score_counter']:
                    video.hot_score = video.hot_score*pow(99.0/1000, data['score_counter']) + data['hotscore']
                    video.put()

                if data['hit']:
                    video.create_index('videos_by_hits', video.hits)

                if data['like']:
                    video.create_index('videos_by_likes', video.likes)

class FlushDanmaku(BaseHandler):
    def get(self):
        q = taskqueue.Queue('FlushDanmaku')
        clips = set()
        while True:
            tasks = q.lease_tasks(3600, 100)
            for t in tasks:
                clips.add(int(t.payload))

            q.delete_tasks(tasks)
            if len(tasks) < 100:
                break

        for clip_id in clips:
            clip = ndb.Key('VideoClip', int(clip_id)).get()
            danmaku_list = clip.danmaku_buffer
            advanced_danmaku_list = clip.advanced_danmaku_buffer
            clip.danmaku_buffer = []
            clip.advanced_danmaku_buffer = []
            clip.put()

            if danmaku_list:
                try:
                    pool = gcs.open('/danmaku/'+str(clip_id)+'/danmaku', 'r')
                    danmaku_list = json.loads(pool.read()) + [Danmaku.format_danmaku(danmaku) for danmaku in danmaku_list]
                    pool.close()
                except NotFoundError:
                    pass

                pool = gcs.open('/danmaku/'+str(clip_key.id())+'/danmaku', 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
                pool.write(json.dumps(danmaku_list))
                pool.close()

            if advanced_danmaku_list:
                try:
                    pool = gcs.open('/danmaku/'+str(clip_id)+'/advanced', 'r')
                    advanced_danmaku_list = json.loads(pool.read()) + [Danmaku.format_advanced_danmaku(danmaku) for  danmaku in advanced_danmaku_list]
                    pool.close()
                except NotFoundError:
                    pass

                pool = gcs.open('/danmaku/'+str(clip_key.id())+'/advanced', 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
                pool.write(json.dumps(advanced_danmaku_list))
                pool.close()

class NewActivity(BaseHandler):
    def get(self):
        q = taskqueue.Queue('Activity')
        users = set()
        while True:
            tasks = q.lease_tasks(3600, 1000)
            for t in tasks:
                upid = int(t.payload)
                subscriptions = models.Subscription.query(models.Subscription.uper==ndb.Key('User', upid)).fetch(keys_only=True)
                for subscription in subscriptions:
                    users.add(int(subscription.key.id().split('s:')[1]))

            q.delete_tasks(tasks)
            if len(tasks) < 1000:
                break

        for uid in users:
            user = ndb.Key('User', uid).get()
            if not user.check_new_subscription:
                user.check_new_subscription = True
                user.put()
