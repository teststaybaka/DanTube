from views import *
import time

class EmailCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.auth_ids==self.request.get('email')).get(keys_only=True)
        if res:
            self.response.write('error')
        else:
            self.response.write('valid')

class NicknameCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = models.User.query(models.User.nickname==self.request.get('nickname').strip()).get(keys_only=True)
        if res:
            self.response.write('error')
        else:
            self.response.write('valid')

class Signup(BaseHandler):
    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signup')
    
    def post(self):
        email = self.user_model.validate_email(self.request.get('email'))
        if not email:
            self.json_response(True, {'message': 'Email is invalid.'})
            return
        nickname = self.user_model.validate_nickname(self.request.get('nickname').strip())
        if not nickname:
            self.json_response(True, {'message': 'Nickname is invalid.'})
            return
        password = self.user_model.validate_password(self.request.get('password'))
        if not password:
            self.json_response(True, {'message': 'Password is invalid.'})
            return

        unique_properties = ['email']
        user_data = self.user_model.create_user(
            email,
            unique_properties,
            nickname=nickname,
            email=email,
            password_raw=password,
            default_avatar=random.randint(1,6)
        )
        if not user_data[0]: #user_data is a tuple
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (email, user_data[1])
            self.json_response(True, {'message': 'Sign up failed.'})
            return

        user = user_data[1]
        user_id = user.get_id()
        user.create_index(intro='')
        models.UserDetail.Create(user.key)

        # auto-login user
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)

        token = self.user_model.create_signup_token(user_id)
        verification_url = self.uri_for('verification', user_id=user_id, signup_token=token, _full=True)
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

        self.json_response(False);

class Signin(BaseHandler):
    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('signin')

    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        remember = self.request.get('remember')
        # logging.info(self.request)

        if not email:
            self.json_response(True, {'message': 'Email is invalid.'})
            return
        if not password:
            self.json_response(True, {'message': 'Password is invalid.'})
            return
        try:
            if remember:
                u = self.auth.get_user_by_password(email, password, remember=True)
            else:
                u = self.auth.get_user_by_password(email, password, remember=False)
            self.json_response(False)
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            logging.info('Login failed for user %s because of %s', email, type(e))
            self.json_response(True, {'message': 'Sign in failed. Email and password don\'t match.'})

class Logout(BaseHandler):
  def get(self):
    self.auth.unset_session()
    self.redirect(self.uri_for('home'))

class ForgotPassword(BaseHandler):
    def get(self):
        if self.user_info:
            self.redirect(self.uri_for('home'))
        else:
            self.render('forgot_password')

    def post(self):
        if self.user_info:
            self.json_response(True, {'message': 'You have already signed in.'})
            return
        
        email = self.request.get('email')
        if not email:
            self.json_response(True, {'message': 'Please enter your email address.'})
            return

        user = models.User.query(models.User.auth_ids==email).get()
        if not user:
            self.json_response(True, {'message': 'The email address you entered does not exist.'})
            return
        user_id = user.key.id()

        # delete any existing tokens if exist
        # token_model = self.user_model.token_model
        # tokens = token_model.query(token_model.user == user, subject == 'pwdreset').fetch()
        # logging.info(tokens)
        # for token in tokens:
        #     self.user_model.delete_pwdreset_token(user_id, token.token)
        token = self.user_model.create_pwdreset_token(user_id)
        password_reset_url = self.uri_for('forgot_password_reset', user_id=user_id, pwdreset_token=token, _full=True)
        message = mail.EmailMessage(sender="DanTube Support <dan-tube@appspot.gserviceaccount.com>",
                                    subject="Password Reset Email from DanTube")
        message.to = user.email
        message.body = """
        Dear %s:

        Your password reset url is:
        %s

        You can safely ignore this email if you didn't request a password reset.
        """ % (user.nickname, password_reset_url)
        logging.info(message.body)
        message.send()

        self.json_response(False)

class ForgotPasswordReset(BaseHandler):
    def get(self, user_id, pwdreset_token):
        if self.user_info:
            self.notify("You have already signed in.")
            return

        user_id = int(user_id)
        token_key = self.user_model.get_token_key(user_id, pwdreset_token, 'pwdreset')
        token = token_key.get()
        if token:
            time_passed = time_to_seconds(datetime.now()) - time_to_seconds(token.created)
            if time_passed > 24 * 60 * 60: # 24 hours
                token.key.delete_async()
                self.notify("Reset url has expired. Please make a new request.")
            else:
                self.render('forgot_password_reset')
        else:
            self.notify("Reset url not found.")


    def post(self, user_id, pwdreset_token):
        if self.user_info:
            self.json_response(True, {'message': 'You have already signed in.'})
            return

        new_password = self.user_model.validate_password(self.request.get('new_password'))
        if not new_password:
            self.json_response(True, {'message': 'Invalid new password.'})
            return

        user_id = int(user_id)
        token_key = self.user_model.get_token_key(user_id, pwdreset_token, 'pwdreset')
        user_key = self.user_model.get_key(user_id)
        token, user = ndb.get_multi([token_key, user_key])
        if token and user:
            time_passed = time_to_seconds(datetime.now()) - time_to_seconds(token.created)
            token.key.delete_async()
            if time_passed > 24 * 60 * 60: # 24 hours
                self.json_response(True, {'message': 'Reset url has expired. Please make a new request.'})
            else:
                user.set_password(new_password)
                user.put_async()
                self.json_response(False)
        else:
            self.json_response(True, {'message': 'Reset url not found.'})

class Verification(BaseHandler):
    @login_required
    def get(self, user_id, signup_token):
        user_id = int(user_id)
        if self.user_key.id() != user_id:
            self.notify('Invalid verification.')
            return

        token_key = self.user_model.get_token_key(user_id, signup_token, 'signup')
        user_key = self.user_model.get_key(user_id)
        token, user = ndb.get_multi([token_key, user_key])
        self.user = user
        if token and user:
            time_passed = time_to_seconds(datetime.now()) - time_to_seconds(token.created)
            token.key.delete_async()
            if time_passed > 24 * 60 * 60: # 24 hours
                self.notify("Verficaition url has expired. Please make a new request.")
            else:
                if user.level == 1:
                    user.level = 2
                    user.put_async()
                self.notify("Your account %s has been activated!" % (user.email), type='success')
        else:
            self.notify("Url not found.")

class SendVerification(BaseHandler):
    @login_required_json
    def post(self):
        user = self.user_key.get()
        if user.level != 1:
            self.json_response(True, {'message': 'Your account has been activated.'})
            return

        user_id = user.key.id()
        token = self.user_model.create_signup_token(user_id)
        verification_url = self.uri_for('verification', user_id=user_id, signup_token=token, _full=True)
        message = mail.EmailMessage(sender="DanTube Support <dan-tube@appspot.gserviceaccount.com>",
                                    subject="Verficaition Email from DanTube")
        message.to = user.email
        message.body = """
        Dear %s:

        Please use the following url to activate your account:
        %s
        """ % (user.nickname, verification_url)
        logging.info(message.body)
        message.send()

        self.json_response(False)
        