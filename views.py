import jinja2
import logging
import os
import traceback
import webapp2
import cStringIO
import itertools
import mimetools
import mimetypes
import urllib2
import urllib
import random
import cgi
import json
import re
import math
import collections
import base64

import cloudstorage as gcs
from google.appengine.api import app_identity
from datetime import datetime
from jinja2 import Undefined
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.api import search
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from apiclient.discovery import build
from google.appengine.ext import deferred
from sessions import *

import models

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
    def session(self):
        return Session.get_session(self.request)

    @webapp2.cached_property
    def auth(self):
        return Auth(self.session)

    @webapp2.cached_property
    def user_info(self):
        return self.auth.get_user()

    @webapp2.cached_property
    def user_key(self):
        u = self.user_info
        return models.User.get_key(u['user_id']) if u else None

    @webapp2.cached_property
    def user_detail_key(self):
        u = self.user_info
        return models.User.get_detail_key(self.user_key) if u else None

    # modified from https://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
    def dispatch(self):
        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session.save_session(self.response)

    def persist_view_history(self):
        if self.request.route.name == 'watch':
            return

        for key in self.request.cookies:
            if models.VIDEO_ID_REGEX.match(key):
                value = self.request.cookies[key]
                self.response.set_cookie(key, value, max_age=1, path='/')

                video_id = key
                video_key = ndb.Key('Video', video_id)
                values = value.split('|')
                try:
                    clip_index = int(values[0])
                    timestamp = float(values[1])
                except ValueError:
                    continue

                record = models.ViewRecord.get(self.user_key, video_key)
                if record:
                    record.clip_index = clip_index
                    record.timestamp = timestamp
                    record.put()

    def render(self, tempname, context=None):
        # logging.info(self.request.remote_addr)
        if not context:
            context = {'user': {}}
        elif not context.get('user'):
            context['user'] = {}
        
        if self.user_info:
            try:
                self.user
            except AttributeError:
                self.user = self.user_key.get()
            context['user'].update(self.user.get_private_info())
            self.persist_view_history()
        # logging.info('user: '+str(context['user']))

        context['category'] = models.Video_Category
        context['subcategory'] = models.Video_SubCategory
        path = 'template/' + tempname + '.html'
        template = env.get_template(path)
        self.response.write(template.render(context))
        
    def notify(self, notice, status=200, type='error'):
        self.response.set_status(status)
        self.render('notice', {'notice': notice, 'type': type})

    def json_response(self, error, result={}):
        self.response.headers['Content-Type'] = 'application/json'
        result['error'] = error
        self.response.write(json.dumps(result))

    def get_keywords(self):
        return models.ILLEGAL_LETTER.sub(' ', self.request.get('keywords')).strip().lower()

    def get_ids(self):
        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            raise ValueError('None id.')

        seen = set()
        seen_add = seen.add
        return [x for x in ids if not (x in seen or seen_add(x))]

    def search(self, query_string, index_name, page_size):
        cursor = search.Cursor(web_safe_string=self.request.get('cursor'))
        options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
        query = search.Query(query_string=query_string, options=options)
        index = search.Index(name=index_name)
        result = index.search(query)

        cursor = result.cursor
        total_found = result.number_found
        results = ndb.get_multi([ndb.Key(urlsafe=doc.doc_id) for doc in result.results])
        context = {
            'total_found': total_found,
            'cursor': cursor.web_safe_string if cursor else ''
        }
        return context, results
    
    def assemble_link(self, temp, users, add_link):
        if temp != '':
            user = models.User.query(models.User.nickname==temp[1:].strip()).get(keys_only=True)
            if user:
                if add_link:
                    temp = '<a class="blue-link" target="_blank" href="'+models.User.get_space_url(user.id())+'">' + temp + '</a>'
                users.append(user)
        return temp

    def at_users_content(self, content, add_link):
        content = cgi.escape(content)
        new_content = ''
        state = 0
        temp = ''
        users = []
        for i in xrange(0, len(content)):
            if models.ILLEGAL_LETTER.match(content[i]) and state == 1:
                state = 0
                new_content += self.assemble_link(temp, users, add_link)
                temp = ''

            if content[i] == '@' and state == 0:
                state = 1
                temp += '@'
            elif state == 0:
                new_content += content[i]
            else: # state == 1
                temp += content[i]
        new_content += self.assemble_link(temp, users, add_link)

        seen = set()
        seen_add = seen.add
        return new_content, [x for x in users if not (x == self.user_key or x in seen or seen_add(x))]

def login_required(handler):
    def check_login(self, *args, **kwargs):
        if not self.user_info:
            self.redirect(self.uri_for('signin'))
        else:
            return handler(self, *args, **kwargs)
 
    return check_login

def login_required_json(handler):
    def check_login(self, *args, **kwargs):
        if not self.user_info:
            self.json_response(True, {'message': 'Please log in!'})
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
        if not mimetype:
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
        page_size = 14
        cursor = models.Cursor()
        videos, cursor, more = models.Video.query().order(-models.Video.hot_score).fetch_page(page_size, start_cursor=cursor)
        context = {
            'top_ten_videos': [],
            'top_ten_cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            context['top_ten_videos'].append(video_info)
        
        remains = 8
        if self.user_info:
            subscriptions = models.Subscription.query(models.Subscription.user==self.user_key).order(-models.Subscription.score).fetch(limit=remains, projection=['uper'])
            uper_keys = [subscription.uper for subscription in subscriptions]
            upers = ndb.get_multi(uper_keys)
            context['upers'] = []
            for i in xrange(0, len(upers)):
                uper = upers[i]
                uper_info = uper.get_public_info()
                context['upers'].append(uper_info)
            remains -= len(upers)

        context['column_categories'] = []
        total_categories = 0
        for i in xrange(0, len(models.Video_Category)):
            category = models.Video_Category[i]
            subcategories = models.Video_SubCategory[category]
            total_categories += len(subcategories)

        used_cat = set()
        while remains:
            random_cat = random.randint(0, total_categories - 1)
            if random_cat in used_cat:
                continue

            used_cat.add(random_cat)
            counter = random_cat
            for i in xrange(0, len(models.Video_Category)):
                category = models.Video_Category[i]
                subcategories = models.Video_SubCategory[category]
                if counter >= len(subcategories):
                    counter -= len(subcategories)
                else:
                    context['column_categories'].append({
                        'category': category,
                        'subcategory': subcategories[counter],
                    })
                    remains -= 1
                    break

        self.render('index', context)

    def second_level(self):
        category = self.request.route.name
        page_size = 10
        cursor = models.Cursor()
        videos, cursor, more = models.Video.query(models.Video.category==category).order(-models.Video.hot_score).fetch_page(page_size, start_cursor=cursor)
        context = {
            'category_name': category,
            'top_ten_videos': [],
            'top_ten_cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            context['top_ten_videos'].append(video_info)

        self.render('category', context)

    def third_level(self):
        [category, subcategory] = self.request.route.name.split('-')
        page_size = 10
        cursor = models.Cursor()
        videos, cursor, more = models.Video.query(ndb.AND(models.Video.category==category, models.Video.subcategory==subcategory)).order(-models.Video.hot_score).fetch_page(page_size, start_cursor=cursor)
        context = {
            'category_name': category,
            'subcategory_name': subcategory,
            'top_ten_videos': [],
            'top_ten_cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            context['top_ten_videos'].append(video_info)

        self.render('subcategory', context)

class LoadByCategory(BaseHandler):
    def post(self):
        try:
            page_size = int(self.request.get('page_size'))
            if page_size > 30:
                raise Exception('Too many')
        except Exception, e:
            self.json_response(True, {'message': 'Page size invalid.'})
            return

        category = self.request.get('category')
        subcategory = self.request.get('subcategory')
        order = self.request.get('order')
        if order != 'Popular' and not subcategory:
            self.json_response(True, {'message': 'Invalid order.'})
            return

        if order == 'Activity':
            order = models.Video.updated
        elif order == 'Newest':
            order = models.Video.created
        elif order == 'Popular':
            order = models.Video.hot_score
        else:
            self.json_response(True, {'message': 'Invalid order.'})
            return

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        if subcategory:
            videos, cursor, more = models.Video.query(ndb.AND(models.Video.category==category, models.Video.subcategory==subcategory)).order(-order).fetch_page(page_size, start_cursor=cursor)
        elif category:
            videos, cursor, more = models.Video.query(models.Video.category==category).order(-order).fetch_page(page_size, start_cursor=cursor)
        else:
            videos, cursor, more = models.Video.query().order(-order).fetch_page(page_size, start_cursor=cursor)
        result = {
            'videos': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            result['videos'].append(video_info)

        self.json_response(False, result)

class LoadByUper(BaseHandler):
    def post(self):
        try:
            page_size = int(self.request.get('page_size'))
            if page_size > 30:
                raise Exception('Too many')
        except ValueError:
            self.json_response(True, {'message': 'Page size invalid.'})
            return

        try:
            uper_key = ndb.Key('User', int(self.request.get('user_id')))
        except ValueError:
            self.json_response(True, {'message': 'Invalid id.'})
            return

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        videos, cursor, more = models.Video.query(models.Video.uploader==uper_key).order(-models.Video.updated).fetch_page(page_size, start_cursor=cursor)
        result = {
            'videos': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            result['videos'].append(video_info)

        self.json_response(False, result)

class FeelingLucky(BaseHandler):
    def get(self):
        max_id = models.Video.get_max_id()
        video = None
        while not video or video.deleted:
            random_id = 'dt'+str(random.randint(1, max_id))
            video = models.Video.get_by_id(random_id)
        self.redirect(self.uri_for('watch', video_id=random_id))

class SearchVideos(BaseHandler):
    def get(self):
        context = {
            'keywords': self.get_keywords(),
            'cur_category': self.request.get('category'),
            'cur_subcategory': self.request.get('subcategory'),
            'order': self.request.get('order'),
        }
        self.render('search', context)

    def post(self):
        page_size = models.STANDARD_PAGE_SIZE
        keywords = self.get_keywords()
        res = re.match(r'dt\d+', keywords)
        if res:
            video_id = res.group(0)
            video = models.Video.get_by_id(video_id)
            if video:
                videos = [video]
            else:
                videos = []
            context = {
                'total_found': len(videos),
                'cursor': '',
            }
        else:
            if not keywords:
                query_string = ''
            else:
                query_string = 'content: ' + keywords
            
            category = self.request.get('category')
            if category:
                if query_string:
                    query_string += ' AND '
                query_string += 'category: "' + category + '"'

                subcategory = self.request.get('subcategory')
                if subcategory:
                    query_string += ' AND subcategory: "' + subcategory + '"'

            order = self.request.get('order')
            if order == 'hits':
                index_name = 'videos_by_hits'
            elif order == 'likes':
                index_name = 'videos_by_likes'
            else: #created
                index_name = 'videos_by_created'

            try:
                context, videos = self.search(query_string, index_name, page_size)
            except Exception, e:
                logging.info("search failed")
                logging.info(e)
                self.json_response(True, {'message': 'Video search error.'});
                return

        context['videos'] = []
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_full_info()
            context['videos'].append(video_info)

        self.json_response(False, context)

class SearchPlaylists(BaseHandler):
    def get(self):
        context = {
            'playlist_types': models.Playlist_Type,
            'keywords': self.get_keywords(),
            'playlist_type': self.request.get('type'),
            'playlist_max': self.request.get('max'),
            'playlist_min': self.request.get('min'),
        }
        self.render('search_playlist', context)

    def post(self):
        page_size = models.STANDARD_PAGE_SIZE
        keywords = self.get_keywords()
        if not keywords:
            query_string = ''
        else:
            query_string = 'content: ' + keywords

        playlist_type = self.request.get('type')
        if playlist_type:
            if query_string:
                query_string += ' AND '
            query_string += 'type: "' + playlist_type + '"'

        try:
            videos_min = int(self.request.get('min'))
            if query_string:
                query_string += ' AND '
            query_string += 'videos >= ' + str(videos_min)
        except ValueError:
            pass

        try:
            videos_max = int(self.request.get('max'))
            if query_string:
                query_string += ' AND '
            query_string += 'videos <= ' + str(videos_max)
        except ValueError:
            pass

        try:
            context, playlists = self.search(query_string, 'playlists_by_modified', page_size)
        except Exception, e:
            logging.info("playlist search failed")
            logging.info(e)
            self.json_response(True, {'message': 'Playlist search error.'});
            return

        context['playlists'] = []
        for i in xrange(0, len(playlists)):
            playlist = playlists[i]
            playlist_info = playlist.get_info()
            context['playlists'].append(playlist_info)

        self.json_response(False, context)
        
class SearchUPers(BaseHandler):
    def get(self):
        context = {'keywords': self.get_keywords()}
        self.render('search_uper', context)

    def post(self):
        page_size = models.STANDARD_PAGE_SIZE
        keywords = self.get_keywords()
        if not keywords:
            query_string = ''
        else:
            query_string = 'content: ' + keywords

        try:
            context, upers = self.search(query_string, 'upers_by_created', page_size)
            upers_detail = ndb.get_multi([models.User.get_detail_key(uper.key)  for uper in upers])
        except Exception, e:
            logging.info(e)
            self.json_response(False, {'message': 'UPer search error.'});
            return

        if self.user_info:
            subscriptions = models.Subscription.query(models.Subscription.user==self.user_key).order(-models.Subscription.score).fetch(projection=['uper'])
            subscribed = set([subscription.uper for subscription in subscriptions])
        else:
            subscribed = set()

        context['upers'] = []
        for i in xrange(0, len(upers)):
            uper = upers[i]
            detail = upers_detail[i]
            uper_info = uper.get_public_info()
            uper_info.update(detail.get_detail_info())
            if uper.key in subscribed:
                uper_info['subscribed'] = True
            else:
                uper_info['subscribed'] = False
            context['upers'].append(uper_info)

        self.json_response(False, context)
