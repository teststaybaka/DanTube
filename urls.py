import webapp2

import views

secret_key = 'efrghtrrouhsmvnmxdiosjkgjfds68_=' \
             'iooijgrdxuihbvc97yutcivbhugd479k'
session_arg = dict(secret_key=secret_key)  # , session_max_age=10)
config = {'webapp2_extras.sessions': session_arg}

application = webapp2.WSGIApplication(
    [
        webapp2.Route(r'/', views.Home, name="home"),
        ], debug=True
    , config=config)
