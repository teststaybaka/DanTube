from views import *
from PIL import Image
from google.appengine.api import images

class Submit(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
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
        elif len(title) > 100:
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
        elif len(tags) > 15:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Too many tags!'
            }))
            return

        allow_tag_add = self.request.get('allow-add')
        if allow_tag_add == 'on':
            allow_tag_add = True
        else:
            allow_tag_add = False

        raw_url = self.request.get('video-url').strip()
        if not raw_url:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video url must not be empty!'
            }))
            return

        playlist_option = self.request.get('playlist-option').strip()
        if not playlist_option:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Must select a playlist option!'
            }))
            return

        try:
            video = models.Video.Create(
                raw_url = raw_url,
                user = user,
                description = description,
                title = title,
                category = category,
                subcategory = subcategory,
                video_type = video_type,
                tags = tags,
                allow_tag_add = allow_tag_add,
            )
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return

        thumbnail_field = self.request.POST.get('thumbnail')
        if thumbnail_field != '':
            try:
                im = Image.open(thumbnail_field.file)
                # mypalette = frame.getpalette()
                # logging.info(frame.info['duration'])
                # nframes = 0
                # while frame:
                #     frame.putpalette(mypalette)
                #     im = frame
                #     nframes += 1
                #     if nframes > 4:
                #         break;
                #     try:
                #         frame.seek(frame.tell() + 1)
                #     except EOFError:
                #         break;

                output = cStringIO.StringIO()
                if im.mode == "RGBA" or "transparency" in im.info:
                    rgba_im = Image.new("RGBA", (512,288))
                    resized_im = im.resize((512,288), Image.ANTIALIAS)
                    rgba_im.paste(resized_im)
                    new_im = Image.new("RGB", (512,288), (255,255,255))
                    new_im.paste(rgba_im, rgba_im)
                    new_im.save(output, format='jpeg', quality=90)
                else:
                    rgb_im = Image.new("RGB", (512,288))
                    resized_im = im.resize((512,288), Image.ANTIALIAS)
                    rgb_im.paste(resized_im)
                    rgb_im.save(output, format='jpeg', quality=90)
            except Exception, e:
                logging.info('image process failed')
            else:
                output.seek(0)
                form = MultiPartForm()
                # form.add_field('raw_url', raw_url)
                form.add_file('coverImage', 'cover.jpg', fileHandle=output)

                # Build the request
                upload_url = models.blobstore.create_upload_url(self.uri_for('cover_upload', video_id=video.key.id().replace('dt', '')) )
                request = urllib2.Request(upload_url)
                request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
                body = str(form)
                request.add_header('Content-type', form.get_content_type())
                request.add_header('Content-length', len(body))
                request.add_data(body)
                # request.get_data()

                if urllib2.urlopen(request).read() == 'error':
                    # self.response.out.write(json.dumps({
                    #     'error': True,
                    #     'message': ''
                    # }))
                    logging.error('Image upload error.')
                    # return

        user.videos_submited += 1
        user.put()
        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video submitted successfully!'
        }))

    def cover_upload(self, video_id):
        self.response.headers['Content-Type'] = 'text/plain'
        upload = self.get_uploads('coverImage')
        if upload == []:
            self.response.out.write('error')
            return

        uploaded_image = upload[0]
        logging.info("upload content_type:"+uploaded_image.content_type)
        logging.info("upload size:"+str(uploaded_image.size))
        types = uploaded_image.content_type.split('/')
        if types[0] != 'image':
            uploaded_image.delete()
            self.response.out.write('error')
            return
        
        if uploaded_image.size > 50*1024*1024:
            uploaded_image.delete()
            self.response.out.write('error')
            return

        video = models.Video.get_by_id('dt'+video_id)
        if video.thumbnail != None:
            images.delete_serving_url(video.thumbnail)
            models.blobstore.BlobInfo(video.thumbnail).delete()
        video.thumbnail = uploaded_image.key()
        video.put()
        self.response.out.write('success')

class EditVideo(BaseHandler):
    @login_required
    def get(self, video_id):
        video = models.Video.get_by_id('dt'+video_id)
        if video.uploader.id() == self.user.key.id():
            self.render('edit_video', {'video':video.get_full_info()})
        else:
            self.render('notice', {'type':'error', 'notice':'You are not allowed to edit this video.'})

    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        user = self.user

        if video.uploader.id() != user.key.id():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You are not allowed to edit this video.'
            }))
            return
        
        title = self.request.get('title').strip()
        if not title:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Title must not be empty!'
            }))
            return
        elif len(title) > 100:
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
        if not ((category in models.Video_Category) and (subcategory in models.Video_SubCategory[category])):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Category mismatch!'
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
        elif len(tags) > 15:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Too many tags!'
            }))
            return

        allow_tag_add = self.request.get('allow-add')
        if allow_tag_add == 'on':
            allow_tag_add = True
        else:
            allow_tag_add = False

        raw_url = self.request.get('video-url').strip()
        if not raw_url:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Video url must not be empty!'
            }))
            return
        url_res = models.Video.parse_url(raw_url)
        if url_res.get('error'):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'invalid url'
            }))
            return

        playlist_option = self.request.get('playlist-option').strip()
        if not playlist_option:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Must select a playlist option!'
            }))
            return

        try:
            if video.url != raw_url:
                video.url = raw_url
                video.vid = url_res['vid']
                video.source = url_res['source']

            if video.description != description:
                video.description = description

            if video.title != title:
                video.title = title

            if video.category != category:
                video.category = category

            if video.subcategory != subcategory:
                video.subcategory = subcategory

            if video.video_type != video_type:
                video.video_type = video_type

            if video.tags != tags:
                video.tags = tags

            if video.allow_tag_add != allow_tag_add:
                video.allow_tag_add = allow_tag_add

            video.put()
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return

        thumbnail_field = self.request.POST.get('thumbnail')
        if thumbnail_field != '':
            try:
                im = Image.open(thumbnail_field.file)
                output = cStringIO.StringIO()
                if im.mode == "RGBA" or "transparency" in im.info:
                    rgba_im = Image.new("RGBA", (512,288))
                    resized_im = im.resize((512,288), Image.ANTIALIAS)
                    rgba_im.paste(resized_im)
                    new_im = Image.new("RGB", (512,288), (255,255,255))
                    new_im.paste(rgba_im, rgba_im)
                    new_im.save(output, format='jpeg', quality=90)
                else:
                    rgb_im = Image.new("RGB", (512,288))
                    resized_im = im.resize((512,288), Image.ANTIALIAS)
                    rgb_im.paste(resized_im)
                    rgb_im.save(output, format='jpeg', quality=90)
            except Exception, e:
                logging.info('image process failed')
            else:
                output.seek(0)
                form = MultiPartForm()
                # form.add_field('raw_url', raw_url)
                form.add_file('coverImage', 'cover.jpg', fileHandle=output)

                # Build the request
                upload_url = models.blobstore.create_upload_url(self.uri_for('cover_upload', video_id=video.key.id().replace('dt', '')) )
                request = urllib2.Request(upload_url)
                request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
                body = str(form)
                request.add_header('Content-type', form.get_content_type())
                request.add_header('Content-length', len(body))
                request.add_data(body)
                # request.get_data()

                if urllib2.urlopen(request).read() == 'error':
                    logging.error('Image upload error.')

        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video updated successfully!'
        }))

class DeleteVideo(BaseHandler):
    @login_required
    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        if video.uploader.id() != self.user.key.id():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'You are not allowed to delete this video.'
            }))
            return

        video.deleted = True
        video.put()
        
        self.response.out.write(json.dumps({
            'error': False
        }))

