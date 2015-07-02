from views import *
import re

def playlist_author_required(handler):
    def check_author(self, playlist_id):
        user = self.user
        playlist = models.PlayList.get_by_id(int(playlist_id))
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
        user = self.user
        playlist = models.PlayList.get_by_id(int(playlist_id))
        if not playlist:
            self.response.out.write(json.dumps({
                'error': True, 
                'message': 'Playlist not found.'
            }))
            return
        elif self.user.key != playlist.creator:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You are not allowed to edit this list.'
            }))
            return

        return handler(self, playlist)

    return check_author

class ManagePlaylist(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        context['playlists'] = []

        keywords = self.get_keywords()
        if keywords:
            context['list_keywords'] = keywords
            query_string = 'content: ' + keywords
            page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
            offset = (page - 1)*page_size
            try:
                options = search.QueryOptions(offset=offset, limit=page_size)
                query = search.Query(query_string=query_string, options=options)
                index = search.Index(name='playlists_by_user' + str(user.key.id()))
                result = index.search(query)                
                total_found = min(result.number_found, models.MAX_QUERY_RESULT)
                total_pages = math.ceil(total_found/float(page_size))
                playlists = ndb.get_multi([ndb.Key(urlsafe=list_doc.doc_id) for list_doc in result.results])
            except Exception, e:
                self.notify('Search error.')
                return
        else:
            total_found = user.playlists_created
            total_pages = math.ceil(total_found/float(page_size))
            playlists = []
            if total_found != 0 and page <= total_pages:
                offset = (page - 1) * page_size
                playlists = models.PlayList.query(models.PlayList.creator==self.user.key).order(-models.PlayList.modified).fetch(offset=offset, limit=page_size)

        for i in range(0, len(playlists)):
            playlist = playlists[i]
            info = playlist.get_basic_info()
            context['playlists'].append(info)

        context['total_found'] = total_found
        context.update(self.get_page_range(page, total_pages) )
        self.render('manage_playlist', context)

class PlaylistInfo(BaseHandler):
    def check_params(self):
        self.title = self.request.get('title').strip()
        if not self.title:
            return {
                'error': True,
                'message': 'Title can\'t be empty.'
            }
        elif len(self.title) > 400:
            return {
                'error': True,
                'message': 'Title too long.'
            }

        self.intro = self.request.get('intro').strip()
        if len(self.intro) > 2000:
            return {
                'error': True,
                'message': 'Introduction too long.'
            }

        return {
            'error': False,
        }

    @login_required_json
    def create(self):
        res = self.check_params()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        try:
            models.PlayList.Create(user=self.user, title=self.title, intro=self.intro)
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return
        
        self.response.out.write(json.dumps({
            'error': False,
        }))

    @login_required_json
    @playlist_author_required_json
    def edit(self, playlist):
        res = self.check_params()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        try:
            playlist.change_info(title=self.title, intro=self.intro)
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return
        
        self.response.out.write(json.dumps({
            'error': False,
        }))

class DeletePlaylist(BaseHandler):
    @login_required_json
    def post(self):
        user = self.user
        ids = self.request.POST.getall('ids[]')
        deleted_ids = []
        for i in range(0, len(ids)):
            try:
                playlist = models.PlayList.get_by_id(int(ids[i]))
                if (not playlist) or user.key != playlist.creator:
                    raise Exception('Error')
            except Exception, e:
                continue

            playlist.Delete()
            deleted_ids.append(ids[i])

        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No list deleted.'
            }))
            return
        user.playlists_created -= len(deleted_ids)
        user.put()

        self.response.out.write(json.dumps({
            'error': False, 
            'message': deleted_ids
        }))

class EditPlaylist(BaseHandler):
    @login_required
    @playlist_author_required
    def get(self, playlist):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {
            'playlist': playlist.get_basic_info()
        }
        context['videos'] = []

        requested_videos = []
        base = (page - 1)*page_size;
        for i in range(0, page_size):
            if base + i >= len(playlist.videos):
                break
            requested_videos.append(playlist.videos[base + i])

        videos = ndb.get_multi(requested_videos)
        for i in range(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            video_info['index'] = i + base + 1;
            context['videos'].append(video_info)

        context.update(self.get_page_range(page, math.ceil(len(playlist.videos)/float(page_size)) ) )
        self.render('edit_playlist', context=context)

class SearchVideo(BaseHandler):
    @login_required_json
    def post(self):
        user = self.user
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {'error': False}
        context['videos'] = []

        keywords = self.get_keywords()
        res = re.match(r'dt(\d+)', keywords)
        if res:
            video_id = res.group(1)
            video = models.Video.get_by_id('dt' + video_id)
            videos = []
            if video and video.uploader.id() == user.key.id():
                videos = [video]
            total_pages = 1
        elif keywords:
            query_string = 'content: ' + keywords
            page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
            offset = (page - 1)*page_size
            try:
                options = search.QueryOptions(offset=offset, limit=page_size)
                query = search.Query(query_string=query_string, options=options)
                index = search.Index(name='videos_by_user' + str(user.key.id()))
                result = index.search(query)                
                total_found = min(result.number_found, models.MAX_QUERY_RESULT)
                total_pages = math.ceil(total_found/float(page_size))
                videos = ndb.get_multi([ndb.Key(urlsafe=video_doc.doc_id) for video_doc in result.results])
            except Exception, e:
                self.response.out.write(json.dumps({
                    'error': True, 
                    'message': 'Search error.'
                }))
                return
        else:
            total_found = user.videos_submitted
            total_pages = math.ceil(total_found/float(page_size))
            videos = []
            if total_found != 0 and page <= total_pages:
                offset = (page - 1) * page_size
                videos = models.Video.query(models.Video.uploader==self.user.key).order(-models.Video.created).fetch(offset=offset, limit=page_size)
        
        # logging.info(videos)
        for i in range(0, len(videos)):
            # logging.info(videos[i])
            video = videos[i]
            video_info = video.get_basic_info()
            if video.playlist_belonged != None:
                video_info['belonged'] = True
            else:
                video_info['belonged'] = False
            context['videos'].append(video_info)

        context['cur_page'] = page
        context['total_pages'] = total_pages
        self.response.out.write(json.dumps(context))

class AddVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        user = self.user
        ids = self.request.POST.getall('ids[]')
        added_ids = []
        put_list = []
        for i in range(0, len(ids)):
            video_id = ids[i]
            video = models.Video.get_by_id('dt'+video_id)
            if (not video) or video.playlist_belonged != None or video.uploader != user.key or len(playlist.videos) > 2000:
                continue

            video.playlist_belonged = playlist.key
            put_list.append(video)
            playlist.videos.append(video.key)
            added_ids.append(video_id)

        if len(added_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video added.'
            }))
            return
        playlist.modified = datetime.now()
        ndb.put_multi([playlist] + put_list)

        self.response.out.write(json.dumps({
            'error': False, 
            'message': added_ids
        }))

class RemoveVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        user = self.user
        ids = self.request.POST.getall('ids[]')
        deleted_ids = []
        put_list = []
        for i in range(0, len(ids)):
            video_id = ids[i]
            video = models.Video.get_by_id('dt'+video_id)
            if (not video) or video.playlist_belonged.id() != playlist.key.id() or video.uploader.id() != user.key.id():
                continue

            try:
                idx = playlist.videos.index(video.key)
                playlist.videos.pop(idx)
                video.playlist_belonged = None
                put_list.append(video)
                deleted_ids.append(video_id)
            except Exception, e:
                continue

        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video removed.'
            }))
            return
        playlist.modified = datetime.now()
        ndb.put_multi([playlist] + put_list)

        self.response.out.write(json.dumps({
            'error': False, 
            'message': deleted_ids
        }))

class MoveVideo(BaseHandler):
    @login_required_json
    @playlist_author_required_json
    def post(self, playlist):
        user = self.user
        try:
            ori_idx = int(self.request.get('ori_idx')) - 1
            target_idx = int(self.request.get('target_idx')) - 1
            if ori_idx < 0 or ori_idx >= len(playlist.videos) or target_idx < 0 or target_idx >= len(playlist.videos):
                raise ValueError('Invalid')
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True, 
                'message': 'Index value error.'
            }))
            return

        if ori_idx != target_idx:
            temp_key = playlist.videos.pop(ori_idx)
            playlist.videos.insert(target_idx, temp_key)
            playlist.modified = datetime.now()
            playlist.put()

        self.response.out.write(json.dumps({
            'error': False, 
        }))
