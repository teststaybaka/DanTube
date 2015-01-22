from views import *

class EmailCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.auth_ids==self.request.get('email')).get()
        if res is not None:
            self.response.write('error')
        else:
            self.response.write('valid')
        # logging.info(res)

class NicknameCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.nickname==self.request.get('nickname')).get()
        if res is not None:
            self.response.write('error')
        else:
            self.response.write('valid')
        # logging.info(res)

class Signup(BaseHandler):
    def validateSignupForm(self):
        email = self.request.get('email')
        nickname = self.request.get('nickname')
        password = self.request.get('password')
        # logging.info(password)

        email = email.strip()
        if not email:
            # logging.info('email 1')
            return -1
        if re.match(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", email) is None:
            # logging.info('email 2')
            return -1

        if not nickname:
            # logging.info('nickname 1')
            return -1
        if ' ' in nickname:
            # logging.info('nickname 2')
            return -1
        if len(nickname) > 30:
            # logging.info('nickname 3')
            return -1

        if not password:
            # logging.info('password 1')
            return -1
        if not password.strip():
            # logging.info('password 2')
            return -1
        if len(password) < 6:
            # logging.info('password 3')
            return -1
        if len(password) > 40:
            # logging.info('password 4')
            return -1

        return {'nickname': nickname, 'email': email, 'password': password}

    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signup')
    
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = self.validateSignupForm()
        if res == -1:
            self.response.out.write('error 1')
            return

        unique_properties = ['email', 'nickname']
        user_data = self.user_model.create_user(res['email'],
            unique_properties,
            nickname=res['nickname'], email=res['email'], password_raw=res['password'], verified=False)
        if not user_data[0]: #user_data is a tuple
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (email, user_data[1])
            # self.render('signup')
            self.response.out.write('error 2')
            return

        user = user_data[1]
        user_id = user.get_id()
        # u = self.auth.get_user_by_password(res['email'], res['password'], remember=True)
        # self.session['message'] = 'Sign up successfully!'
        # self.redirect(self.uri_for('home'))
        self.response.out.write('success')
