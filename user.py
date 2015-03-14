from views import *

class Space(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        page_size = models.DEFAULT_PAGE_SIZE
        try:
            page = int(self.request.get('page'))
            if page < 1:
                raise ValueError('Negative')
        except ValueError:
            page = 1

        context = {}
        context['videos'] = []

        total_found = host.videos_submitted
        total_pages = math.ceil(total_found/float(page_size))
        videos = []
        if total_found != 0 and page <= total_pages:
            offset = (page - 1) * page_size
            videos = models.Video.query(models.Video.uploader==host.key).order(-models.Video.created).fetch(offset=offset, limit=page_size)
        
        # logging.info(videos)
        for i in range(0, len(videos)):
            # logging.info(videos[i])
            video = videos[i]
            video_info = video.get_basic_info()
            if video.playlist_belonged != None:
                playlist = video.playlist_belonged.get()
                video_info['playlist_title'] = playlist.title
            context['videos'].append(video_info)

        context['total_found'] = total_found
        context.update(self.get_page_range(page, total_pages) )

        auth = self.auth
        if (not auth.get_user_by_session()) or int(user_id) != self.user.key.id():
            host.space_visited += 1
            host.put()

        context['host'] = host.get_public_info()
        context['host'].update(host.get_statistic_info())
        self.render('space', context)

class SpacePlaylist(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        page_size = models.DEFAULT_PAGE_SIZE
        try:
            page = int(self.request.get('page'))
            if page < 1:
                raise ValueError('Negative')
        except ValueError:
            page = 1

        context = {}
        context['playlists'] = []

        total_found = host.playlists_created
        total_pages = math.ceil(total_found/float(page_size))
        playlists = []
        if total_found != 0 and page <= total_pages:
            offset = (page - 1) * page_size
            playlists = models.PlayList.query(models.PlayList.creator==host.key).order(-models.PlayList.modified).fetch(offset=offset, limit=page_size)
        
        for i in range(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_basic_info()
            context['playlists'].append(info)

        context['total_found'] = total_found
        context.update(self.get_page_range(page, total_pages) )

        context['host'] = host.get_public_info()
        context['host'].update(host.get_statistic_info())
        self.render('space_playlist', context)

class SpaceBoard(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        context = {}
        context['host'] = host.get_public_info()
        context['host'].update(host.get_statistic_info())
        self.render('space_board', context)


class Subscribe(BaseHandler):
    @login_required
    def post(self, user_id):
        self.response.headers['Content-Type'] = 'application/json'
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not found',
            }))
            return

        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'cannot subscribe self'
            }))
            return

        l = len(user.subscriptions)
        if host.key not in user.subscriptions:
            if l >= 1000:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'You have reached subscriptions limit.'
                }))
                return
        
            user.subscriptions.append(host.key)
            user.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
            host.subscribers_counter += 1
            host.put()
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'already subscribed'
            }))

class Unsubscribe(BaseHandler):
    @login_required
    def post(self, user_id):
        self.response.headers['Content-Type'] = 'application/json'
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not found'
            }))
            return

        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'cannot unsubscribe self'
            }))
            return

        try:
            user.subscriptions.remove(host.key)
            user.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
            host.subscribers_counter -= 1
            host.put()
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not subscribed'
            }))
