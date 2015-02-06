from views import *

class Message(BaseHandler):
    @login_required
    def get(self):
        self.render('message')

class Compose(BaseHandler):
    @login_required
    def get(self):
        self.render('message_compose')

class Mentioned(BaseHandler):
    @login_required
    def get(self):
        self.render('mentioned_me')

class Notifications(BaseHandler):
    @login_required
    def get(self):
        self.render('notifications')
