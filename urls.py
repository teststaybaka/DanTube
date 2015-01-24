import webapp2

import views, admin, login, account
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
    webapp2.Route(r'/account', account.Account, name="account"),
    webapp2.Route(r'/account/change_password', account.ChangePassword, name="change_password"),

    webapp2.Route(r'/password/reset/<user_id:\d+>-<pwdreset_token:.+>', views.ForgotPasswordReset, name="forgot_password_reset"),
    webapp2.Route(r'/password/reset', views.PasswordReset, name="password_reset"),
    webapp2.Route(r'/password/forgot', views.ForgotPassword, name="forgot_password"),
    webapp2.Route(r'/verify', views.SendVerification, name='send_verification'),
    webapp2.Route(r'/verify/<user_id:\d+>-<signup_token:.+>', views.Verification, name='verification'),

    webapp2.Route(r'/settings', views.BasicsSetting, name="settings"),
    webapp2.Route(r'/settings/basics', views.BasicsSetting, name="basics_setting"),
    webapp2.Route(r'/settings/avatar', views.AvatarSetting, name="avatar_setting"),
    webapp2.Route(r'/settings/avatar/upload', views.AvatarUpload, name="avatar_upload"),
    webapp2.Route(r'/submit', views.Submit, name="submit"),
    webapp2.Route(r'/video', views.Video, name="video"),
    webapp2.Route(r'/video/dt<video_id:\d+>', views.Watch, name="watch"),
    webapp2.Route(r'/video/dt<video_id:\d+>/danmaku', views.Danmaku, name="danmaku"),
    webapp2.Route(r'/player', views.Player, name="player"),

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
