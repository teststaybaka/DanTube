from views import *

def host_info(handler):
    def check_host(self, user_id):
        host_id = int(host_id)
        host_key = self.user_model.get_key(host_id)
        host_detail_key = models.UserDetail.get_key(host_key)
        if self.user_info:
            host, host_detail, user = ndb.get_multi([host_key, host_detail_key, self.user_key])
            self.user = user
            if not host:
                self.notify('404 not found.', 404)
                return

            try:
                index = host_detail.recent_visitors.index(user.key)
                host_detail.recent_visitors.pop(index)
                host_detail.visitor_snapshots.pop(index)
            except ValueError:
                logging.info('not found')
            host_detail.recent_visitors.append(user.key)
            host_detail.visitor_snapshots.append(user.create_snapshot())
            if len(host_detail.recent_visitors) > 8:
                host_detail.recent_visitors.pop(0)
                host_detail.visitor_snapshots.pop(0)
            host_detail.space_visited += 1
            host_detail.put_async()
        else:
            host, host_detail = ndb.get_multi([host_key, host_detail_key])
            if not host:
                self.notify('404 not found.', 404)
                return

            host_detail.space_visited += 1
            host_detail.put_async()

        context = {}
        context['host'] = host.get_public_info()
        context['host'].update(host_detail.get_detail_info())
        context['host'].update(host_detail.get_visitor_info())
        if self.user_info:
            context['host']['subscribed'] = bool(models.Subscription.query(models.Subscription.uper==host.key, ancestor=user.key).get(keys_only=True))
        else:
            context['host']['subscribed'] = False

        return handler(self, context)

    return check_host

class Space(BaseHandler):
    @host_info
    def get(self, context):
        self.render('space', context)

    def post(self, user_id):
        host_key = self.user_model.get_key(int(user_id))
        page_size = models.STANDARD_PAGE_SIZE
        
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        videos, cursor, more = models.Video.query(models.Video.uploader==host_key).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
        
        context = {
            'videos': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            context['videos'].append(video_info)

        self.json_response(False, context)

class SpacePlaylist(BaseHandler):
    @host_info
    def get(self, context):
        self.render('space_playlist', context)

    def post(self, user_id):
        host_key = self.user_model.get_key(int(user_id))
        page_size = models.STANDARD_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        playlists, cursor, more = models.PlayList.query(models.PlayList.creator==host_key).order(-models.PlayList.modified).fetch_page(page_size, start_cursor=cursor)

        context = {
            'playlists': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_info()
            context['playlists'].append(info)

        self.json_response(False, context)

class FeaturedUpers(BaseHandler):
    @host_info
    def get(self, context):
        self.render('space_upers', context)

    def post(self, user_id):
        host_key = self.user_model.get_key(int(user_id))
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        uper_keys, cursor, more = models.Subscription.query(ancestor=host_key).order(-models.Subscription.score).fetch_page(page_size, start_cursor=cursor, projection=['uper'])
        upers = ndb.get_multi(uper_keys)

        if self.user_info:
            subscribed_keys = models.Subscription.query(ancestor=self.user_key).order(-models.Subscription.score).fetch(projection=['uper'])
        else:
            subscribed_keys = []

        context = {
            'upers': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(upers)):
            uper = upers[i]
            info = uper.get_public_info()
            if uper.key in subscribed_keys:
                info['subscribed'] = True
            else:
                info['subscribed'] = False
            context['upers'].append(info)

        self.json_response(False, context)

class Subscribe(BaseHandler):
    @login_required_json
    def post(self, user_id):
        user_key = self.user_key
        host_key = self.user_model.get_key(int(user_id))
        if user_key == host_key:
            self.json_response(True, {'message': 'You can\'t subscribe to yourself.'})
            return

        host = host_key.get()
        if not host:
            self.json_response(True, {'message': 'User not found.'})
            return

        is_new = models.Subscription.unique_create(host.key, user_key)
        if is_new:
            host.subscribers_counter += 1
            host.put_async()

        self.json_response(False)

class Unsubscribe(BaseHandler):
    @login_required_json
    def post(self, user_id):
        user_key = self.user_key
        host_key = self.user_model.get_key(int(user_id))

        subscription = models.Subscription.query(models.Subscription.uper==host_key, ancestor=user_key).get(keys_only=True)
        if subscription:
            subscription.delete_async()
            host = host_key.get()
            host.subscribers_counter -= 1
            host.put_async()

        self.json_response(False)
