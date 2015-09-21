from views import *
import time
from PIL import Image

class EmailCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = self.user_model.check_unique('auth_id', self.request.get('email'))
        if res:
            self.response.write('error')
        else:
            self.response.write('valid')

class NicknameCheck(BaseHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        res = self.user_model.check_unique('nickname', self.request.get('nickname').strip())
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

        unique_properties = ['nickname']
        success, user = self.user_model.create_user(
            email,
            unique_properties,
            nickname=nickname,
            email=email,
            password_raw=password,
        )
        if not success:
            # self.session['message'] = 'Unable to create user for email %s because of \
            #     duplicate keys %s' % (email, user_data[1])
            self.json_response(True, {'message': 'Sign up failed.'})
            return
        user.create_index(intro='')
        user_detail = models.UserDetail(key=models.User.get_detail_key(user.key))
        user_detail.put()

        token = self.user_model.create_signup_token(user.key.id())
        verification_url = self.uri_for('verification', user_id=user.key.id(), signup_token=token, _full=True)
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

        img = Image.open(cStringIO.StringIO(urllib2.urlopen(self.request.host_url+'/static/emoticons_img/default_avatar'+str(random.randint(1,6))+'.png').read()))
        bucket_name = 'dantube-avatar'
        standard_file = gcs.open('/'+bucket_name+'/standard-'+str(user.key.id()), 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
        small_file = gcs.open('/'+bucket_name+'/small-'+str(user.key.id()), 'w', content_type="text/plain", options={'x-goog-acl': 'public-read'})
        img.save(standard_file, format='png', optimize=True)
        img = img.resize((64, 64), Image.ANTIALIAS)
        img.save(small_file, format='png', optimize=True)
        standard_file.close()
        small_file.close()

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
        remember = bool(self.request.get('remember'))

        try:
            u = self.auth.get_user_by_password(email, password, remember=remember)
            if u['level'] == 1:
                self.auth.unset_session()
                self.json_response(True, {'message': 'Please verify your email address.'})
            else:
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
            self.json_response(True, {'message': 'Account does not exist.'})
            return

        # delete any existing tokens if exist
        tokens = self.user_model.token_model.fetch_tokens(user.key, 'pwdreset')
        for token in tokens:
            token.key.delete()
        
        token = self.user_model.create_pwdreset_token(user.key.id())
        password_reset_url = self.uri_for('forgot_password_reset', user_id=user.key.id(), pwdreset_token=token, _full=True)
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
        token = self.user_model.get_token_key(user_id, pwdreset_token, 'pwdreset').get()
        if token:
            time_passed = models.time_to_seconds(datetime.now()) - models.time_to_seconds(token.created)
            if time_passed > 24 * 60 * 60: # 24 hours
                token.key.delete()
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
        user_key = ndb.Key('User', user_id)
        token_key = self.user_model.get_token_key(user_id, pwdreset_token, 'pwdreset')
        token, user = ndb.get_multi([token_key, user_key])
        if token and user:
            time_passed = models.time_to_seconds(datetime.now()) - models.time_to_seconds(token.created)
            token.key.delete()
            if time_passed > 24 * 60 * 60: # 24 hours
                self.json_response(True, {'message': 'Password reset has expired. Please make a new request.'})
            else:
                user.set_password(new_password)
                user.put()
                self.json_response(False)
        else:
            self.json_response(True, {'message': 'Reset url not found.'})

class Verification(BaseHandler):
    def get(self, user_id, signup_token):
        user_id = int(user_id)
        user_key = ndb.Key('User', user_id)
        token_key = self.user_model.get_token_key(user_id, signup_token, 'signup')
        token, user = ndb.get_multi([token_key, user_key])
        if token and user:
            time_passed = models.time_to_seconds(datetime.now()) - models.time_to_seconds(token.created)
            token.key.delete()
            if time_passed > 24 * 60 * 60: # 24 hours
                self.notify("Verficaition has expired. Please make a new request.")
            else:
                if user.level == 1:
                    user.level = 2
                    user.put()
                self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                self.notify("Your account %s has been activated!" % (user.email), type='success')
        else:
            self.notify("Url not found.")

class SendVerification(BaseHandler):
    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        
        try:
            u = self.auth.get_user_by_password(email, password, save_session=False)            
        except (auth.InvalidAuthIdError, auth.InvalidPasswordError) as e:
            self.json_response(True, {'message': 'Account invalid. Please check email address or password.'})
            return

        if u['level'] != 1:
            self.json_response(True, {'message': 'Your account has been activated.'})
            return

        user = ndb.Key('User', u['user_id']).get()
        # delete any existing tokens if exist
        tokens = self.user_model.token_model.fetch_tokens(user.key, 'signup')
        for token in tokens:
            token.key.delete()

        token = self.user_model.create_signup_token(user.key.id())
        verification_url = self.uri_for('verification', user_id=user.key.id(), signup_token=token, _full=True)
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
