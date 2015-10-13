from views import *

def host_info(handler):
    def check_host(self, user_id):
        host_key = ndb.Key('User', int(user_id))
        host_detail_key = models.User.get_detail_key(host_key)
        if self.user_info:
            host, host_detail, user = ndb.get_multi([host_key, host_detail_key, self.user_key])
            self.user = user
            if not host:
                self.notify('404 not found.', 404)
                return

            if host.key != user.key:
                try:
                    index = host_detail.recent_visitors.index(user.key)
                    host_detail.recent_visitors.pop(index)
                    host_detail.recent_visitor_names.pop(index)
                except ValueError:
                    logging.info('not found')
                host_detail.recent_visitors.append(user.key)
                host_detail.recent_visitor_names.append(user.nickname)
                if len(host_detail.recent_visitors) > 8:
                    host_detail.recent_visitors.pop(0)
                    host_detail.recent_visitor_names.pop(0)
                host_detail.space_visited += 1
                host_detail.put()
        else:
            host, host_detail = ndb.get_multi([host_key, host_detail_key])
            if not host:
                self.notify('404 not found.', 404)
                return

            host_detail.space_visited += 1
            host_detail.put()

        context = {}
        context['host'] = host.get_public_info()
        context['host'].update(host_detail.get_detail_info())
        context['host'].update(host_detail.get_visitor_info())
        if self.user_info:
            context['host']['subscribed'] = models.Subscription.has_subscribed(user.key, host.key)
        else:
            context['host']['subscribed'] = False

        return handler(self, context)

    return check_host

class SpaceVideo(BaseHandler):
    @host_info
    def get(self, context):
        self.render('space', context)

    def post(self, user_id):
        host_key = ndb.Key('User', int(user_id))
        page_size = models.STANDARD_PAGE_SIZE
        
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        videos, cursor, more = models.Video.query(models.Video.uploader==host_key).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
        
        context = {
            'videos': [],
            'cursor': cursor.urlsafe() if more else '',
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
        host_key = ndb.Key('User', int(user_id))
        page_size = models.STANDARD_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        playlists, cursor, more = models.Playlist.query(models.Playlist.creator==host_key).order(-models.Playlist.modified).fetch_page(page_size, start_cursor=cursor)

        context = {
            'playlists': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_info()
            context['playlists'].append(info)

        self.json_response(False, context)

class SpaceComment(BaseHandler):
    @host_info
    def get(self, context):
        self.render('space_comments', context)

    def post(self, user_id):
        host_key = ndb.Key('User', int(user_id))
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        comments, cursor, more = models.Comment.query(ndb.AND(models.Comment.creator==host_key, models.Comment.share==True)).order(-models.Comment.created).fetch_page(page_size, start_cursor=cursor)

        context = {
            'comments': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(comments)):
            comment = comments[i]
            content_info = comment.get_content()
            context['comments'].append(content_info)

        self.json_response(False, context)

class FeaturedUpers(BaseHandler):
    @host_info
    def get(self, context):
        self.render('space_upers', context)

    def post(self, user_id):
        host_key = ndb.Key('User', int(user_id))
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        subscriptions, cursor, more = models.Subscription.query(models.Subscription.user==host_key).order(-models.Subscription.score).fetch_page(page_size, start_cursor=cursor, projection=['uper'])
        uper_keys = [subscription.uper for subscription in subscriptions]
        upers = ndb.get_multi(uper_keys)

        if self.user_info:
            subscriptions = models.Subscription.query(models.Subscription.user==self.user_key).order(-models.Subscription.score).fetch(projection=['uper'])
            subscribed_keys = set([subscription.uper for subscription in subscriptions])
        else:
            subscribed_keys = set()

        context = {
            'upers': [],
            'cursor': cursor.urlsafe() if more else '',
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
        host_key = ndb.Key('User', int(user_id))
        if user_key == host_key:
            self.json_response(True, {'message': 'You can\'t subscribe to yourself.'})
            return

        host, user = ndb.get_multi([host_key, user_key])
        if not host:
            self.json_response(True, {'message': 'User not found.'})
            return

        try:
            is_new = models.Subscription.unique_create(user_key, host.key)
        except models.TransactionFailedError, e:
            logging.error('Subscription unique creation failed!!!')
            self.json_response(True, {'message': 'Subscription error. Please try again.'})
            return

        if is_new:
            host.subscribers_counter += 1
            user.subscription_counter += 1
            ndb.put_multi([host, user])

        self.json_response(False)

class Unsubscribe(BaseHandler):
    @login_required_json
    def post(self, user_id):
        user_key = self.user_key
        host_key = ndb.Key('User', int(user_id))

        delete = models.Subscription.unsubscribe(user_key, host_key)
        if delete:
            host, user = ndb.get_multi([host_key, user_key])
            host.subscribers_counter -= 1
            user.subscription_counter -= 1
            ndb.put_multi([host, user])

        self.json_response(False)
