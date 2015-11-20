import webapp2
import json
import base64
import time
import hmac
import hashlib
import Cookie
import logging
import urllib

from webapp2_extras import security

class Secure(object):
    @classmethod
    def sign(cls, *parts):
        try:
            cls.secret_key
        except AttributeError:
            cls.secret_key = webapp2.get_app().config.get('secret_key')

        signature = hmac.new(cls.secret_key, digestmod=hashlib.sha256)
        signature.update('|'.join(parts))
        return signature.hexdigest()

class Session(object):
    def __init__(self, value=None):
        self.remember = False
        if value:
            self.value = value
        else:
            self.value = {}

    def get(self, name):
        return self.value.get(name)

    def set(self, name, val):
        self.value[name] = val

    def unset(self, name):
        del self.value[name]

    @classmethod
    def get_session(cls, request, max_age=2592000):
        cookie_value = request.cookies.get('db_session')
        if not cookie_value:
            return cls()

        cookie_value = urllib.unquote(Cookie._unquote(cookie_value))
        parts = cookie_value.split('|')
        if len(parts) != 3:
            return cls()

        value, timestamp, signature = parts
        valid_signature = Secure.sign('db_session', value, timestamp)
        if not security.compare_hashes(signature, valid_signature):
            logging.warning('Invalid cookie signature %r', cookie_value)
            return cls()

        if max_age:
            if int(timestamp) < cls.get_timestamp() - max_age:
                logging.warning('Expired cookie %r', cookie_value)
                return cls()
        try:
            value = json.loads(base64.b64decode(value))
            return cls(value)
        except  Exception, e:
            logging.warning('Cookie value failed to be decoded: %r', parts[0])
            return cls()

    def save_session(self, response):
        value = base64.b64encode(json.dumps(self.value))
        timestamp = str(self.get_timestamp())
        signature = Secure.sign('db_session', value, timestamp)

        cookie_value = '|'.join([value, timestamp, signature])
        if self.value.get('remember'):
            response.set_cookie('db_session', urllib.quote(cookie_value), max_age=2592000, path='/', httponly=False)
        else:
            response.set_cookie('db_session', urllib.quote(cookie_value), path='/', httponly=False)

    @classmethod
    def get_timestamp(cls):
        return int(time.time())

class Auth(object):
    def __init__(self, session):
        self.session = session

    def get_user(self):
        return self.session.get('user') if self.session else None

    def set_user(self, user, remember=True):
        u = self.session.get('user')
        if not u:
            u = {}
            self.session.set('user', u)
        u['user_id'] = user.key.id()
        u['level'] = user.level
        self.session.set('remember', remember)

    def unset_user(self):
        self.session.unset('user')
