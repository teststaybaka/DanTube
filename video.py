from views import *
from PIL import Image
from google.appengine.api import images
import urlparse
import random
import math

class CoverUpload(BaseHandler, blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
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

        self.response.out.write(str(uploaded_image.key()))

class VideoUpload(BaseHandler):
    @login_required
    def submit(self):
        self.render('submit_multi')

    @login_required
    def edit(self):
        video = models.Video.get_by_id('dt'+video_id)
        if video.uploader.id() == self.user.key.id():
            self.render('edit_video', {'video':video.get_full_info()})
        else:
            self.render('notice', {'type':'error', 'notice':'You are not allowed to edit this video.'})

    def field_check(self):
        self.title = self.request.get('total-title').strip()
        if not self.title:
            return {
                'error': True,
                'message': 'Title must not be empty!'
            }
        elif len(self.title) > 100:
            return {
                'error': True,
                'message': 'Title is too long!'
            }

        self.category = self.request.get('category').strip()
        if not self.category:
            return {
                'error': True,
                'message': 'Category must not be empty!'
            }
        self.subcategory = self.request.get('subcategory').strip()
        if not self.subcategory:
            return {
                'error': True,
                'message': 'Subcategory must not be empty!'
            }
        if not ((self.category in models.Video_Category) and (self.subcategory in models.Video_SubCategory[self.category])):
            return {
                'error': True,
                'message': 'Category mismatch!'
            }

        self.description = self.request.get('description').strip()
        if not self.description:
            return {
                'error': True,
                'message': 'Description must not be empty!'
            }
        elif len(self.description) > 2000:
            return {
                'error': True,
                'message': 'Description is too long!'
            }

        self.video_type = self.request.get('video-type-option').strip()
        if not self.video_type:
            return {
                'error': True,
                'message': 'Video type must not be empty!'
            }

        self.tags_ori = self.request.get('tags').split(',')
        self.tags = []
        for i in range(0, len(self.tags_ori)):
            if self.tags_ori[i].strip() != '':
                self.tags.append(self.tags_ori[i].strip())
        if len(self.tags) == 0:
            return {
                'error': True,
                'message': 'Tags must not be empty!'
            }
        elif len(self.tags) > 20:
            return {
                'error': True,
                'message': 'Too many tags!'
            }

        self.allow_tag_add = self.request.get('allow-add')
        if self.allow_tag_add == 'on':
            self.allow_tag_add = True
        else:
            self.allow_tag_add = False

        self.raw_urls = self.request.POST.getall('video-url[]')
        if len(self.raw_urls) == 0:
            return {
                'error': True,
                'message': 'You must submit at least one video!'
            }
        for i in range(0, len(self.raw_urls)):
            raw_url = self.raw_urls[i];
            if not raw_url:
                return {
                    'error': True,
                    'message': 'Video url must not be empty!',
                    'index': i,
                }
            else:
                if not urlparse.urlparse(raw_url).scheme:
                    raw_url = "http://" + raw_url
                try:
                    req = urllib2.urlopen(raw_url)
                except Exception, e:
                    return {
                        'error': True,
                        'message': 'invalid url',
                        'index': i,
                    }

        self.subtitles = self.request.POST.getall('sub-title[]')
        for i in range(0, len(self.subtitles)):
            subtitle = self.subtitles[i]
            if len(subtitle) > 100:
                return {
                    'error': True,
                    'message': 'Sub title too long!',
                }

        self.subintros = self.request.POST.getall('sub-intro[]')
        for i in range(0, len(self.subintros)):
            subintro = self.subintros[i]
            if len(subintro) > 2000:
                return {
                    'error': True,
                    'message': 'Sub intro too long!',
                }

        return {'error': False}

    def thumbnail_upload(self):
        try:
            im = Image.open(self.thumbnail_field.file)
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
            # logging.info('image process failed')
            raise Exception('Image process failed.')
        else:
            output.seek(0)
            form = MultiPartForm()
            # form.add_field('raw_url', raw_url)
            form.add_file('coverImage', 'cover.jpg', fileHandle=output)

            # Build the request
            upload_url = models.blobstore.create_upload_url(self.uri_for('cover_upload'))
            request = urllib2.Request(upload_url)
            request.add_header('User-agent', 'PyMOTW (http://www.doughellmann.com/PyMOTW/)')
            body = str(form)
            request.add_header('Content-type', form.get_content_type())
            request.add_header('Content-length', len(body))
            request.add_data(body)
            # request.get_data()
            request_res = urllib2.urlopen(request).read()
            if request_res == 'error':
                raise Exception('Image upload error.')
            else:
                self.thumbnail_key = models.blobstore.BlobKey(request_res)

    @login_required
    def submit_post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        res = self.field_check()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        self.thumbnail_field = self.request.POST.get('thumbnail')
        self.thumbnail_key = None
        if self.thumbnail_field != '':
            try:
                self.thumbnail_upload()
            except Exception, e:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': str(e),
                }))

        try:
            video = models.Video.Create(
                user = user,
                description = self.description,
                title = self.title,
                category = self.category,
                subcategory = self.subcategory,
                video_type = self.video_type,
                tags = self.tags,
                allow_tag_add = self.allow_tag_add,
                thumbnail = self.thumbnail_key
            )
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e),
            }))
            return

        try:
            for i in range(0, len(self.subtitles)):
                video_clip = models.VideoClip.Create(subintro=self.subintros[i], raw_url=self.raw_urls[i])
                video.video_clips.append(video_clip.key)
                video.video_clip_titles.append(self.subtitles[i])
            if self.thumbnail_key is None:
                video.default_thumbnail = video.video_clips[0].get().vid
            video.put()
        except Exception, e:
            for i in range(0, len(video.video_clips)):
                video.video_clips.delete()
            video.key.delete()
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e),
                'index': i,
            }))
            return

        user.videos_submited += 1
        user.put()
        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video submitted successfully!'
        }))

    @login_required
    def edit_post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id('dt'+video_id)
        user = self.user

        res = self.field_check()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        self.thumbnail_field = self.request.POST.get('thumbnail')
        self.thumbnail_key = None
        if self.thumbnail_field != '':
            try:
                self.thumbnail_upload()
            except Exception, e:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': str(e),
                }))

        try:
            changed = False
            if video.description != self.description:
                video.description = self.description
                changed = True

            if video.title != self.title:
                video.title = self.title
                changed = True

            if video.category != self.category:
                video.category = self.category
                changed = True

            if video.subcategory != self.subcategory:
                video.subcategory = self.subcategory
                changed = True

            if video.video_type != self.video_type:
                video.video_type = self.video_type
                changed = True

            if video.tags != self.tags:
                video.tags = self.tags
                changed = True

            if video.allow_tag_add != self.allow_tag_add:
                video.allow_tag_add = self.allow_tag_add

            if self.thumbnail_key != None:
                if video.thumbnail != None:
                    images.delete_serving_url(video.thumbnail)
                    models.blobstore.BlobInfo(video.thumbnail).delete()
                video.thumbnail = self.thumbnail_key

            for i in range(0, len(self.subtitles)):
                video_clip = models.VideoClip.Create(subtitle=self.subtitles[i], subintro=self.subintros[i], raw_url=self.raw_urls[i])
                video.video_clips.append(video_clip.key)

            video.put()
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
            return
        else:
            if changed:
                video.create_index('videos_by_created', models.time_to_seconds(video.created) )
                video.create_index('videos_by_hits', video.hits )
                video.create_index('videos_by_favors', video.favors )
                video.create_index('videos_by_user' + str(video.uploader.id()), models.time_to_seconds(video.created) )

        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Video updated successfully!'
        }))

class DeleteVideo(BaseHandler):
    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video selected.'
            }))
            return

        deleted_ids = []
        for i in range(0, len(ids)):
            video_id = ids[i]
            video = models.Video.get_by_id('dt'+video_id)
            if video is None or video.uploader.id() != self.user.key.id():
                continue

            deleted_ids.append(video_id)
            video.deleted = True
            video.put()

        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No video deleted.'
            }))
            return

        self.response.out.write(json.dumps({
            'error': False,
            'message': deleted_ids,
        }))

class ManageVideo(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        context = {'user': {'videos_submited': user.videos_submited}}
        self.render('manage_video', context)
        
    @login_required
    def post(self):
        user = self.user
        self.response.headers['Content-Type'] = 'application/json'
        try:
            page = int(self.request.get('page'))
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid page'
            }))
            return

        try:
            page_size = int(self.request.get('page_size'))
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid page size'
            }))
            return

        keywords = self.request.get('keywords').strip().lower()
        if keywords:
            query_string = 'content: ' + keywords
            page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
            offset = (page - 1)*page_size
            options = search.QueryOptions(offset=offset, limit=page_size)
            query = search.Query(query_string=query_string, options=options)
            index = search.Index(name='videos_by_user' + str(user.key.id()))
            try:
                result = index.search(query)                
                total_found = min(result.number_found, models.MAX_QUERY_RESULT)
                total_pages = math.ceil(total_found/float(page_size))

                video_keys = []
                for video_doc in result.results:
                    video_keys.append(ndb.Key(urlsafe=video_doc.doc_id))
                videos = ndb.get_multi(video_keys)

                result = {'error': False}
                result['videos'] = []

                for i in range(0, len(videos)):
                    video = videos[i]
                    video_info = video.get_basic_info()
                    result['videos'].append(video_info)

                result['total_pages'] = total_pages
                result['total_found'] = total_found
                self.response.out.write(json.dumps(result))
            except search.Error:
                logging.info("search failed")
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Failed to search.'
                }))
        else:
            order = self.request.get('order')
            if order == 'hits': # most viewed
                order = models.Video.hits
            elif order == 'created': # newest uplooad
                order = models.Video.created
            elif order == 'favors': # most favors
                order = models.Video.favors
            else:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'Invalid order'
                }))
                return
            
            video_count = user.videos_submited
            total_pages = math.ceil(video_count/float(page_size))
            
            result = {'error': False}
            result['videos'] = []
            if video_count != 0 and page <= total_pages:
                offset = (page - 1) * page_size
                videos = models.Video.query(models.Video.uploader==self.user.key).order(-order).fetch(offset=offset, limit=page_size)
                for i in range(0, len(videos)):
                    video = videos[i]
                    video_info = video.get_basic_info()
                    result['videos'].append(video_info)

            result['total_pages'] = total_pages
            result['total_found'] = video_count
            self.response.out.write(json.dumps(result))

class RandomVideos(BaseHandler):
    #Assuming that there are always more videos than requeseted
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        try:
            size = int(self.request.get('size'))
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Size invalid'
            }))
            return
        size = min(100, models.Video.get_video_count(), size)

        try:
            fetched = {}
            result = {'error': False}
            result['videos'] = []
            max_id = models.Video.get_max_id()

            for i in range(0, size):
                while True:
                    random_id = random.randint(1, max_id)
                    if not fetched.get(random_id):
                        video = models.Video.get_by_id('dt'+str(random_id))
                        if (video is not None) and (not video.deleted):
                            uploader = video.uploader.get()
                            video_info = video.get_basic_info()
                            video_info['uploader'] = uploader.get_public_info()
                            result['videos'].append(video_info)
                            fetched[random_id] = 1;
                            break

            self.response.out.write(json.dumps(result))
        except Exception, e:
            logging.info('error occurred fetching random videos')
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))
