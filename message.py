from views import *

class Message(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        threads = models.MessageThread.query(ndb.OR(models.MessageThread.sender==user.key,
            models.MessageThread.receiver==user.key)).order(-models.MessageThread.updated).fetch()
        context = {
            'threads': [],
            'threads_fetched': len(threads)
        }

        total_new_messages = 0
        for thread in threads:
            thread_dict = {}
            thread_dict['subject'] = thread.subject
            thread_dict['last_message'] = thread.last_message
            thread_dict['updated'] = thread.updated.strftime("%Y-%m-%d %H:%M")
            thread_dict['url'] = '/account/messages/' + str(thread.key.id())
            if user.key.id() == thread.sender.id():
                partner = models.User.get_by_id(thread.receiver.id())
            else:
                partner = models.User.get_by_id(thread.sender.id())
            thread_dict['partner'] = partner.get_public_info()
            if user.key.id() == thread.last_message_sender.id():
                thread_dict['is_last_sender'] = True
                thread_dict['unread'] = False
            else:
                thread_dict['is_last_sender'] = False
                if thread.new_messages > 0:
                    thread_dict['new_messages'] = thread.new_messages
                    total_new_messages += thread.new_messages
                    thread_dict['unread'] = True
                else:
                    thread_dict['unread'] = False

            context['threads'].append(thread_dict)

        context['total_new_messages'] = total_new_messages
        self.render('message', context)

class Compose(BaseHandler):
    @login_required
    def get(self):
        self.render('message_compose')

    @login_required
    def post(self):
        user = self.user
        self.response.headers['Content-Type'] = 'application/json'
        receiver_nickname = self.request.get('receiver').strip()
        if not receiver_nickname:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'receiver cannot be empty.'
            }))
            return

        if receiver_nickname == user.nickname:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'receiver cannot be self.'
            }))
            return

        receiver = models.User.query(models.User.nickname==receiver_nickname).get()
        if not receiver:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'receiver not found.'
            }))
            return

        subject = self.request.get('subject').strip()
        if not subject:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'subject cannot be empty.'
            }))
            return
        
        content = self.request.get('content')
        if not content.strip():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'content cannot be empty.'
            }))
            return
        
        message = models.Message(
            sender = user.key,
            content = content,
            sent_time = datetime.now()
        )
        message_key = message.put()
        message_thread = models.MessageThread(
            messages = [message_key],
            subject = subject,
            sender = user.key,
            receiver = receiver.key,
            last_message_sender = user.key,
            last_message = content,
            updated = message.sent_time
        )
        message_thread.put()

        self.response.out.write(json.dumps({
            'error': False,
            'message':'message sent!'
        }))

class Detail(BaseHandler):
    @login_required
    def get(self, thread_id):
        user = self.user
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread:
            self.render('notice', {'type':'error', 'notice':'page not found'});
            return
        if (thread.sender.id() != user.key.id()) and (thread.receiver.id() != user.key.id()):
            self.render('notice', {'type':'error', 'notice':'page not found'})
            return

        context = {}
        context['subject'] = thread.subject
        if user.key.id() == thread.sender.id():
            partner = models.User.get_by_id(thread.receiver.id())
        else:
            partner = models.User.get_by_id(thread.sender.id())
        context['partner'] = partner.get_public_info()

        context['messages'] = []
        messages = ndb.get_multi(thread.messages)
        for msg in messages:
            message = {}
            if msg.sender.id() == user.key.id():
                message['is_sender_user'] = True
            else:
                message['is_sender_user'] = False
            message['content'] = msg.content
            message['sent_time'] = msg.sent_time.strftime("%Y-%m-%d %H:%M")
            context['messages'].append(message)

        self.render('message_detail', context)

        if thread.last_message_sender.id() != user.key.id():
            thread.new_messages = 0
            thread.put()

    @login_required
    def post(self, thread_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'message does not exist.'
            }))
            return
        if (thread.sender.id() != user.key.id()) and (thread.receiver.id() != user.key.id()):
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'you are not allowed to view.'
            }))
            return

        content = self.request.get('content')
        if not content.strip():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'content cannot be empty.'
            }))
            return

        message = models.Message(
            sender = user.key,
            content = content,
            sent_time = datetime.now()
        )
        message_key = message.put()
        thread.messages.append(message_key)
        thread.last_message_sender = user.key
        thread.last_message = content
        thread.new_messages += 1
        thread.updated = message.sent_time
        thread.put()

        self.response.out.write(json.dumps({
            'error': False,
            'message': 'message sent.',
            'sent_time': message.sent_time.strftime("%Y-%m-%d %H:%M"),
            'content': message.content
        }))

class Mentioned(BaseHandler):
    @login_required
    def get(self):
        self.render('mentioned_me')

class Notifications(BaseHandler):
    @login_required
    def get(self):
        self.render('notifications')
