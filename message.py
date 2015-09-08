from views import *

class Message(BaseHandler):
    @login_required
    def get(self):
        self.user = user = self.user_key.get()
        context = {'new_messages': user.new_messages}
        self.render('message', context)

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.MEDIUM_PAGE_SIZE
        
        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        threads, cursor, more = models.MessageThread.query(models.MessageThread.users==user_key).order(-models.MessageThread.updated).fetch_page(page_size, start_cursor=cursor)
        context = {
            'entries': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        partner_keys = []
        for i in xrange(0, len(threads)):
            thread = threads[i]
            last_message = thread.messages[-1]
            thread_dict = {
                'id': thread.key.id(),
                'subject': thread.subject,
                'last_message': last_message.content,
                'updated': thread.updated.strftime("%Y-%m-%d %H:%M"),
            }
            if thread.is_sender(user_key):
                thread_dict['is_sender'] = True
                thread_dict['unread'] = False
            else:
                thread_dict['is_sender'] = False
                if thread.new_messages > 0:
                    thread_dict['new_messages'] = thread.new_messages
                    thread_dict['unread'] = True
                else:
                    thread_dict['unread'] = False

            partner_keys.append(thread.get_partner_key(user_key))
            context['entries'].append(thread_dict)

        partners = ndb.get_multi(partner_keys)
        for i in xrange(0, len(partners)):
            partner = partners[i]
            context['entries'][i]['partner'] = partner.get_public_info()

        self.json_response(False, context)

class Compose(BaseHandler):
    @login_required
    def get(self):
        self.render('message_compose')

    @login_required_json
    def post(self):
        receiver_nickname = self.request.get('receiver').strip()
        if not receiver_nickname:
            self.json_response(True, {'message': 'Receiver cannot be empty.'})
            return

        subject = self.request.get('subject').strip()
        if not subject:
            self.json_response(True, {'message': 'Subject cannot be empty.'})
            return
        elif models.ILLEGAL_REGEX.match(subject):
            self.json_response(True, {'message': 'Subject contains illegal characters.'})
            return
        elif len(subject) > 400:
            self.json_response(True, {'message': 'Subject is too long.'})
            return

        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'Content cannot be empty.'})
            return
        elif len(content) > 2000:
            self.json_response(True, {'message': 'Content is too long.'})
            return

        user_key = self.user_key
        receiver = models.User.query(models.User.nickname==receiver_nickname).get()
        if not receiver:
            self.json_response(True, {'message': 'Receiver not found.'})
            return
        elif receiver.key == user_key:
            self.json_response(True, {'message': 'Receiver cannot be self.'})
            return

        message = models.Message(sender=user_key, content=content, when=datetime.now())
        thread = models.MessageThread(messages=[message], subject=subject, users=[user_key, receiver.key], users_backup=[user_key, receiver.key], new_messages=0, updated=message.when)
        thread.new_messages += 1
        receiver.new_messages += 1
        ndb.put_multi([thread, receiver])
        
        self.json_response(False, {'message':'Message sent!'})

def message_author_required(handler):
    def check_message_author(self, thread_id):
        user_key = self.user_key
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread or user_key not in thread.users:
            self.notify("Message does not exist.");
            return

        return handler(self, thread)
 
    return check_message_author

def message_author_required_json(handler):
    def check_message_author(self, thread_id):
        user_key = self.user_key
        thread = models.MessageThread.get_by_id(int(thread_id))
        if not thread or user_key not in thread.users:
            self.json_response(True, {'message': "Message does not exist."})
            return

        return handler(self, thread)

    return check_message_author

class Detail(BaseHandler):
    @login_required
    @message_author_required
    def get(self, thread):
        user_key = self.user_key
        partner_key = thread.get_partner_key(user_key)
        user, partner = ndb.get_multi([user_key, partner_key])
        self.user = user

        context = {
            'thread_id': thread.key.id(),
            'subject': thread.subject,
            'messages': [],
        }
        for msg in thread.messages:
            message = {}
            if msg.sender == user.key:
                message['is_sender'] = True
            else:
                message['is_sender'] = False
            message['content'] = msg.content
            message['when'] = msg.when.strftime("%Y-%m-%d %H:%M")
            context['messages'].append(message)

        if not thread.is_sender(user_key) and thread.new_messages != 0:
            user.new_messages -= thread.new_messages
            if user.new_messages < 0:
                user.new_messages = 0
            thread.new_messages = 0
            ndb.put_multi([thread, user])
        
        context['partner'] = partner.get_public_info()
        self.render('message_detail', context)

    @login_required_json
    @message_author_required_json
    def post(self, thread):
        content = self.request.get('content').strip()
        if not content:
            self.json_response(True, {'message': 'Content cannot be empty.'})
            return
        elif len(content) > 2000:
            self.json_response(True, {'message': 'Content is too long.'})
            return

        user_key = self.user_key
        partner_key = thread.get_partner_key(user_key)

        message = models.Message(sender=user_key, content=content, when=datetime.now())
        thread.messages.append(message)
        thread.new_messages += 1
        thread.updated = message.when
        
        partner = partner_key.get()
        if partner.key not in thread.users:
            thread.users.append(partner.key)
            partner.new_messages += thread.new_messages
        else:
            partner.new_messages += 1

        ndb.put_multi([thread, partner])
        self.json_response(False, {
            'message': 'Message sent.',
            'when': message.when.strftime("%Y-%m-%d %H:%M"),
            'content': message.content,
        })

class DeleteMessage(BaseHandler):
    @login_required_json
    def post(self):
        try:
            ids = self.get_ids()
            threads = ndb.get_multi([ndb.Key('MessageThread', int(identifier)) for identifier in ids])
        except ValueError:
            self.json_response(True, {'message': 'Invalid id.'})
            return

        user = self.user_key.get()
        put_list = []
        for i in xrange(0, len(ids)):
            thread = threads[i]
            if not thread or user.key not in thread.users:
                continue

            if not thread.is_sender(user.key):
                user.new_messages -= thread.new_messages # In case, user has unread new messages when deleting

            partner_key = thread.get_partner_key(user.key)
            if partner_key not in thread.users: # The other user has already deleted the message
                thread.key.delete()
            else:
                thread.users.remove(user.key)
                put_list.append(thread)

        if user.new_messages < 0:
            user.new_messages = 0
        ndb.put_multi([user] + put_list)
        self.json_response(False)

class Mentioned(BaseHandler):
    @login_required
    def get(self):
        self.user = user = self.user_key.get()
        new_mentions = user.new_mentions
        user.new_mentions = 0
        user.put()
        self.render('mentioned_me', {'new_mentions': new_mentions})

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        records, cursor, more = models.MentionedRecord.query(models.MentionedRecord.receivers==user_key).order(-models.MentionedRecord.created).fetch_page(page_size, start_cursor=cursor)
        targets = ndb.get_multi([record.target for record in records])

        result = {
            'entries': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(records)):
            target_key = records[i].target
            # if target_key.kind() == 'Video':
            #     video = targets[i]
            #     if not video:
            #         video_info = models.Video.get_deleted_video_info(record.target)
            #     else:
            #         video_info = video.get_basic_info()
            #     video_info['entry_type'] = 'Video'
            #     result['entries'].append(video_info)
            if target_key.kind() == 'Comment':
                comment = targets[i]
                comment_info = comment.get_content()
                comment_info['type'] = 'comment'
                result['entries'].append(comment_info)
            elif target_key.kind() == 'DanmakuRecord':
                danmaku_record = targets[i]
                danmaku_info = danmaku_record.get_content()
                danmaku_info['type'] = 'danmaku'
                result['entries'].append(danmaku_info)
        
        self.json_response(False, result)

class Notifications(BaseHandler):
    @login_required
    def get(self):
        self.user = user = self.user_key.get()
        context = {'new_notifications': user.new_notifications}
        self.render('notifications', context)

    @login_required_json
    def post(self):
        user_key = self.user_key
        page_size = models.MEDIUM_PAGE_SIZE

        cursor = models.Cursor(urlsafe=self.request.get('cursor'))
        notifications, cursor, more = models.Notification.query(models.Notification.receiver==user_key).order(-models.Notification.created, models.Notification.key).fetch_page(page_size, start_cursor=cursor)

        context = {
            'entries': [],
            'cursor': cursor.urlsafe() if more else '',
        }
        for i in xrange(0, len(notifications)):
            notification = notifications[i]
            note_info = {
                'type': notification.note_type,
                'content': notification.content,
                'created': notification.created.strftime("%Y-%m-%d %H:%M"),
                'read': notification.read,
                'title': notification.subject,
                'id': notification.key.id(),
            }
            context['entries'].append(note_info)
        
        self.json_response(False, context)

class ReadNotification(BaseHandler):
    @login_required_json
    def post(self):
        try:
            note_id = int(self.request.get('id'))
            note = models.Notification.get_by_id(note_id)
            if not note:
                raise Exception('Not found.')
        except Exception, e:
            self.json_response(True, {'message': 'Invalid id.'})
            return

        if note.read:
            self.json_response(False)
            return

        user = self.user_key.get()
        note.read = True
        user.new_notifications -= 1
        if user.new_notifications < 0:
            user.new_notifications = 0

        ndb.put_multi([note, user])
        self.json_response(False)

class DeleteNotifications(BaseHandler):
    @login_required_json
    def post(self):
        try:
            ids = self.get_ids()
            notifications = ndb.get_multi([ndb.Key('Notification', int(identifier)) for identifier in ids])
        except ValueError:
            self.json_response(True, {'message': 'Invalid id.'})
            return

        user = self.user_key.get()
        for i in xrange(0, len(ids)):
            note = notifications[i]
            if not note or note.receiver != user.key:
                continue

            if not note.read:
                user.new_notifications -= 1
            note.key.delete()

        if user.new_notifications < 0:
            user.new_notifications = 0
        user.put()
        self.json_response(False)
