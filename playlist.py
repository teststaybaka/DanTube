from views import *
import re

def playlist_author_required(handler):
    def check_author(self, playlist_id):
        playlist = models.PlayList.get_by_id(int(playlist_id))
        if not playlist:
            self.notify('Playlist not found.')
            return
        elif self.user_key != playlist.creator:
            self.notify('You are not allowed to edit this list.')
            return
        
        return handler(self, playlist)

    return check_author

def playlist_author_required_json(handler):
    def check_author(self, playlist_id):
        user_key = self.user_key
        playlist = models.PlayList.get_by_id(int(playlist_id))
        if not playlist:
            self.json_response(True,  {'message': 'Playlist not found.'})
            return
        elif user_key != playlist.creator:
            self.json_response(True, {'message': 'You are not allowed to edit this list.'})
            return

        return handler(self, playlist)

    return check_author

class ManagePlaylist(BaseHandler):
    @login_required
    def get(self):
        context = {'list_keywords': self.get_keywords()}
        self.render('manage_playlist', context)

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        context = {'playlists': []}
        keywords = self.get_keywords()
        cursor_string = self.request.get('cursor')
        if keywords:
            query_string = 'content: ' + keywords + ' AND uper: "' + user_key.id() + '"'
            try:
                cursor = search.Cursor(web_safe_string=cursor_string)
                options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
                query = search.Query(query_string=query_string, options=options)
                index = search.Index(name='playlists_by_modified')
                result = index.search(query)

                cursor = result.cursor
                context['cursor'] = cursor.web_safe_string if cursor else None
                playlists = ndb.get_multi([ndb.Key(urlsafe=list_doc.doc_id) for list_doc in result.results])
            except Exception, e:
                logging.info('search error: '+e)
                self.json_response(True, {'message': 'Search failed.'})
                return
        else:
            cursor = models.Cursor(urlsafe=cursor_string)
            playlists, cursor, more = models.PlayList.query(models.PlayList.creator==user_key).order(-models.PlayList.modified).fetch_page(page_size, start_cursor=cursor)
            context['cursor'] = cursor.urlsafe() if cursor else None

        for i in xrange(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_basic_info()
            context['playlists'].append(info)

        self.json_response(False, context)

class PlaylistInfo(BaseHandler):
    def check_params(self):
        self.title = self.request.get('title').strip()
        if not self.title:
            raise Exception('Title can\'t be empty.')
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

        playlist = PlayList(creator=user.key, title=title, intro=intro)
        playlist.put()
        list_detail = models.PlayListDetail(id='lv'+str(playlist.key.id()))
        list_detail.put_async()
        # user.playlists_created += 1
        # user.put_async()
        playlist.create_index()

        self.json_response(False)

    @login_required_json
    @playlist_author_required_json
    def edit(self, playlist):
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

        if changed:
            playlist.modified = datetime.now()
            playlist.put_async()
            playlist.create_index()

        self.json_response(False)

class DeletePlaylist(BaseHandler):
    @login_required_json
    def post(self):
        user_key = self.user_key
        try:
            ids = self.get_ids()
            playlists = ndb.get_multi([ndb.Key('Playlist', int(identifier)) for identifier in ids])
            lists_detail = ndb.get_multi([models.PlayList.get_detail_key(playlist.key) for playlist in playlists])
        except ValueError:
            self.json_response(True, {'message': 'Invalid id'})
            return

        for i in xrange(0, len(ids)):
            playlist = playlists[i]
            list_detail = lists_detail[i]
            if not playlist or user_key != playlist.creator:
                continue

            videos = models.get_multi(list_detail.videos)
            for j in xrange(0, len(videos)):
                video = videos[j]
                video.playlist_belonged = None
            ndb.put_multi_async(videos)

            playlist.delete_index()
            lists_detail.key.delete_async()
            playlist.key.delete_async()

        # user.playlists_created -= len(deleted_ids)
        # user.put_async()
        self.json_response(False)

class EditPlaylist(BaseHandler):
    @login_required
    @playlist_author_required
    def get(self, playlist):
        context = {'playlist': playlist.get_basic_info()}
        self.render('edit_playlist', context)

    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        page_size = models.STANDARD_PAGE_SIZE
        try:
            page = int(self.request.get('cursor'))
        except ValueError:
            page = 1

        list_detail = models.PlayList.get_detail_key(playlist.key).get()
        offset = (page - 1)*page_size
        video_keys = []
        if not self.request.get('descending'):
            for i in xrange(offset, min(len(list_detail.videos), offset + page_size)):
                video_keys.append(list_detail.videos[i])
        else:
            for i in reversed(xrange(max(len(list_detail.videos) - offset - page_size, 0), len(list_detail.videos) - offset)):
                video_keys.append(list_detail.videos[i])
        videos = ndb.get_multi(video_keys)

        context = {
            'videos': [],
            'cursor': page + 1,
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            video_info['index'] = offset+i
            context['videos'].append(video_info)

        self.json_response(False, context)

class SearchVideo(BaseHandler):
    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.STANDARD_PAGE_SIZE

        keywords = self.get_keywords()
        cursor_string = self.request.get('cursor')
        res = re.match(r'dt\d+', keywords)
        context = {'videos': []}
        if res:
            video_id = res.group(0)
            video = models.Video.get_by_id(video_id)
            videos = []
            if video and video.uploader == user_key:
                videos = [video]
            context['cursor'] = None
        elif keywords:
            query_string = 'content: ' + keywords + ' AND uper: ' +user_key.id()
            try:
                cursor = search.Cursor(web_safe_string=cursor_string)
                options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
                query = search.Query(query_string=query_string, options=options)
                index = search.Index(name='videos_by_created')
                result = index.search(query)

                cursor = result.cursor
                context['cursor'] = cursor.web_safe_string if cursor else None
                videos = ndb.get_multi([ndb.Key(urlsafe=video_doc.doc_id) for video_doc in result.results])
            except Exception, e:
                self.json_response(True, {'message': 'Search error.'})
                return
        else:
            cursor = models.Cursor(urlsafe=cursor_string)
            videos, cursor, more = models.Video.query(models.Video.uploader==self.user_key).order(-models.Video.created).fetch_page(page_size, start_cursor=cursor)
            context['cursor'] = cursor.urlsafe() if cursor else None
        
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            if video.playlist_belonged:
                video_info['belonged'] = True
            else:
                video_info['belonged'] = False
            context['videos'].append(video_info)

        self.json_response(False, context)

class AddVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        user_key = self.user_key
        try:
            ids = get_ids()
            videos = ndb.get_multi([ndb.Key('Video', identifier) for identifier in ids])
        except ValueError:
            self.json_response(True, {'message': 'Invalid id'})
            return

        list_detail = models.PlayList.get_detail_key(playlist.key).get()
        put_list = []
        for i in xrange(0, len(ids)):
            video = videos[i]
            if not video or video.playlist_belonged or video.uploader != user_key:
                continue

            if not list_detail.videos:
                playlist.set_first_video(video)
            list_detail.videos.append(video.key)
            video.playlist_belonged = playlist.key
            put_list.append(video)

        playlist.videos_num = len(list_detail.videos)
        if playlist.videos_num > 1000:
            self.json_response(True, {'message': 'Too many videos in one playlist.'})
            return

        playlist.modified = datetime.now()
        ndb.put_multi_async([playlist, list_detail] + put_list)
        playlist.create_index()

        self.json_response(False)

class RemoveVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        user_key = self.user_key
        try:
            ids = get_ids()
            videos = ndb.get_multi([ndb.Key('Video', identifier) for identifier in ids])
        except ValueError:
            self.json_response(True, {'message': 'Invalid id'})
            return

        list_detail = models.PlayList.get_detail_key(playlist.key).get()
        put_list = []
        for i in xrange(0, len(ids)):
            video = videos[i]
            if not video or video.playlist_belonged != playlist.key or video.uploader != user_key:
                continue

            try:
                list_detail.videos.remove(video.key)
            except ValueError:
                continue
            video.playlist_belonged = None
            put_list.append(video)

        if not list_detail.videos:
            playlist.reset_first_video()
        elif playlist.first_video != list_detail.videos[0]:
            playlist.set_first_video(list_detail.videos[0].get())

        playlist.videos_num = len(list_detail.videos)
        playlist.modified = datetime.now()
        ndb.put_multi_async([playlist, list_detail] + put_list)
        playlist.create_index()

        self.json_response(False)

class MoveVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        try:
            ori_idx = int(self.request.get('ori_idx')) - 1
            target_idx = int(self.request.get('target_idx')) - 1
            list_detail = models.PlayList.get_detail_key(playlist.key).get()
            if ori_idx < 0 or ori_idx >= len(list_detail.videos) or target_idx < 0 or target_idx >= len(list_detail.videos) or ori_idx == target_idx:
                raise ValueError('Invalid')
        except ValueError:
            self.json_response(True, {'message': 'Index value error.'})
            return

        temp_key = list_detail.videos.pop(ori_idx)
        list_detail.videos.insert(target_idx, temp_key)
        if playlist.first_video != list_detail.videos[0]:
            playlist.set_first_video(list_detail.videos[0].get())
        
        playlist.modified = datetime.now()
        ndb.put_multi_async([playlist, list_detail])
        playlist.create_index()

        self.json_response(False)
