from views import *

def host_required(handler):
    def check_host(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        return handler(self, host)

    return check_host

def host_required_json(handler):
    def check_host(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'User not found.',
            }))
            return

        return handler(self, host)

    return check_host

class Space(BaseHandler):
    @host_required
    def get(self, host):
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        if not self.user:
            host.space_visited += 1
            host.put()
        elif host.key != self.user.key:
            try:
                idx = host.recent_visitors.index(self.user.key)
                host.recent_visitors.pop(idx)
            except ValueError:
                logging.info('not found')
            host.recent_visitors.append(self.user.key)
            if len(host.recent_visitors) > 8:
                host.recent_visitors.pop(0)
            host.space_visited += 1
            host.put()

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
            context['videos'].append(video_info)

        context['host'] = host.get_public_info(self.user)
        context['host'].update(host.get_statistic_info())
        context['host'].update(host.get_visitor_info())
        context.update(self.get_page_range(page, total_pages) )
        self.render('space', context)

class SpacePlaylist(BaseHandler):
    @host_required
    def get(self, host):
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        context['playlists'] = []
        total_found = host.playlists_created
        total_pages = math.ceil(total_found/float(page_size))
        playlists = models.PlayList.query(models.PlayList.creator==host.key).order(-models.PlayList.modified).fetch(offset=(page-1)*page_size, limit=page_size)
        
        for i in range(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_basic_info()
            context['playlists'].append(info)

        context['host'] = host.get_public_info(self.user)
        context['host'].update(host.get_statistic_info())
        context['host'].update(host.get_visitor_info())
        context.update(self.get_page_range(page, total_pages))
        self.render('space_playlist', context)

class FeaturedUpers(BaseHandler):
    @host_required
    def get(self, host):
        page_size = 20;
        page = self.get_page_number()

        context = {'users': []}
        total_found = len(host.subscriptions)
        total_pages = math.ceil(total_found/float(page_size))
        user_keys = []
        offset = (page-1)*page_size
        for i in range(0, page_size):
            if i+offset >= total_found:
                break
            user_keys.append(host.subscriptions[i+offset])
        
        users = ndb.get_multi(user_keys)
        for i in range(0, len(users)):
            user = users[i]
            info = user.get_public_info()
            info.update(user.get_statistic_info())
            context['users'].append(info)

        context['host'] = host.get_public_info(self.user)
        context['host'].update(host.get_statistic_info())
        context['host'].update(host.get_visitor_info())
        context.update(self.get_page_range(page, total_pages))
        self.render('space_upers', context)

class Subscribe(BaseHandler):
    @login_required_json
    @host_required_json
    def post(self, host):
        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You can\'t subscribe to yourself.'
            }))
            return

        if host.key in user.subscriptions:
            self.response.out.write(json.dumps({
                'error': True,
                'change': True,
                'message': 'Already subscribed.'
            }))
            return

        if len(user.subscriptions) >= 1000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You have reached the limit of subscriptions.'
            }))
            return
    
        user.subscriptions.append(host.key)
        host.subscribers_counter += 1
        ndb.put_multi([user, host])

        self.response.out.write(json.dumps({
            'error': False
        }))

class Unsubscribe(BaseHandler):
    @login_required_json
    @host_required_json
    def post(self, host):
        user = self.user
        try:
            user.subscriptions.remove(host.key)
            host.subscribers_counter -= 1
            ndb.put_multi([user, host])

            self.response.out.write(json.dumps({
                'error': False
            }))
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'change': True,
                'message': 'You didn\'t subscribe to the user.'
            }))
