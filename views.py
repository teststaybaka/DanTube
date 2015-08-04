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
    def user_key(self):
        u = self.user_info
        return self.user_model.get_key(u['user_id']) if u else None

    @webapp2.cached_property
    def user_detail_key(self):
        u = self.user_info
        return models.UserDetail.get_key(self.user_key) if u else None

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

    def render(self, tempname, context={}):
        if not context.get('user'):
            context['user'] = {}
        if self.user_info:
            if not self.user:
                self.user = self.user_key.get()
            context['user']['is_auth'] = True
            context['user'].update(self.user.get_private_info())
        else:
            context['user']['is_auth'] = False

        context['category'] = models.Video_Category
        context['subcategory'] = models.Video_SubCategory
        path = 'template/' + tempname + '.html'
        template = env.get_template(path)
        self.response.write(template.render(context))
    
    def notify(self, notice, tatus=200, type='error'):
        self.response.set_status(status)
        self.render('notice', {'notice': notice, 'type': type})

    def json_response(self, error, result={}):
        self.response.headers['Content-Type'] = 'application/json'
        result['error'] = error
        self.response.write(json.dumps(result))

    def get_keywords(self):
        return models.ILLEGAL_LETTER.sub(' ', self.request.get('keywords').strip().lower())

    def get_ids(self):
        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            raise ValueError('None id.')

        seen = set()
        seen_add = seen.add
        return [x for x in ids if not (x in seen or seen_add(x))]
    
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
                new_content += self.assemble_link(temp, add_link, users)
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
        return new_content, [x for x in users if not (x == user_key or x in seen or seen_add(x))]


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
        cursor = models.Cursor()
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        videos, cursor, more = models.Video.query(models.Video.category==category).order(-models.Video.hot_score).fetch_page(page_size, start_cursor=cursor)
        context = {
            'top_ten_videos': [],
            'top_ten_cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            context['top_ten_videos'].append(video_info)

        remains = 8
        if self.user_info:
            uper_keys = models.Subscription.query(ancestor=self.user_key).order(-models.Subscription.score).fetch(limit=remains, projection=['uper'])
            upers = ndb.get_multi(uper_keys)
            context = ['upers'] = []
            for i in xrange(0, len(upers)):
                uper = upers[i]
                uper_info = uper.get_public_info()
                context['upers'].append(uper_info)
            remains -= len(upers)

        context['blocks'] = []
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
            counter = 0
            for i in xrange(0, len(models.Video_Category)):
                category = models.Video_Category[i]
                subcategories = models.Video_SubCategory[category]
                if counter >= len(subcategories):
                    counter -= len(subcategories)
                else:
                    context['blocks'].append({
                        'category': category,
                        'subcategory': subcategories[counter],
                    })
                    remains -= 1
                    break

        self.render('index', context)

    def second_level(self):
        category = self.request.route.name
        context = {'category_name': category}
        self.render('category', context)

    def third_level(self):
        [category, subcategory] = self.request.route.name.split('-')
        context = {
            'category_name': category,
            'subcategory_name': subcategory,
        }
        self.render('subcategory', context)

class LoadVideos(BaseHandler):
    def subcategory(self):
        try:
            page_size = int(self.request.get('page-size'))
        except Exception, e:
            self.json_response(True, {'message': 'Page size invalid.'})
            return

        category = self.request.get('category')
        subcategory = self.request.get('subcategory')
        if category not in models.Video_Category or subcategory not in models.Video_SubCategory:
            self.json_response(True, {'message': 'Invalid category.'})
            return
        category = category+'-'+subcategory

        order = self.request.get('order')
        if order == 'updated':
            order = models.Video.updated
        elif order == 'created':
            order = models.Video.created
        elif order == 'hot':
            order = models.Video.hot_score

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        videos, cursor, more = models.Video.query(models.Video.category==category).order(-order).fetch_page(page_size, start_cursor=cursor)
        result = {
            'videos': [],
            'cursor': cursor.urlsafe() if cursor else None,
        }
        for i in xrange(0, len(videos)):
            video = videos[i]
            video_info = video.get_basic_info()
            result['videos'].append(video_info)

        self.json_response(False, result)

    def uper(self):
        try:
            page_size = int(self.request.get('page-size'))
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
            'cursor': cursor.urlsafe() if cursor else None,
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
        while not video:
            random_id = random.randint(1, max_id)
            video = models.Video.get_by_id('dt'+str(random_id))
        self.redirect(self.uri_for('watch', video_id=random_id))

class Search(BaseHandler):
    def get(self):
        context = {
            'keywords': self.get_keywords(),
            'order': self.request.get('order'),
        }
        category = self.request.get('category')
        if category in models.Video_Category:
            context['cur_category'] = category
            subcategory = self.request.get('subcategory')
            if subcategory in models.Video_SubCategory[category]:
                context['cur_subcategory'] = subcategory

        self.render('search', context)

    def post(self):
        page_size = models.STANDARD_PAGE_SIZE
        keywords = self.get_keywords()
        if not keywords:
            query_string = ''
        else:
            query_string = 'content: ' + keywords
        
        category = self.request.get('category')
        if category in models.Video_Category:
            if query_string:
                query_string += ' AND '
            query_string += 'category: "' + category + '"'

            subcategory = self.request.get('subcategory')
            if subcategory in models.Video_SubCategory[category]:
                query_string += ' AND subcategory: "' + subcategory + '"'

        order = self.request.get('order')
        if order == 'hits':
            index = search.Index(name='videos_by_hits')
        elif order == 'likes':
            index = search.Index(name='videos_by_likes')
        elif order == 'created':
            index = search.Index(name='videos_by_created')
        else:
            self.json_response(True, {'message': 'Invalid order.'})
            return

        context{'videos': []}
        cursor = search.Cursor(web_safe_string=self.request.get('cursor'))
        try:
            options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
            query = search.Query(query_string=query_string, options=options)
            result = index.search(query)

            cursor = result.cursor
            context['cursor'] = cursor.web_safe_string if cursor else None
            videos = ndb.get_multi([ndb.Key(urlsafe=video_doc.doc_id) for video_doc in result.results])
            for i in xrange(0, len(videos)):
                video = videos[i]
                video_info = video.get_basic_info()
                context['videos'].append(video_info)

            self.json_response(False, context)
        except Exception, e:
            logging.info("search failed")
            logging.info(e)
            self.json_response(True, {'message': 'Video search error.'});

class SearchPlaylist(BaseHandler):
    def get(self):
        context = {'keywords': self.get_keywords()}
        self.render('search_playlist', context)

    def post(self):
        page_size = models.STANDARD_PAGE_SIZE
        keywords = self.get_keywords()
        if not keywords:
            query_string = ''
        else:
            query_string = 'content: ' + keywords

        context{'playlists': []}
        index = search.Index(name='playlists_by_modified')
        cursor = search.Cursor(web_safe_string=self.request.get('cursor'))
        try:
            options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
            query = search.Query(query_string=query_string, options=options)
            result = index.search(query)

            cursor = result.cursor
            context['cursor'] = cursor.web_safe_string if cursor else None
            playlists = ndb.get_multi([ndb.Key(urlsafe=playlist_doc.doc_id) for playlist_doc in result.results])
            for i in xrange(0, len(playlists)):
                playlist = playlists[i]
                playlist_info = playlist.get_info()
                context['playlists'].append(playlist_info)

            self.json_response(False, context)
        except Exception, e:
            logging.info("playlist search failed")
            logging.info(e)
            self.json_response(True, {'message': 'Playlist search error.'});
        
class SearchUPer(BaseHandler):
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

        context{'upers': []}
        index = search.Index(name='upers_by_created')
        cursor = search.Cursor(web_safe_string=self.request.get('cursor'))
        try:
            options = search.QueryOptions(cursor=cursor, limit=page_size, ids_only=True)
            query = search.Query(query_string=query_string, options=options)
            result = index.search(query)

            cursor = result.cursor
            context['cursor'] = cursor.web_safe_string if cursor else None
            upers = ndb.get_multi([ndb.Key(urlsafe=uper_doc.doc_id) for uper_doc in result.results])
            upers_detail = ndb.get_multi([models.UserDetail.get_key(uper.key)  for uper in upers])
            for i in xrange(0, len(upers)):
                uper = upers[i]
                uper_info = uper.get_public_info(self.user)
                uper_info.update(upers_detail.get_detail_info())
                context['upers'].append(uper_info)

            self.json_response(False, context)
        except Exception, e:
            logging.info(e)
            self.json_response(False, {'message': 'UPer search error.'});
