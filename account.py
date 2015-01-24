from views import *

class Account(BaseHandler):
    def get(self):
        self.render('account');

class ChangePassword(BaseHandler):
    def get(self):
        self.render('change_password');