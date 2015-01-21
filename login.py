from views import *

class EmailCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.auth_ids==self.request.get('email')).get()
        if res is not None:
            self.response.write('error');
        else:
            self.response.write('valid');
        logging.info(res);

class NicknameCheck(BaseHandler):
    def post(self):
        pass;