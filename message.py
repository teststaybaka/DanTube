from views import *

class Message(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        xrequest = self.request.headers.get('X-Requested-With')
        if xrequest and xrequest == 'XMLHttpRequest':

            try:
                page_size = int(self.request.get('page_size'))
            except ValueError:
                page_size = models.PAGE_SIZE

            try:
                page = int(self.request.get('page') )
                if page < 1:
                    raise ValueError('Negative')
            except ValueError:
                page = 1

            total_pages = -(-user.threads_counter // page_size)
            if page > total_pages:
                page = total_pages
            offset = (page - 1) * page_size

            self.response.headers['Content-Type'] = 'application/json'
            threads = models.MessageThread.query(ndb.OR(models.MessageThread.sender==user.key,
            models.MessageThread.receiver==user.key)).order(-models.MessageThread.updated).fetch(offset=offset, limit=page_size)
            result = {
                'threads': [],
                'threads_fetched': len(threads),
                'total_pages': total_pages,
                'page': page
            }

            for thread in threads:
                thread_dict = {}
                thread_dict['id'] = thread.key.id()
                thread_dict['subject'] = thread.subject
                thread_dict['last_message'] = thread.messages[-1].content
                thread_dict['updated'] = thread.updated.strftime("%Y-%m-%d %H:%M")
                thread_dict['url'] = '/account/messages/' + str(thread.key.id())
                if thread.delete_user:
                    partner = thread.delete_user.get() # the other user deleted the message
                else:
                    if user.key.id() == thread.sender.id():
                        partner = thread.receiver.get()
                    else:
                        partner = thread.sender.get()
                thread_dict['partner'] = partner.get_public_info()

                if user.key.id() == thread.messages[-1].sender.id():
                    thread_dict['is_last_sender'] = True
                    thread_dict['unread'] = False
                else:
                    thread_dict['is_last_sender'] = False
                    if thread.new_messages > 0:
                        thread_dict['new_messages'] = thread.new_messages
                        thread_dict['unread'] = True
                    else:
                        thread_dict['unread'] = False

                result['threads'].append(thread_dict)

            self.response.out.write(json.dumps(result))
        else:
            context = {}
            context['user'] = {
                'threads_counter': user.threads_counter,
                'new_messages': user.new_messages
            }
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
            when = datetime.now()
        )

        message_thread = models.MessageThread(
            messages = [message],
            subject = subject,
            sender = user.key,
            receiver = receiver.key,
            updated = message.when
        )
        user.threads_counter += 1
        receiver.threads_counter += 1
        receiver.new_messages += 1
        ndb.put_multi([message_thread, user, receiver])
        
        self.response.out.write(json.dumps({
            'error': False,
            'message':'message sent!'
        }))

def message_author_required(handler):
    def check_message_author(self, thread_id):
        xrequest = self.request.headers.get('X-Requested-With')
        user = self.user
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread:
            error_msg = 'message does not exist.'
            if xrequest and xrequest == 'XMLHttpRequest':
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': error_msg
                }))
            else:
                self.notify(error_msg);
            return

        if thread.sender:
            if thread.sender.id() != user.key.id():
                is_user_sender = False
            else:
                is_user_sender = True
        else:
            is_user_sender = False

        if not(is_user_sender):
            if thread.receiver:
                if thread.receiver.id() != user.key.id():
                    is_user_receiver = False
                else:
                    is_user_receiver = True
            else:
                is_user_receiver = False

        if not(is_user_sender or is_user_receiver):
            error_msg = 'message does not exist.'
            if xrequest and xrequest == 'XMLHttpRequest':
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': error_msg
                }))
            else:
                self.notify(error_msg);
            return

        else:
            self.is_user_sender = is_user_sender
            self.thread = thread
            return handler(self, thread_id)
 
    return check_message_author

class Detail(BaseHandler):
    @message_author_required
    @login_required
    def get(self, thread_id):
        user = self.user
        thread = self.thread

        context = {}
        context['subject'] = thread.subject
        if thread.delete_user:
            partner = thread.delete_user.get() # the other user deleted the message
        else:
            if self.is_user_sender:
                partner = thread.receiver.get()
            else:
                partner =thread.sender.get()
        context['partner'] = partner.get_public_info()

        context['messages'] = []
        for msg in thread.messages:
            message = {}
            if msg.sender.id() == user.key.id():
                message['is_sender_user'] = True
            else:
                message['is_sender_user'] = False
            message['content'] = msg.content
            message['when'] = msg.when.strftime("%Y-%m-%d %H:%M")
            context['messages'].append(message)

        self.render('message_detail', context)

        if thread.messages[-1].sender.id() != user.key.id():
            user.new_messages -= thread.new_messages
            thread.new_messages = 0
            ndb.put_multi([thread, user])

    @message_author_required
    @login_required
    def post(self, thread_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        thread = self.thread

        content = self.request.get('content')
        if not content.strip():
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'content cannot be empty.'
            }))
            return

        if thread.messages[-1].sender.id() != user.key.id():
            user.new_messages -= thread.new_messages
            thread.new_messages = 0
            user.put()

        message = models.Message(
            sender = user.key,
            content = content,
            when = datetime.now(),
        )
        thread.messages.append(message)
        thread.new_messages += 1
        thread.updated = message.when
        if thread.delete_user:
            partner = thread.delete_user.get()
            partner.threads_counter += 1
            partner.new_messages += thread.new_messages
            if thread.sender:
                thread.receiver = thread.delete_user
            else:
                thread.sender = thread.delete_user
            thread.delete_user = None
        else:
            if self.is_user_sender:
                partner = thread.receiver.get()
            else:
                partner = thread.sender.get()
            partner.new_messages += 1
        ndb.put_multi([thread, partner])

        self.response.out.write(json.dumps({
            'error': False,
            'message': 'message sent.',
            'when': message.when.strftime("%Y-%m-%d %H:%M"),
            'content': message.content
        }))

class DeleteMessage(BaseHandler):
    @message_author_required
    @login_required
    def post(self, thread_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        thread = self.thread

        user.threads_counter -= 1
        if thread.messages[-1].sender.id() != user.key.id(): # user has unread new messages when deleting
            user.new_messages -= thread.new_messages
        user.put()

        if thread.delete_user: # The other user has already deleted the message
            thread.key.delete()
        else:
            thread.delete_user = user.key
            if self.is_user_sender:
                thread.sender = None
            else:
                thread.receiver = None
            thread.put()


        self.response.out.write(json.dumps({
            'error': False,
            'message': 'success'
        }))

class Mentioned(BaseHandler):
    def new_mentions_count(self):
        user = self.user
        new_count = models.MentionedComment.query(ndb.AND(models.MentionedComment.receivers==user.key, 
                                                                models.MentionedComment.created > user.last_mentioned_check)).count()
        return new_count

    @login_required
    def get_count(self):
        self.response.headers['Content-Type'] = 'application/json'
        new_messages = self.new_mentions_count()
        self.response.out.write(json.dumps({
            'error': False,
            'count': new_messages,
        }))

    @login_required
    def get(self):
        user = self.user
        new_messages = self.new_mentions_count()
        user.last_mentioned_check = datetime.now()
        user.put()
        if new_messages > 99:
            self.response.set_cookie('new_mentions', '99+', path='/')
        elif new_messages == 0:
            self.response.set_cookie('new_mentions', '', path='/')
        else:
            self.response.set_cookie('new_mentions', str(new_messages), path='/')
        self.render('mentioned_me', {'new_messages': new_messages})

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        page_size = 20

        # urlsafe = self.request.get('cursor')
        # logging.info(urlsafe)
        # if urlsafe:
        result = {'error': False}
        result['comments'] = []

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        comments, cursor, more = models.MentionedComment.query(models.MentionedComment.receivers==user.key).order(-models.MentionedComment.created, models.MentionedComment.key).fetch_page(page_size, start_cursor=cursor)
        for i in range(0, len(comments)):
            comment = comments[i]
            video = comment.video.get()
            sender = comment.sender.get()
            comment_info = {
                'sender': sender.get_public_info(),
                'type': comment.comment_type,
                'timestamp': comment.timestamp,
                'floorth': comment.floorth,
                'inner_floorth': comment.inner_floorth,
                'content': comment.content,
                'created': comment.created.strftime("%Y-%m-%d %H:%M"),
                'video': video.get_basic_info(),
                'clip_index': comment.clip_index,
            }
            result['comments'].append(comment_info)
        if not cursor:
            result['cursor'] = ''
        else:
            result['cursor'] = cursor.urlsafe()
        
        self.response.out.write(json.dumps(result))

class Notifications(BaseHandler):
    def new_notifications_count(self):
        user = self.user
        new_count = models.Notification.query(ndb.AND(models.Notification.receiver==user.key, 
                                                                models.Notification.created > user.last_notification_check)).count()
        return new_count

    @login_required
    def get_count(self):
        self.response.headers['Content-Type'] = 'application/json'
        new_messages = self.new_notifications_count()
        self.response.out.write(json.dumps({
            'error': False,
            'count': new_messages,
        }))

    @login_required
    def get(self):
        user = self.user
        new_notifications = self.new_notifications_count()
        user.last_notification_check = datetime.now()
        user.put()
        if new_notifications > 99:
            self.response.set_cookie('new_notifications', '99+', path='/')
        elif new_notifications == 0:
            self.response.set_cookie('new_notifications', '', path='/')
        else:
            self.response.set_cookie('new_notifications', str(new_notifications), path='/')
        self.render('notifications', {'new_notifications': new_notifications})

    @login_required
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        page_size = 20

        result = {'error': False}
        result['notifications'] = []

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        notifications, cursor, more = models.Notification.query(models.Notification.receiver==user.key).order(-models.Notification.created, models.Notification.key).fetch_page(page_size, start_cursor=cursor)
        for i in range(0, len(notifications)):
            notification = notifications[i]
            note_info = {
                'type': notification.note_type,
                'content': notification.content,
                'created': notification.created.strftime("%Y-%m-%d %H:%M"),
                'read': notification.read,
                'title': notification.title,
                'id': notification.key.id(),
            }
            result['notifications'].append(note_info)
        if not cursor:
            result['cursor'] = ''
        else:
            result['cursor'] = cursor.urlsafe()
        
        self.response.out.write(json.dumps(result))

    @login_required
    def read(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user

        try:
            note_id = int(self.request.get('id'))
        except Exception, e:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Invalid id.'
            }))
            return

        note = models.Notification.get_by_id(note_id)
        if not note:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No notification found.'
            }))

        note.read = True
        note.put()

        self.response.out.write(json.dumps({
            'error': False,
        }))

    @login_required
    def delete(self):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No notification selected.'
            }))
            return

        deleted_ids = []
        for i in range(0, len(ids)):
            try:
                note_id = int(ids[i])
            except Exception, e:
                continue

            note = models.Notification.get_by_id(note_id)
            if note is None or note.receiver.id() != user.key.id():
                continue

            note.key.delete()
            deleted_ids.append(note_id)

        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No notification deleted.'
            }))
            return

        self.response.out.write(json.dumps({
            'error': False,
            'message': deleted_ids,
        }))
