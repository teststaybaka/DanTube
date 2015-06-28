from views import *

class Message(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        page_size = 20
        page = self.get_page_number()

        thread_keys = models.MessageThread.query(ndb.AND(ndb.OR(models.MessageThread.sender==user.key, models.MessageThread.receiver==user.key), models.MessageThread.delete_user!=user.key)) \
                                                    .order(models.MessageThread.delete_user, -models.MessageThread.updated, models.MessageThread.key).fetch(offset=(page-1)*page_size, limit=page_size, keys_only=True)
        threads = ndb.get_multi(thread_keys)
        context = {
            'threads_counter': user.threads_counter,
            'new_messages': user.new_messages,
            'entries': [],
        }
        partner_keys = []
        for i in range(0, len(threads)):
            thread = threads[i]
            thread_dict = {}
            thread_dict['id'] = thread.key.id()
            thread_dict['subject'] = thread.subject
            thread_dict['last_message'] = thread.messages[-1].content
            thread_dict['updated'] = thread.updated.strftime("%Y-%m-%d %H:%M")
            if thread.sender == user.key:
                partner_keys.append(thread.receiver)
                thread_dict['is_sender'] = True
                thread_dict['unread'] = False
            else:
                partner_keys.append(thread.sender)
                thread_dict['is_sender'] = False
                if thread.new_messages > 0:
                    thread_dict['new_messages'] = thread.new_messages
                    thread_dict['unread'] = True
                else:
                    thread_dict['unread'] = False
            context['entries'].append(thread_dict)

        partners = ndb.get_multi(partner_keys)
        for i in range(0, len(partners)):
            partner = partners[i]
            context['entries'][i]['partner'] = partner.get_public_info()

        context.update(self.get_page_range(page, math.ceil(user.threads_counter/float(page_size))))
        self.render('message', context)

class Compose(BaseHandler):
    @login_required
    def get(self):
        self.render('message_compose')

    @login_required_json
    def post(self):
        user = self.user
        receiver_nickname = self.request.get('receiver').strip()
        if not receiver_nickname:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Receiver cannot be empty.'
            }))
            return
        elif receiver_nickname == user.nickname:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Receiver cannot be self.'
            }))
            return

        subject = self.request.get('subject').strip()
        if not subject:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subject cannot be empty.'
            }))
            return
        elif len(subject) > 400:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Subject is too long.'
            }))
            return

        content = self.request.get('content').strip()
        if not content:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Content cannot be empty.'
            }))
            return
        elif len(content) > 2000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Content is too long.'
            }))
            return

        receiver = models.User.query(models.User.nickname==receiver_nickname).get()
        if not receiver:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Receiver not found.'
            }))
            return

        message = models.Message(sender=user.key, content=content, when=datetime.now())
        message_thread = models.MessageThread(messages=[message], subject=subject, sender=user.key, receiver=receiver.key, new_messages=0, updated=message.when)
        message_thread.new_messages += 1
        user.threads_counter += 1
        receiver.threads_counter += 1
        receiver.new_messages += 1
        ndb.put_multi([message_thread, user, receiver])
        
        self.response.out.write(json.dumps({
            'error': False,
            'message':'Message sent!'
        }))

def message_author_required_json(handler):
    def check_message_author(self, thread_id):
        self.response.headers['Content-Type'] = 'application/json'
        user = self.user
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread:
            self.response.out.write(json.dumps({
                'error': True,
                'message': "Message does not exist.",
            }))
            return

        if user.key == thread.delete_user or (thread.sender != user.key and thread.receiver != user.key):
            self.response.out.write(json.dumps({
                'error': True,
                'message': "Message does not exist.",
            }))
            return

        return handler(self, thread)

    return check_message_author

def message_author_required(handler):
    def check_message_author(self, thread_id):
        user = self.user
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread:
            self.notify("Message does not exist.");
            return

        if user.key == thread.delete_user or (thread.sender != user.key and thread.receiver != user.key):
            self.notify("Message does not exist.");
            return

        return handler(self, thread)
 
    return check_message_author

class Detail(BaseHandler):
    @login_required
    @message_author_required
    def get(self, thread):
        user = self.user

        context = {}
        context['thread_id'] = thread.key.id()
        context['subject'] = thread.subject
        context['messages'] = []
        for msg in thread.messages:
            message = {}
            if msg.sender == user.key:
                message['is_sender'] = True
            else:
                message['is_sender'] = False
            message['content'] = msg.content
            message['when'] = msg.when.strftime("%Y-%m-%d %H:%M")
            context['messages'].append(message)

        if thread.receiver == user.key:
            user.new_messages -= thread.new_messages
            thread.new_messages = 0
            ndb.put_multi([thread, user])
            partner = thread.sender.get()
        else:
            partner = thread.receiver.get()
        context['partner'] = partner.get_public_info()

        self.render('message_detail', context)

    @login_required_json
    @message_author_required_json
    def post(self, thread):
        user = self.user

        content = self.request.get('content').strip()
        if not content:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Content cannot be empty.'
            }))
            return
        elif len(content) > 2000:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Content is too long.'
            }))
            return

        if thread.receiver == user.key:
            user.new_messages -= thread.new_messages
            thread.receiver = thread.sender
            thread.sender = user.key
            thread.new_messages = 0

        message = models.Message(sender=user.key, content=content, when=datetime.now())
        thread.messages.append(message)
        thread.new_messages += 1
        thread.updated = message.when
        
        partner = thread.receiver.get()
        if thread.delete_user:
            thread.delete_user = None
            partner.threads_counter += 1
            partner.new_messages += thread.new_messages
        else:
            partner.new_messages += 1

        ndb.put_multi([thread, partner, user])

        self.response.out.write(json.dumps({
            'error': False,
            'message': 'Message sent.',
            'when': message.when.strftime("%Y-%m-%d %H:%M"),
            'content': message.content
        }))

class DeleteMessage(BaseHandler):
    @login_required_json
    def post(self):
        user = self.user

        ids = self.request.POST.getall('ids[]')
        if len(ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No message selected.'
            }))
            return

        deleted_ids = []
        put_list = []
        for i in range(0, len(ids)):
            try:
                thread_id = int(ids[i])
                thread = models.MessageThread.get_by_id(thread_id)
                if not thread or user.key == thread.delete_user or (thread.sender != user.key and thread.receiver != user.key):
                    raise Exception('error')
            except Exception, e:
                continue

            user.threads_counter -= 1
            if user.key == thread.receiver:
                user.new_messages -= thread.new_messages # In case, user has unread new messages when deleting

            if thread.delete_user: # The other user has already deleted the message
                thread.key.delete()
            else:
                thread.delete_user = user.key
                put_list.append(thread)
            deleted_ids.append(thread_id)
        
        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No message deleted.'
            }))
            return
        ndb.put_multi([user] + put_list)

        self.response.out.write(json.dumps({
            'error': False,
            'message': deleted_ids,
        }))

class Mentioned(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        new_mentions = user.new_mentions
        user.new_mentions = 0
        user.put()
        self.render('mentioned_me', {'new_mentions': new_mentions})

    @login_required_json
    def post(self):
        user = self.user
        page_size = 20

        # urlsafe = self.request.get('cursor')
        # logging.info(urlsafe)
        # if urlsafe:
        result = {'error': False}
        result['entries'] = []

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        comments, cursor, more = models.MentionedComment.query(models.MentionedComment.receivers==user.key).order(-models.MentionedComment.created, models.MentionedComment.key).fetch_page(page_size, start_cursor=cursor)
        videos = ndb.get_multi([comment.video for comment in comments])
        senders = ndb.get_multi([comment.sender for comment in comments])
        for i in range(0, len(comments)):
            comment = comments[i]
            video = videos[i]
            sender = senders[i]
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
            result['entries'].append(comment_info)
        if not cursor:
            result['cursor'] = ''
        else:
            result['cursor'] = cursor.urlsafe()
        
        self.response.out.write(json.dumps(result))

class Notifications(BaseHandler):
    @login_required
    def get(self):
        user = self.user
        page_size = 20
        page = self.get_page_number()

        context = {}
        context['new_notifications'] = user.new_notifications
        context['entries'] = []

        notification_keys = models.Notification.query(models.Notification.receiver==user.key).order(-models.Notification.created, models.Notification.key).fetch(offset=(page-1)*page_size, limit=page_size, keys_only=True)
        notifications = ndb.get_multi(notification_keys)
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
            context['entries'].append(note_info)
        
        context.update(self.get_page_range(page, math.ceil(user.notification_counter/float(page_size))))
        self.render('notifications', context)

class ReadNotification(BaseHandler):
    @login_required_json
    def post(self):
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
            return
        elif note.read:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'Notification already read.'
            }))
            return

        note.read = True
        if user.new_notifications != 0:
            user.new_notifications -= 1
        ndb.put_multi([note, user])

        self.response.out.write(json.dumps({
            'error': False,
        }))

class DeleteNotifications(BaseHandler):
    @login_required_json
    def post(self):
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
                note = models.Notification.get_by_id(note_id)
                if note is None or note.receiver.id() != user.key.id():
                    raise Exception('error')
            except Exception, e:
                continue

            if not note.read:
                user.new_notifications -= 1
            user.notification_counter -= 1
            deleted_ids.append(note_id)
            note.key.delete()

        if len(deleted_ids) == 0:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'No notification deleted.'
            }))
            return
        user.put()

        self.response.out.write(json.dumps({
            'error': False,
            'message': deleted_ids,
        }))
