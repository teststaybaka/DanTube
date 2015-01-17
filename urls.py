import webapp2

import views, admin

secret_key = 'efrghtrrouhsmvnmxdiosjkgjfds68_=' \
             'iooijgrdxuihbvc97yutcivbhugd479k'
config = {
    'webapp2_extras.auth': {
        'user_model' : 'models.User',
        'user_attributes': ['username', 'email']
    },
    'webapp2_extras.sessions': {
        'secret_key': secret_key
    }
}

application = webapp2.WSGIApplication(
    [
        webapp2.Route(r'/', views.Home, name="home"),
        webapp2.Route(r'/signin', views.Signin, name="signin"),
        webapp2.Route(r'/signup', views.Signup, name="signup"),
        webapp2.Route(r'/logout', views.Logout, name="logout"),
        webapp2.Route(r'/submit', views.Submit, name="submit"),
        webapp2.Route(r'/video', views.Video, name="post-video", methods=['POST']),
        webapp2.Route(r'/video/dt<video_id:\d+>', views.Video, name="get-video", methods=['GET']),
        webapp2.Route(r'/video/dt<video_id:\d+>/danmaku', views.Danmaku, name="danmaku"),
        webapp2.Route(r'/videolist', views.Videolist, name="videolist"),
        webapp2.Route(r'/player', views.Player, name="player"),

        webapp2.Route(r'/admin/video', admin.VideoPageTest, name="Admin_Video"),
        webapp2.Route(r'/admin/danmaku', admin.DanmakuTest, name="Admin_Danmaku"),
        ], debug=True
    , config=config)
