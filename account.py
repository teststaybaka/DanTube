from views import *

class Account(BaseHandler):
    def get(self):
        self.render('account');