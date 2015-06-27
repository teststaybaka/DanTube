from views import *
import time

class EmailCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.auth_ids==self.request.get('email').strip()).get()
        if res is not None:
            self.response.write('error')
        else:
            self.response.write('valid')
        # logging.info(res)

class NicknameCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.nickname==self.request.get('nickname').strip()).get()
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
        self.response.headers['Content-Type'] = 'application/json'
        email = self.user_model.validate_email(self.request.get('email').strip())
        if not email:
            self.response.out.write(json.dumps({'error':True,'message': 'Email is invalid.'}))
            return
        nickname = self.user_model.validate_nickname(self.request.get('nickname').strip())
        if not nickname:
            self.response.out.write(json.dumps({'error':True,'message': 'Nickname is invalid.'}))
            return
        password = self.user_model.validate_password(self.request.get('password'))
        if not password:
            self.response.out.write(json.dumps({'error':True,'message': 'Password is invalid.'}))
            return

        unique_properties = ['email']
        user_data = self.user_model.create_user(email,
            unique_properties,
            nickname=nickname, email=email, password_raw=password, verified=False, default_avatar=random.randint(1,6))
        if not user_data[0]: #user_data is a tuple
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (email, user_data[1])
            self.response.out.write(json.dumps({'error':True,'message': 'Sign up failed.'}))
            return

        user = user_data[1]
        user_id = user.get_id()
        user.create_index()

        # auto-login user
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        token = self.user_model.create_signup_token(user_id)
 
        verification_url = self.uri_for('verification', user_id=user_id,
          signup_token=token, _full=True)

        message = mail.EmailMessage(sender="DanTube Support <dan-tube@appspot.gserviceaccount.com>",
                            subject="Verficaition Email from DanTube")

        message.to = email
        message.body = """
        Dear %s:

        Please use the following url to activate your account:
        %s
        """ % (nickname, verification_url)
        logging.info(message.body)
        message.send()

        # u = self.auth.get_user_by_password(res['email'], res['password'], remember=True)
        self.response.out.write(json.dumps({'error':False}))

class Signin(BaseHandler):
    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signin')

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        email = self.request.get('email').strip()
        password = self.request.get('password')
        remember = self.request.get('remember').strip()
        # logging.info(self.request)

        if not email:
            self.response.out.write(json.dumps({'error':True,'message': 'Email is invalid.'}))
            return
        if not password:
            self.response.out.write(json.dumps({'error':True,'message': 'Password is invalid.'}))
            return
        try:
            if remember:
                u = self.auth.get_user_by_password(email, password, remember=True)
            else:
                u = self.auth.get_user_by_password(email, password, remember=False)
            self.response.out.write(json.dumps({'error':False}))
            return
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', email, type(e))
            self.response.out.write(json.dumps({'error':True,'message': 'Sign in failed. Email and password don\'t match.'}))
            return

class Logout(BaseHandler):
  def get(self):
    self.auth.unset_session()
    # self.session['message'] = 'Logout successfully'
    self.redirect(self.uri_for('home'))

class ForgotPassword(BaseHandler):
    def get(self):
        if self.user_info is not None:
            self.redirect(self.uri_for('home'))
            return
        self.render('forgot_password')

    def post(self):
        if self.user_info is not None:
            self.redirect(self.uri_for('home'))
            return
        
        self.response.headers['Content-Type'] = 'application/json'
        email = self.request.get('email').strip()
        if not email:
            self.response.out.write(json.dumps({'error':True,'message': 'Please enter your email address.'}))
            return

        user = models.User.query(models.User.auth_ids == email).get()
        if user is None:
            self.response.out.write(json.dumps({'error':True,'message': 'The email address you entered does not exist.'}))
            return

        user_id = user.get_id()

        # delete any existing tokens if exist
        # token_model = self.user_model.token_model
        # tokens = token_model.query(token_model.user == user, subject == 'pwdreset').fetch()
        # logging.info(tokens)
        # for token in tokens:
        #     self.user_model.delete_pwdreset_token(user_id, token.token)

        token = self.user_model.create_pwdreset_token(user_id)

        password_reset_url = self.uri_for('forgot_password_reset', user_id=user_id,
            pwdreset_token=token, _full=True)
        message = mail.EmailMessage(sender="DanTube Support <dan-tube@appspot.gserviceaccount.com>",
                            subject="Password Reset Email from DanTube")

        message.to = user.email
        message.body = """
        Dear %s:

        Your password reset url is:
        %s

        You can safely ignore this email if you didn't require a password reset.
        """ % (user.nickname, password_reset_url)
        logging.info(message.body)
        message.send()

        self.response.out.write(json.dumps({'error':False}))

class ForgotPasswordReset(BaseHandler):
    def validateToken(self, user_id, pwdreset_token):
        if self.user:
            return {'error':True,'message': 'You have already signed in.'}, None

        user = None
        user, ts = self.user_model.get_by_auth_token(user_id, pwdreset_token, 'pwdreset')

        if not user:
            logging.info('Could not find any user with id "%s" and token "%s"', user_id, pwdreset_token)
            return {'error':True,'message': 'Reset url not found.'}, None

        time_passed = time.mktime(datetime.now().timetuple()) - ts
        if time_passed > 24 * 60 * 60: # 24 hours
            self.user_model.delete_pwdreset_token(user_id, pwdreset_token)
            return {'error':True,'message': "Reset url has expired. Please make a new request."}, None

        return {'error':False}, user

    def get(self, *args, **kwargs):
        user_id = int(kwargs['user_id'])
        pwdreset_token = kwargs['pwdreset_token']
        res, user = self.validateToken(user_id, pwdreset_token)
        if not res['error']:
            self.render('forgot_password_reset');
        else:
            self.notify(res['message']);


    def post(self, *args, **kwargs):
        self.response.headers['Content-Type'] = 'application/json'
        user_id = int(kwargs['user_id'])
        pwdreset_token = kwargs['pwdreset_token']
        res, user = self.validateToken(user_id, pwdreset_token)
        if not res['error']:
            new_password = self.user_model.validate_password(self.request.get('new_password'))
            if not new_password:
                self.response.out.write(json.dumps({'error':True,'message': 'Invalid new password.'}))
                return

            user.set_password(new_password)
            user.put()
            self.user_model.delete_pwdreset_token(user.get_id(), pwdreset_token)
            self.response.out.write(json.dumps({'error':False}))
        else:
            self.response.out.write(json.dumps(res))
