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
    def get(self, video_id):
        video = models.Video.get_by_id(int(video_id))
        if video is not None:
            context = {'video': video, 'video_id': video_id}
            template = env.get_template('template/video.html')
            self.response.write(template.render(context))
        else:
            self.response.write('video not found')
            self.response.set_status(404)

    def post(self):
        raw_url = self.request.get('raw_url')
        description = self.request.get('description')

        res = parse_url(raw_url)
        logging.info(res)
        self.response.headers['Content-Type'] = 'application/json'
        if res.get('error'):
            self.response.out.write(json.dumps({
                'error': 'failed to submit video'
            }))
        else:
            video = models.Video(
                url = res['url'],
                vid = res['vid'],
                source = res['source'],
                description = description
            )
            video.put()
            self.response.out.write(json.dumps({
                'id': '123'
            }))

class Danmaku(BaseHandler):
    def get(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id(int(video_id))
        if video is not None:
            danmaku_itr = models.Danmaku.all().filter('video = ', video).run()
            danmakus = []
            for danmaku in danmaku_itr:
                danmakus.append({
                    'content': danmaku.content,
                    'timestamp': danmaku.timestamp,
                    'creator': danmaku.creator
                });
            self.response.out.write(json.dumps(danmakus))
        else:
            self.response.out.write(json.dumps({
                'error': 'video not found',
            }))

    def post(self, video_id):
        self.response.headers['Content-Type'] = 'application/json'
        video = models.Video.get_by_id(int(video_id))
        if video is not None:
            danmaku = models.Danmaku(
                video = video,
                timestamp = float(self.request.get('timestamp')),
                # creator = 
                content = self.request.get('content')
            )
            danmaku.put()
            
            self.response.out.write(json.dumps({
                'timestamp': danmaku.timestamp,
                'content': danmaku.content
            }))
        else:
            self.response.out.write(json.dumps({
                'error': 'video not found',
            }))