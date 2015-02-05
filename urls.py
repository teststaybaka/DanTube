import webapp2

import views, admin, login, account, video
import models

secret_key = 'efrghtrrouhsmvnmxdiosjkgjfds68_=' \
             'iooijgrdxuihbvc97yutcivbhugd479k'
config = {
    'webapp2_extras.auth': {
        'user_model' : 'models.User',
        'user_attributes': ['nickname', 'email']
    },
    'webapp2_extras.sessions': {
        'secret_key': secret_key
    }
}

routes = [
    webapp2.Route(r'/', views.Home, name="home"),
    webapp2.Route(r'/signin', login.Signin, name="signin"),
    webapp2.Route(r'/signup', login.Signup, name="signup"),
    webapp2.Route(r'/email_check', login.EmailCheck, name="email_check"),
    webapp2.Route(r'/nickname_check', login.NicknameCheck, name="nickname_check"),
    webapp2.Route(r'/logout', login.Logout, name="logout"),
    webapp2.Route(r'/password/forgot', login.ForgotPassword, name="forgot_password"),
    webapp2.Route(r'/password/reset/<user_id:\d+>-<pwdreset_token:.+>', login.ForgotPasswordReset, name="forgot_password_reset"),

    webapp2.Route(r'/account', account.Account, name="account"),
    webapp2.Route(r'/account/nickname', account.ChangeNickname, name="change_nickname"),
    webapp2.Route(r'/account/avatar', account.ChangeAvatar, name="change_avatar"),
    webapp2.Route(r'/account/avatar/upload/<user_id:\d+>', account.AvatarUpload, name="avatar_upload"),
    webapp2.Route(r'/account/password', account.ChangePassword, name="change_password"),
    webapp2.Route(r'/account/video', account.ManageVideo, name="manage_video"),
    webapp2.Route(r'/account/favorites', account.Favorites, name="favorites"),
    webapp2.Route(r'/account/subscriptions', account.Subscriptions, name="subscriptions"),
    webapp2.Route(r'/subscriptions', account.Subscriptions, name="subscriptions_quick", handler_method='quick'),
    webapp2.Route(r'/account/subscribed', account.Subscribed, name="subscribed_users"),
    webapp2.Route(r'/history', account.History, name="history"),    
    webapp2.Route(r'/verify', account.SendVerification, name='send_verification'),
    webapp2.Route(r'/verify/<user_id:\d+>-<signup_token:.+>', account.Verification, name='verification'),

    webapp2.Route(r'/user/<user_id:\d+>', views.Space, name='space'),
    webapp2.Route(r'/user/<user_id:\d+>/subscribe', views.Subscribe, name='subscribe'),
    webapp2.Route(r'/user/<user_id:\d+>/unsubscribe', views.Unsubscribe, name='unsubscribe'),
    webapp2.Route(r'/submit', video.Submit, name="submit"),
    webapp2.Route(r'/cover_upload/dt<video_id:\d+>', video.Submit, name="cover_upload", handler_method='cover_upload'),

    webapp2.Route(r'/video', views.Video, name="video"),
    webapp2.Route(r'/video/dt<video_id:\d+>', views.Watch, name="watch"),
    webapp2.Route(r'/video/dt<video_id:\d+>/danmaku', views.Danmaku, name="danmaku"),
    webapp2.Route(r'/video/dt<video_id:\d+>/favor', views.Favor, name="favor"),
    webapp2.Route(r'/video/dt<video_id:\d+>/unfavor', views.Unfavor, name="unfavor"),
    webapp2.Route(r'/player', views.Player, name="player"),
    webapp2.Route(r'/search', views.Search, name="search"),

    webapp2.Route(r'/admin/video', admin.VideoPageTest, name="Admin_Video"),
    webapp2.Route(r'/admin/danmaku', admin.DanmakuTest, name="Admin_Danmaku"),
]
for category in models.Video_Category:
    route = webapp2.Route(r'/%s' % models.URL_NAME_DICT[category][0], views.Category, name=category)
    routes.append(route)
    for subcategory in models.Video_SubCategory[category]:
        route = webapp2.Route(r'/%s/%s' % (models.URL_NAME_DICT[category][0], models.URL_NAME_DICT[category][1][subcategory]),
            views.Subcategory, name=category + '-' + subcategory)
        routes.append(route)

application = webapp2.WSGIApplication(routes, debug=True, config=config)
