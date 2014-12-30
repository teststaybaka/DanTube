import jinja2
import logging
import os
import sys
import traceback
import webapp2
import datetime

from jinja2 import Undefined
from webapp2_extras import sessions

import models
import json
import urllib2
import urlparse

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
    @property
    def current_user(self):
        return self.session.get('user')
        # if self.session.get('user'):
        #     return self.session.get('user')
        # else:
        #     return None
            # return self.check_status();

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

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
        """
        return self.session_store.get_session()


class Home(BaseHandler):
    def get(self):
        context = {}
        template = env.get_template('template/index.html')
        self.response.write(template.render(context))

def parse_url(raw_url):
    if not urlparse.urlparse(raw_url).scheme:
      raw_url = "http://" + raw_url

    try:
      req = urllib2.urlopen(raw_url)
    except:
      return {'error': 'invalid url'}
    else:
      url_parts = raw_url.split('//')[-1].split('/')
      source = url_parts[0].split('.')[-2]
      if source == 'youtube':
        vid = url_parts[-1].split('=')[-1]
        url = 'http://www.youtube.com/embed/' + vid
      else:
        url = raw_url
      return {'url': url, 'vid': vid, 'source': source}

class Video(BaseHandler):
    def post(self):
        raw_url = self.request.get('raw_url')
        description = self.request.get('description')

        res = parse_url(raw_url)
        logging.info(res)
        if res.get('error'):
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'status': 'failed'
            }))
        else:
            video = models.Video(
                url = res['url'],
                vid = res['vid'],
                source = res['source'],
                description = description
            )
            video.put()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({
                'status': 'success'
            }))

class Danmaku(BaseHandler):
    def post(self):
        # video_id = self.request.get('video_id')
        # video_time = self.request.get('video_time')
        video_id = 'test'
        timestamp = datetime.time(0, 0, 0)
        content = self.request.get('content')
        danmaku = models.Danmaku(
            video_id = video_id,
            timestamp = timestamp,
            content = content
        )
        danmaku.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'content': danmaku.content
        }))