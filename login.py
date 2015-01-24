from views import *
from google.appengine.api import mail
import random

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

    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signup')
    
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        email = self.user_model.validate_email(self.request.get('email'))
        if not email:
            self.response.out.write('error 1')
            return
        nickname = self.user_model.validate_nickname(self.request.get('nickname'))
        if not nickname:
            self.response.out.write('error 1')
            return
        password = self.user_model.validate_password(self.request.get('password'))
        if not password:
            self.response.out.write('error 1')
            return

        unique_properties = ['email']
        user_data = self.user_model.create_user(email,
            unique_properties,
            nickname=nickname, email=email, password_raw=password, verified=False, default_avatar=random.randint(1,6))
        if not user_data[0]: #user_data is a tuple
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (email, user_data[1])
            # self.render('signup')s
            self.response.out.write('error 2')
            return

        user = user_data[1]
        user_id = user.get_id()

        # auto-login user
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        token = self.user_model.create_signup_token(user_id)
 
        verification_url = self.uri_for('verification', user_id=user_id,
          signup_token=token, _full=True)

        message = mail.EmailMessage(sender="tianfanw@gmail.com",
                            subject="Verficaition Email from DanTube")

        message.to = email
        message.body = """
        Dear %s:

        Your verification url is:
        %s
        """ % (nickname, verification_url)
        logging.info(message.body)
        message.send()

        # u = self.auth.get_user_by_password(res['email'], res['password'], remember=True)
        # self.session['message'] = 'Sign up successfully!'
        # self.redirect(self.uri_for('home'))
        self.response.out.write('success')

class Signin(BaseHandler):
    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signin')

    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        email = self.request.get('email')
        password = self.request.get('password')
        remember = self.request.get('remember')
        # logging.info(self.request)

        if not email:
            self.response.out.write('error')
            return
        if not password:
            self.response.out.write('error')
            return
        try:
            if remember:
                u = self.auth.get_user_by_password(email, password, remember=True)
            else:
                u = self.auth.get_user_by_password(email, password, remember=False)
            self.response.out.write('success')
            return
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', email, type(e))
            self.response.out.write('error')
            return

class Logout(BaseHandler):
  def get(self):
    self.auth.unset_session()
    # self.session['message'] = 'Logout successfully'
    self.redirect(self.uri_for('home'))
