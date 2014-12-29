import jinja2
import logging
import os
import sys
import traceback
import webapp2

from jinja2 import Undefined
from webapp2_extras import sessions


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