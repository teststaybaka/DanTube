import webapp2

import views

secret_key = 'efrghtrrouhsmvnmxdiosjkgjfds68_=' \
             'iooijgrdxuihbvc97yutcivbhugd479k'
session_arg = dict(secret_key=secret_key)  # , session_max_age=10)
config = {'webapp2_extras.sessions': session_arg}

application = webapp2.WSGIApplication(
    [
        webapp2.Route(r'/', views.Home, name="home"),
        webapp2.Route(r'/signin', views.Signin, name="signin"),
        webapp2.Route(r'/signup', views.Signup, name="signup"),
        webapp2.Route(r'/video', views.Video, name="post-video", methods=['POST']),
        webapp2.Route(r'/video/dt<video_id:\d+>', views.Video, name="get-video", methods=['GET']),
        webapp2.Route(r'/video/dt<video_id:\d+>/danmaku', views.Danmaku, name="danmaku"),
        ], debug=True
    , config=config)
