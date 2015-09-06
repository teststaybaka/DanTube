from views import *
import re

def playlist_author_required(handler):
    def check_author(self, playlist_id):
        user, playlist = ndb.get_multi([self.user_key, ndb.Key('Playlist', int(playlist_id))])
        self.user = user
        if not playlist:
            self.notify('Playlist not found.')
            return
        elif user.key != playlist.creator:
            self.notify('You are not allowed to edit this list.')
            return
        
        return handler(self, playlist)

    return check_author

def playlist_author_required_json(handler):
    def check_author(self, playlist_id):
        playlist_key = ndb.Key('Playlist', int(playlist_id))
        playlist, list_detail = ndb.get_multi([playlist_key, models.Playlist.get_detail_key(playlist_key)])
        if not playlist:
            self.json_response(True,  {'message': 'Playlist not found.'})
            return
        elif self.user_key != playlist.creator:
            self.json_response(True, {'message': 'You are not allowed to edit this list.'})
            return

        return handler(self, playlist, list_detail)

    return check_author

class PlaylistInfo(BaseHandler):
    def check_params(self):
        self.playlist_type = self.request.get('type')
        if self.playlist_type not in models.Playlist_Type:
            raise Exception('Invalid type.')

        self.title = self.request.get('title').strip()
        if not self.title:
            raise Exception('Title can\'t be empty.')
        elif models.ILLEGAL_REGEX.match(self.title):
            raise Exception('Title contains illegal characters.')
        elif len(self.title) > 400:
            raise Exception('Title too long.')

        self.intro = self.request.get('intro').strip()
        if len(self.intro) > 2000:
            raise Exception('Introduction too long')

    @login_required_json
    def create(self):
        try:
            self.check_params()
        except Exception, e:
            self.json_response(True, {'message': str(e)})
            return

        playlist = models.Playlist(creator=self.user_key, title=self.title, playlist_type=self.playlist_type, intro=self.intro)
        playlist.put()
        list_detail = models.PlaylistDetail(key=models.Playlist.get_detail_key(playlist.key))
        user_detail = self.user_detail_key.get()
        user_detail.playlists_created += 1
        ndb.put_multi([user_detail, list_detail])
        playlist.create_index()
        self.json_response(False)

    @login_required_json
    def edit(self, playlist_id):
        playlist = models.Playlist.get_by_id(int(playlist_id))
        if not playlist or playlist.creator != self.user_key:
            self.json_response(True, {'message': 'You are not allowed to edit this list.'})
            return

        try:
            self.check_params()
        except Exception, e:
            self.json_response(True, {'message': str(e)})
            return

        changed = False
        if playlist.title != self.title:
            playlist.title = self.title
            changed = True

        if playlist.intro != self.intro:
            playlist.intro = self.intro
            changed = True

        if not changed:
            self.json_response(True, {'message': 'Nothing changed.'})
            return

        playlist.modified = datetime.now()
        playlist.put()
        playlist.create_index()
        self.json_response(False)

class ManagePlaylist(BaseHandler):
    @login_required
    def get(self):
        user, user_detail = ndb.get_multi([self.user_key, self.user_detail_key])
        self.user = user
        context = {
            'user': user_detail.get_detail_info(),
            'list_keywords': self.get_keywords(),
        }
        self.render('manage_playlist', context)

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        playlist_type = self.request.get('type')
        keywords = self.get_keywords()
        if keywords:
            query_string = 'content: ' + keywords + ' AND uper: "' + str(user_key.id()) + '"'
            if playlist_type:
                query_string += ' AND type: "' + playlist_type + '"'
            try:
                context, playlists = self.search(query_string, 'playlists_by_modified', page_size)
            except Exception, e:
                logging.info('search error: '+str(e))
                self.json_response(True, {'message': 'Search failed.'})
                return
        else:
            cursor = models.Cursor(urlsafe=self.request.get('cursor'))
            if playlist_type:
                playlists, cursor, more = models.Playlist.query(ndb.AND(models.Playlist.creator==user_key, models.Playlist.playlist_type==playlist_type)).order(-models.Playlist.modified).fetch_page(page_size, start_cursor=cursor)
            else:
                playlists, cursor, more = models.Playlist.query(models.Playlist.creator==user_key).order(-models.Playlist.modified).fetch_page(page_size, start_cursor=cursor)
            context = {'cursor': cursor.urlsafe() if more else ''}

        context['playlists'] = []
        for i in xrange(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_info()
            context['playlists'].append(info)

        self.json_response(False, context)

class DeletePlaylist(BaseHandler):
    @login_required_json
    def post(self):
        user_key = self.user_key
        try:
            ids = self.get_ids()
            playlists = ndb.get_multi([ndb.Key('Playlist', int(identifier)) for identifier in ids])
            lists_detail = ndb.get_multi([models.Playlist.get_detail_key(ndb.Key('Playlist', int(identifier))) for identifier in ids])
        except ValueError:
            self.json_response(True, {'message': 'Invalid id'})
            return

        deleted_counter = 0
        for i in xrange(0, len(ids)):
            playlist = playlists[i]
            list_detail = lists_detail[i]
            if not playlist or user_key != playlist.creator:
                continue

            if playlist.playlist_type == 'Primary':
                videos = ndb.get_multi(list_detail.videos)
                for j in xrange(0, len(videos)):
                    video = videos[j]
                    video.playlist_belonged = None
                ndb.put_multi(videos)

            playlist.delete_index()
            list_detail.key.delete()
            playlist.key.delete()
            deleted_counter += 1

        user_detail = self.user_detail_key.get()
        user_detail.playlists_created -= deleted_counter
        user_detail.put()
        self.json_response(False)

class EditPlaylist(BaseHandler):
    @login_required
    @playlist_author_required
    def get(self, playlist):
        context = {'playlist': playlist.get_info()}
        self.render('edit_playlist', context)

    @login_required_json
    def post(self, playlist_id):
        page_size = models.STANDARD_PAGE_SIZE
        playlist_id = int(playlist_id)
        playlist_type = self.request.get('type')
        try:
            page = int(self.request.get('cursor'))
        except ValueError:
            page = 1

        list_detail = models.Playlist.get_detail_key(ndb.Key('Playlist', playlist_id)).get()
        if not list_detail:
            self.json_response(True, {'message': 'Playlist not found.'})
            return

        offset = (page - 1)*page_size
        video_keys = []
        indices = []
        if self.request.get('ascend'):
            for i in xrange(offset, min(len(list_detail.videos), offset + page_size)):
                video_keys.append(list_detail.videos[i])
                indices.append(i)
        else:
            for i in reversed(xrange(max(len(list_detail.videos) - offset - page_size, 0), len(list_detail.videos) - offset)):
                video_keys.append(list_detail.videos[i])
                indices.append(i)
        videos = ndb.get_multi(video_keys)

        context = {
            'videos': [],
            'cursor': page + 1 if len(videos) >= page_size else '',
            'videos_num': len(list_detail.videos),
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            index = indices[i]
            if playlist_type == 'Primary':
                video_info = video.get_basic_info()
            else:
                video_info = video.get_basic_info(playlist_id)
            video_info['index'] = index + 1
            context['videos'].append(video_info)

        self.json_response(False, context)

class SearchVideo(BaseHandler):
    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        playlist_type = self.request.get('type')
        keywords = self.get_keywords()
        res = re.match(r'dt\d+', keywords)
        if res:
            video_id = res.group(0)
            video = models.Video.get_by_id(video_id)
            if not video or video.deleted or (playlist_type == 'Primary' and video.uploader != user_key):
                videos = []
            else:
                videos = [video]
            context = {'cursor': ''}
        elif keywords:
            query_string = 'content: ' + keywords + ' AND uper: "' + str(user_key.id()) + '"'
            try:
                context, videos = self.search(query_string, 'videos_by_created', page_size)
            except Exception, e:
                self.json_response(True, {'message': 'Search error.'})
                return
        else:
            cursor = models.Cursor(urlsafe=self.request.get('cursor'))
            if playlist_type == 'Primary':
                videos, cursor, more = models.Video.query(models.Video.uploader==self.user_key).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
            else:
                videos, cursor, more = models.Video.query().order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
            context = {'cursor': cursor.urlsafe() if more else ''}
        
        context['videos'] = []
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            if playlist_type == 'Primary' and video.playlist_belonged:
                video_info['belonged'] = True
            else:
                video_info['belonged'] = False
            context['videos'].append(video_info)

        self.json_response(False, context)

class AddVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist, list_detail):
        user_key = self.user_key
        put_list = []
        if playlist.playlist_type == 'Primary':
            try:
                ids = self.get_ids()
                videos = ndb.get_multi([ndb.Key('Video', identifier) for identifier in ids])
            except ValueError:
                self.json_response(True, {'message': 'Invalid id'})
                return

            for i in xrange(0, len(ids)):
                video = videos[i]
                if not video or video.deleted or video.playlist_belonged or video.uploader != user_key:
                    continue

                if not list_detail.videos:
                    playlist.set_first_video(video)
                list_detail.videos.append(video.key)
                video.playlist_belonged = playlist.key
                put_list.append(video)
        else:
            try:
                ids = self.get_ids()
                video_keys = [ndb.Key('Video', identifier) for identifier in ids]
            except ValueError:
                self.json_response(True, {'message': 'Invalid id'})
                return

            for i in xrange(0, len(ids)):
                video_key = video_keys[i]
                if not list_detail.videos:
                    video = video_key.get()
                    playlist.set_first_video(video)

                try:
                    list_detail.videos.index(video_key)
                except ValueError:
                    list_detail.videos.append(video_key)

        playlist.videos_num = len(list_detail.videos)
        if playlist.videos_num > 1000:
            self.json_response(True, {'message': 'Too many videos in one playlist.'})
            return

        playlist.modified = datetime.now()
        ndb.put_multi([playlist, list_detail] + put_list)
        playlist.create_index()

        result = {'playlist': playlist.get_info()}
        self.json_response(False, result)

class RemoveVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist, list_detail):
        user_key = self.user_key
        put_list = []
        try:
            ids = self.get_ids()
            video_keys = [ndb.Key('Video', identifier) for identifier in ids]
        except ValueError:
            self.json_response(True, {'message': 'Invalid id'})
            return

        if playlist.playlist_type == 'Primary':
            videos = ndb.get_multi(video_keys)

        for i in xrange(0, len(ids)):
            video_key = video_keys[i]
            try:
                list_detail.videos.remove(video_key)
            except ValueError:
                continue

            if playlist.playlist_type == 'Primary':
                video = videos[i]
                if not video or video.deleted or video.playlist_belonged != playlist.key or video.uploader != user_key:
                    continue
                video.playlist_belonged = None
                put_list.append(video)
        
        if not list_detail.videos:
            playlist.reset_first_video()
        elif playlist.first_video != list_detail.videos[0]:
            playlist.set_first_video(list_detail.videos[0].get())

        playlist.videos_num = len(list_detail.videos)
        playlist.modified = datetime.now()
        ndb.put_multi([playlist, list_detail] + put_list)
        playlist.create_index()
        self.json_response(False)

class MoveVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist, list_detail):
        try:
            ori_idx = int(self.request.get('ori_idx')) - 1
            target_idx = int(self.request.get('target_idx')) - 1
            if ori_idx < 0 or ori_idx >= len(list_detail.videos) or target_idx < 0 or target_idx >= len(list_detail.videos):
                raise ValueError('Invalid')
        except ValueError:
            self.json_response(True, {'message': 'Invalid index.'})
            return

        if ori_idx == target_idx:
            self.json_response(False)
            return

        temp_key = list_detail.videos.pop(ori_idx)
        list_detail.videos.insert(target_idx, temp_key)
        if playlist.first_video != list_detail.videos[0]:
            playlist.set_first_video(list_detail.videos[0].get())
        
        playlist.modified = datetime.now()
        ndb.put_multi([playlist, list_detail])
        playlist.create_index()
        self.json_response(False)
