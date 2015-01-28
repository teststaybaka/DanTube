from views import *

class Submit(BaseHandler):
    @login_required
    def get(self):
        self.render('submit')

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        title = self.request.get('title').strip()
        if not title:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Title must not be empty!'
            }))
            return
        elif len(title) > 40:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Title is too long!'
            }))
            return

        category = self.request.get('category').strip()
        if not category:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Category must not be empty!'
            }))
            return

        subcategory = self.request.get('subcategory').strip()
        if not subcategory:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subcategory must not be empty!'
            }))
            return

        description = self.request.get('description').strip()
        if not description:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Description must not be empty!'
            }))
            return
        elif len(description) > 2000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Description is too long!'
            }))
            return

        video_type = self.request.get('video-type-option').strip()
        if not video_type:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video type must not be empty!'
            }))
            return

        tags_ori = self.request.get('tags').split(',')
        tags = []
        for i in range(0, len(tags_ori)):
            if tags_ori[i].strip() != '':
                tags.append(tags_ori[i].strip())
        if len(tags) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Tags must not be empty!'
            }))
            return
        elif len(tags) > 30:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Too many tags!'
            }))
            return


        raw_url = self.request.get('video-url').strip()
        if not raw_url:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video url must not be empty!'
            }))
            return

        playlis_option = self.request.get('playlist-option').strip()
        if not playlis_option:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Must select a playlist option!'
            }))
            return

        # res = models.Video.parse_url(raw_url)
        # logging.info(res)
        try:
            video = models.Video.Create(
                raw_url = raw_url,
                user = user,
                description = description,
                title = title,
                category = category,
                subcategory = subcategory,
                video_type = video_type,
                tags = tags
            )
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return

        self.response.out.write(json.dumps({
            'error': False
        }))
        user.videos_submited += 1
        user.put()