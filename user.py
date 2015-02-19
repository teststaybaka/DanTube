from views import *

class Space(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        auth = self.auth
        if (not auth.get_user_by_session()) or int(user_id) != self.user.key.id():
            host.space_visited += 1
            host.put()

        self.render('space', {'host': host.get_public_info()})

class SpacePlaylist(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        self.render('space_playlist', {'host': host.get_public_info()})

class SpaceBoard(BaseHandler):
    def get(self, user_id):
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.notify('404 not found.', 404)
            return

        self.render('space_board', {'host': host.get_public_info()})


class Subscribe(BaseHandler):
    @login_required
    def post(self, user_id):
        self.response.headers['Content-Type'] = 'application/json'
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not found',
            }))
            return

        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'cannot subscribe self'
            }))
            return

        l = len(user.subscriptions)
        if host.key not in user.subscriptions:
            if l >= 1000:
                self.response.out.write(json.dumps({
                    'error': True,
                    'message': 'You have reached subscriptions limit.'
                }))
                return
        
            user.subscriptions.append(host.key)
            user.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
            host.subscribers_counter += 1
            host.put()
        else:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'already subscribed'
            }))

class Unsubscribe(BaseHandler):
    @login_required
    def post(self, user_id):
        self.response.headers['Content-Type'] = 'application/json'
        host = self.user_model.get_by_id(int(user_id))
        if not host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not found'
            }))
            return

        user = self.user
        if user == host:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'cannot unsubscribe self'
            }))
            return

        try:
            user.subscriptions.remove(host.key)
            user.put()
            self.response.out.write(json.dumps({
                'message': 'success'
            }))
            host.subscribers_counter -= 1
            host.put()
        except ValueError:
            self.response.out.write(json.dumps({
                'error': True,
                'message': 'user not subscribed'
            }))
