import jinja2
import logging
import os
import traceback
import webapp2
import cStringIO
import itertools
import mimetools
import mimetypes
import urllib
import urllib2
import random
import cgi

from datetime import datetime
from jinja2 import Undefined
from webapp2_extras import sessions
from webapp2_extras import auth
from webapp2_extras import sessions_ndb
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.api import search
from google.appengine.ext import ndb

import models
import json
import re
import math

class SilentUndefined(Undefined):
    '''
    Dont break pageloads because vars arent there!
    '''
    def _fail_with_undefined_error(self, *args, **kwargs):
        logging.exception('JINJA2: something was undefined!')
        return None

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True,
    undefined=SilentUndefined)
env.globals = {
    'uri_for': webapp2.uri_for,
}

class BaseHandler(webapp2.RequestHandler):
    @webapp2.cached_property
    def auth(self):
        """Shortcut to access the auth instance as a property."""
        return auth.get_auth()

    @webapp2.cached_property
    def user_info(self):
        return self.auth.get_user_by_session()

    @webapp2.cached_property
    def user(self):
        u = self.user_info
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        return self.auth.store.user_model

    @webapp2.cached_property
    def session(self):
        # return self.session_store.get_session(backend="datastore")
        return self.session_store.get_session(name='db_session', factory=sessions_ndb.DatastoreSessionFactory)

    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
        """
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    def render(self, tempname, context = {}):
        user = self.user
        if not context.get('user'):
            context['user'] = {}
        if user is not None:
            context['user']['is_auth'] = True
            context['user'].update(user.get_public_info())
            context['user'].update(user.get_private_info())
        else:
            context['user']['is_auth'] = False

        message = self.session.get('message')
        if message is not None:
            context['message'] = message
            self.session.pop('message')
        context['category'] = models.Video_Category
        context['subcategory'] = models.Video_SubCategory
        path = 'template/' + tempname + '.html'
        template = env.get_template(path)
        self.response.write(template.render(context))
    
    def notify(self, notice, status=200, type='error'):
        self.response.set_status(status)
        self.render('notice', {'notice': notice, 'type': type})

    def get_page_size(self):
        try:
            page_size = int(self.request.get('page_size'))
            if page_size < 0 or page_size > 100:
                raise ValueError('Page size invalid')
        except ValueError:
            page_size = models.DEFAULT_PAGE_SIZE
        return page_size

    def get_page_number(self):
        try:
            page = int(self.request.get('page'))
            if page < 1:
                raise ValueError('Negative')
        except ValueError:
            page = 1
        return page

    def get_page_range(self, cur_page, total_pages, page_range=10):
        cur_page = int(cur_page)
        total_pages = int(total_pages)
        if cur_page > total_pages:
            max_page = total_pages
            min_page = max(total_pages - page_range + 1, 1)
        elif cur_page < 1:
            min_page = 1
            max_page = max(min_page + page_range - 1, total_pages)
        else:
            max_page = min(cur_page + 4, total_pages)
            min_page = max(cur_page - 5, 1)
            remain_page = page_range -(max_page - cur_page) - (cur_page - min_page) - 1
            if remain_page > 0:
                max_page = min(max_page + remain_page, total_pages);
                min_page = max(min_page - remain_page, 1);
        return {
            'total_pages': total_pages,
            'cur_page': cur_page,
            'pages': range(min_page, max_page+1)
        }

def login_required(handler):
    """
        Decorator that checks if there's a user associated with the current session.
        Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        auth = self.auth
        if not auth.get_user_by_session():
            self.redirect(self.uri_for('signin'), abort=True)
        else:
            return handler(self, *args, **kwargs)
 
    return check_login

def login_required_json(handler):
    def check_login(self, *args, **kwargs):
        self.response.headers['Content-Type'] = 'application/json'
        auth = self.auth
        if not auth.get_user_by_session():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Please log in!'
            }))
            return
        else:
            return handler(self, *args, **kwargs)
 
    return check_login

class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return
    
    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return
    
    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.  
        parts = []
        part_boundary = '--' + self.boundary
        
        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )
        
        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )
        
        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)

class Home(BaseHandler):
    def get(self):
        context = {}
        context['top_ten_videos'] = []
        videos, total_page = models.Video.get_page(order=models.Video.hot_score, page=1, page_size=10)
        uploaders = ndb.get_multi([video.uploader for video in videos])
        for i in range(0, len(videos)):
            video = videos[i]
            uploader = uploaders[i]
            video_info = video.get_basic_info()
            video_info['uploader'] = uploader.get_public_info()
            context['top_ten_videos'].append(video_info)
        self.render('index', context)

class Category(BaseHandler):
    def get(self):
        category = self.request.route.name
        context = {}
        context['category_name'] = category
        context['top_ten_videos'] = []
        videos, total_page = models.Video.get_page(category=category, order=models.Video.hot_score, page=1, page_size=10)
        uploaders = ndb.get_multi([video.uploader for video in videos])
        for i in range(0, len(videos)):
            video = videos[i]
            uploader = uploaders[i]
            video_info = video.get_basic_info()
            video_info['uploader'] = uploader.get_public_info()
            context['top_ten_videos'].append(video_info)
        self.render('category', context)

class Subcategory(BaseHandler):
    def get(self):
        [category, subcategory] = self.request.route.name.split('-')
        context = {}
        context['category_name'] = category
        context['subcategory_name'] = subcategory
        context['top_ten_videos'] = []
        videos, total_page = models.Video.get_page(category=category, subcategory=subcategory, order=models.Video.hot_score, page=1, page_size=10)
        uploaders = ndb.get_multi([video.uploader for video in videos])
        for i in range(0, len(videos)):
            video = videos[i]
            uploader = uploaders[i]
            video_info = video.get_basic_info()
            video_info['uploader'] = uploader.get_public_info()
            context['top_ten_videos'].append(video_info)
        self.render('subcategory', context)

class RandomVideo(BaseHandler):
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
        size = min(models.Video.get_video_count(), size)

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
                        if video is not None:
                            uploader = video.uploader.get()
                            video_info = video.get_basic_info()
                            video_info['uploader'] = uploader.get_public_info()
                            result['videos'].append(video_info)
                            fetched[random_id] = 1;
                            break

            self.response.out.write(json.dumps(result))
        except Exception, e:
            logging.info('error occurred fetching random videos:'+str(e))
            self.response.out.write(json.dumps({
                'error': True,
                'message': str(e)
            }))

class FeelingLucky(BaseHandler):
    def get(self):
        max_id = models.Video.get_max_id()
        video = None
        while video is None:
            random_id = random.randint(1, max_id)
            video = models.Video.get_by_id('dt'+str(random_id))
        self.redirect(self.uri_for('watch', video_id=random_id))

class CategoryVideo(BaseHandler):
    def post(self):
        # models.Video.fetch_page()
        self.response.headers['Content-Type'] = 'application/json'
        category = self.request.get('category').strip()
        subcategory = self.request.get('subcategory').strip()

        if (not (category in models.Video_Category)) or \
            ((category in models.Video_Category) and (subcategory) and not (subcategory in models.Video_SubCategory[category]) ):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid category/subcategory'
            }))
            return
        # try:
        #     if category:
        #         for cat_name, url_name in dict((k,v[0]) for k,v in models.URL_NAME_DICT.items()).iteritems():
        #             if url_name == category:
        #                 category = cat_name
        #                 break
        #         if subcategory:
        #             for subcat_name, url_name in models.URL_NAME_DICT[category][1].iteritems():
        #                 if url_name == subcategory:
        #                     subcategory = subcat_name
        #                     break
        #         else:
        #             subcategory = ""
        #     else:
        #         category = ""
        # except (KeyError, BadValueError) as e:
        #     self.response.out.write(json.dumps({
        #         'error': True,
        #         'message': 'Invalid category/subcategory'
        #     }))
        #     return

        order_str = self.request.get('order').strip()
        if order_str == 'hits': # ranking
            order = models.Video.hits
        elif order_str == 'hot_score':
            order = models.Video.hot_score
        elif order_str == 'created': # newest upload
            order = models.Video.created
        elif order_str == 'last_updated': # neweset activity
            order = models.Video.last_updated
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid order'
            }))
            return

        page = self.get_page_number()
        page_size = self.get_page_size()

        # videos, more = models.Video.fetch_page(category, subcategory, order, page)
        videos, total_pages = models.Video.get_page(category=category, subcategory=subcategory, order=order, page=page, page_size=page_size)

        # try:
        #     videos, more = models.Video.fetch_page(category, subcategory, order, page)
        # except Exception, e:
        #     logging.info(e)
        #     self.response.out.write(json.dumps({
        #         'error': True,
        #         'message': str(e)
        #     }))
        #     return

        # try:
        #     limit = int(self.request.get('limit'))
        # except ValueError:
        #     limit = len(videos)

        result = {'error': False}
        result['videos'] = []
        uploaders = ndb.get_multi([video.uploader for video in videos])
        for i in range(0, len(videos)): # videos[0:limit]:
            video = videos[i]
            uploader = uploaders[i]
            video_info = video.get_basic_info()
            video_info['uploader'] = uploader.get_public_info()
            result['videos'].append(video_info)
        result['total_pages'] = total_pages

        self.response.out.write(json.dumps(result))

class Search(BaseHandler):
    def get(self):
        # all_videos = models.Video.query().fetch()
        # for video in all_videos:
        #     video.create_index('videos_by_created', models.time_to_seconds(video.created))
        #     video.create_index('videos_by_hits', video.hits)
        #     video.create_index('videos_by_favors', video.favors)
        #     video.create_index('videos_by_user' + str(video.uploader.id()), models.time_to_seconds(video.created) )
            
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        keywords = self.request.get('keywords').strip().lower()
        if not keywords:
            query_string = ''
        elif models.ILLEGAL_REGEX.match(keywords):
            self.notify('Keywords include illegal characters.');
            return
        else:
            query_string = 'content: ' + keywords
        context['keywords'] = keywords
        
        category = self.request.get('category').strip()
        if category in models.Video_Category:
            context['cur_category'] = category
            if query_string:
                query_string += ' AND '
            query_string += 'category: \"' + category + '\"'

            subcategory = self.request.get('subcategory').strip()
            if subcategory in models.Video_SubCategory[category]:
                context['cur_subcategory'] = subcategory
                query_string += ' AND subcategory: \"' + subcategory + '\"'
                                   
        order = self.request.get('order').strip()
        if order == 'hits':
            index = search.Index(name='videos_by_hits')
        elif order == 'created':
            index = search.Index(name='videos_by_created')
        elif order == 'favors':
            index = search.Index(name='videos_by_favors')
        else:
            order = 'hits'
            index = search.Index(name='videos_by_hits')
        context['order'] = order

        page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
        offset = (page - 1) * page_size
        context['videos'] = []
        try:
            options = search.QueryOptions(offset=offset, limit=page_size)
            query = search.Query(query_string=query_string, options=options)
            result = index.search(query)
            total_found = min(result.number_found, models.MAX_QUERY_RESULT)
            total_pages = math.ceil(total_found/float(page_size))

            videos = ndb.get_multi([ndb.Key(urlsafe=video_doc.doc_id) for video_doc in result.results])
            uploaders = ndb.get_multi([video.uploader for video in videos])
            for i in range(0, len(videos)):
                video = videos[i]
                video_info = video.get_basic_info()
                uploader = uploaders[i]
                video_info['uploader'] = uploader.get_public_info()
                context['videos'].append(video_info)

            context['total_found'] = total_found
            context.update(self.get_page_range(page, total_pages) )
            # logging.info(videos)
            self.render('search', context)
        except Exception, e:
            logging.info("search failed")
            logging.info(e)
            self.notify('Video search error.');

        # total_pages = -(-total_videos // page_size)

        # result = index.search("")
        # logging.info(result.number_found)
        # for doc in result.results:
        #     logging.info(doc)

        # key_words_ori = self.request.get('keywords')
        # logging.info(key_words_ori)
        # self.render('search', {'keywords': key_words_ori})

class SearchPlaylist(BaseHandler):
    def get(self):
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        keywords = self.request.get('keywords').strip().lower()
        if not keywords:
            query_string = ''
        elif models.ILLEGAL_REGEX.match(keywords):
            self.notify('Keywords include illegal characters.');
            return
        else:
            query_string = 'content: ' + keywords
        context['keywords'] = keywords

        index = search.Index(name='playlists_by_modified')
        page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
        offset = (page - 1) * page_size
        context['playlists'] = []
        try:
            options = search.QueryOptions(offset=offset, limit=page_size)
            query = search.Query(query_string=query_string, options=options)
            result = index.search(query)
            total_found = min(result.number_found, models.MAX_QUERY_RESULT)
            total_pages = math.ceil(total_found/float(page_size))

            playlists = ndb.get_multi([ndb.Key(urlsafe=playlist_doc.doc_id) for playlist_doc in result.results])
            creators = ndb.get_multi([playlist.creator for playlist in playlists])
            for i in range(0, len(playlists)):
                playlist = playlists[i]
                playlist_info = playlist.get_basic_info()
                creator = creators[i]
                playlist_info['creator'] = creator.get_public_info()
                playlist_info['videos'] = []

                videos_limit = min(9, len(playlist.videos))
                video_keys = []
                for i in range(0, videos_limit):
                    video_keys.append(playlist.videos[i])
                videos = ndb.get_multi(video_keys)
                for i in range(0, len(videos)):
                    video = videos[i]
                    video_info = video.get_basic_info()
                    video_info['index'] = i + 1
                    playlist_info['videos'].append(video_info)

                context['playlists'].append(playlist_info)

            context['total_found'] = total_found
            context.update(self.get_page_range(page, total_pages) )
            self.render('search_playlist', context)
        except Exception, e:
            logging.info("playlist search failed")
            logging.info(e)
            self.notify('Playlist search error.');
        
class SearchUPer(BaseHandler):
    def get(self):
        # all_users = models.User.query().fetch()
        # for user in all_users:
        #     user.create_index()
        
        page_size = models.DEFAULT_PAGE_SIZE
        page = self.get_page_number()

        context = {}
        keywords = self.request.get('keywords').strip().lower()
        if not keywords:
            query_string = ''
        elif models.ILLEGAL_REGEX.match(keywords):
            self.notify('Keywords include illegal characters.');
            return
        else:
            query_string = 'content: ' + keywords
        context['keywords'] = keywords

        index = search.Index(name='upers_by_created')
        page =  min(page, math.ceil(models.MAX_QUERY_RESULT/float(page_size)) )
        offset = (page - 1) * page_size
        context['upers'] = []
        try:
            options = search.QueryOptions(offset=offset, limit=page_size)
            query = search.Query(query_string=query_string, options=options)
            result = index.search(query)
            total_found = min(result.number_found, models.MAX_QUERY_RESULT)
            total_pages = math.ceil(total_found/float(page_size))

            upers = ndb.get_multi([ndb.Key(urlsafe=uper_doc.doc_id) for uper_doc in result.results])
            for i in range(0, len(upers)):
                uper = upers[i]
                uper_info = uper.get_public_info(self.user)
                uper_info.update(uper.get_statistic_info())
                context['upers'].append(uper_info)

            context['total_found'] = total_found
            context.update(self.get_page_range(page, total_pages) )
            self.render('search_uper', context)
        except Exception, e:
            logging.info(e)
            self.notify('UPer search error.');

class Feedback(BaseHandler):
    @login_required
    def get(self):
        self.render('feedback', {'feedback_category': models.Feedback_Category})

    def field_check(self):
        self.category = self.request.get('category').strip()
        if not self.category:
            return {
                'error': True,
                'message': 'Category must not be empty!'
            }
        
        if not (self.category in models.Feedback_Category):
            return {
                'error': True,
                'message': 'Category mismatch!'
            }

        self.subject = self.request.get('subject').strip()
        if not self.subject:
            return {
                'error': True,
                'message': 'Subject must not be empty!'
            }
        elif len(self.subject) > 400:
            return {
                'error': True,
                'message': 'Subject is too long!'
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

        if(self.request.get('anonymous').strip()):
            self.anonymous = True
        else:
            self.anonymous = False

        return {'error': False}

    @login_required_json
    def post(self):
        user = self.user

        res = self.field_check()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        feedback = models.Feedback(
            category = self.category,
            subject = self.subject,
            description = self.description,
            anonymous = self.anonymous
        )
        if not self.anonymous:
            feedback.sender = user.key
            feedback.sender_nickname = user.nickname
        feedback.put()    
        
        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Feedback submitted successfully!'
        }))

class Report(BaseHandler):
    @login_required
    def get(self):
        self.render('report', {'issues': models.Report_Issues})
        
    def field_check(self):
        vid = self.request.get('vid').strip()
        if not vid:
            return {
                'error': True,
                'message': 'Video ID must not be empty!'
            }
        video = models.Video.get_by_id(vid)
        if not video:
            return {
                'error': True,
                'message': 'Video ID does not exist!'
            }
        self.video = video
        self.video_id = vid
        self.video_title = video.title

        self.issue = self.request.get('issue').strip()
        if not self.issue:
            return {
                'error': True,
                'message': 'Issue must not be empty!'
            }
        
        if not (self.issue in models.Report_Issues):
            return {
                'error': True,
                'message': 'Issue mismatch!'
            }

        self.details = self.request.get('details').strip()

        return {'error': False}

    @login_required_json
    def post(self):
        user = self.user

        res = self.field_check()
        if res['error']:
            self.response.out.write(json.dumps(res))
            return

        report = models.Report(
            video = self.video.key,
            video_id = self.video_id,
            video_title = self.video_title,
            issue = self.issue,
            details = self.details,
            reporter_nickname = user.nickname,
            reporter = user.key
        )
        report.put()    
        
        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Report submitted successfully!'
        }))