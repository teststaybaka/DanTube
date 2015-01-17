import webapp2

import views, admin
import models

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

routes = [
    webapp2.Route(r'/', views.Home, name="home"),
    webapp2.Route(r'/signin', views.Signin, name="signin"),
    webapp2.Route(r'/signup', views.Signup, name="signup"),
    webapp2.Route(r'/logout', views.Logout, name="logout"),
    webapp2.Route(r'/submit', views.Submit, name="submit"),
    webapp2.Route(r'/video', views.Video, name="post-video", methods=['POST']),
    webapp2.Route(r'/video/dt<video_id:\d+>', views.Video, name="get-video", methods=['GET']),
    webapp2.Route(r'/video/dt<video_id:\d+>/danmaku', views.Danmaku, name="danmaku"),
    webapp2.Route(r'/player', views.Player, name="player"),

    webapp2.Route(r'/admin/video', admin.VideoPageTest, name="Admin_Video"),
    webapp2.Route(r'/admin/danmaku', admin.DanmakuTest, name="Admin_Danmaku"),
]
for category in models.Video_Category:
    route = webapp2.Route(r'/%s' % models.URL_NAME_DICT[category], views.Category, name=category)
    routes.append(route)
    for subcategory in models.Video_SubCategory[category]:
        route = webapp2.Route(r'/%s/%s' % (models.URL_NAME_DICT[category], models.URL_NAME_DICT[subcategory]),
            views.Subcategory, name=category + '-' + subcategory)
        routes.append(route)

application = webapp2.WSGIApplication(routes, debug=True, config=config)
