import webapp2

import views, admin, login, account, video, message, user, playlist, watch
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
    webapp2.Route(r'/account/info', account.ChangeInfo, name="change_info"),
    webapp2.Route(r'/account/avatar', account.ChangeAvatar, name="change_avatar"),
    webapp2.Route(r'/account/avatar/upload/<user_id:\d+>', account.AvatarUpload, name="avatar_upload"),
    webapp2.Route(r'/account/password', account.ChangePassword, name="change_password"),
    webapp2.Route(r'/account/favorites', account.Favorites, name="favorites"),
    webapp2.Route(r'/account/favor/dt<video_id:\d+>', account.Favor, name="favor"),
    webapp2.Route(r'/account/favorites/remove', account.Unfavor, name="unfavor"),
    webapp2.Route(r'/account/subscriptions', account.Subscriptions, name="subscriptions"),
    webapp2.Route(r'/subscriptions', account.Subscriptions, name="subscriptions_quick", handler_method='quick'),
    webapp2.Route(r'/account/subscribed', account.Subscribed, name="subscribed_users"),
    webapp2.Route(r'/account/space', account.SpaceSetting, name="space_setting"),
    webapp2.Route(r'/account/css_upload', account.SpaceSetting, name="css_upload", handler_method='css_upload'),
    webapp2.Route(r'/account/space_reset', account.SpaceSetting, name="space_setting_reset", handler_method='reset'),
    webapp2.Route(r'/user/css/<resource:.+>', account.SpaceCSS, name="space_css"),
    webapp2.Route(r'/history', account.History, name="history"),
    webapp2.Route(r'/verify', account.SendVerification, name='send_verification'),
    webapp2.Route(r'/verify/<user_id:\d+>-<signup_token:.+>', account.Verification, name='verification'),
    
    webapp2.Route(r'/account/messages', message.Message, name='message'),
    webapp2.Route(r'/account/messages/<thread_id:\d+>', message.Detail, name='message_detail'),
    webapp2.Route(r'/account/messages/delete/<thread_id:\d+>', message.DeleteMessage, name='delete_message'),
    webapp2.Route(r'/account/messages/compose', message.Compose, name='compose'),
    webapp2.Route(r'/account/mentioned', message.Mentioned, name='mentioned'),
    webapp2.Route(r'/account/notifications', message.Notifications, name='notifications'),

    webapp2.Route(r'/user/<user_id:\d+>', user.Space, name='space'),
    webapp2.Route(r'/user/playlist/<user_id:\d+>', user.SpacePlaylist, name='space_playlist'),
    webapp2.Route(r'/user/board/<user_id:\d+>', user.SpaceBoard, name='space_board'),
    webapp2.Route(r'/user/<user_id:\d+>/subscribe', user.Subscribe, name='subscribe'),
    webapp2.Route(r'/user/<user_id:\d+>/unsubscribe', user.Unsubscribe, name='unsubscribe'),

    webapp2.Route(r'/submit', video.VideoUpload, name="submit", handler_method="submit"),
    webapp2.Route(r'/submit_post', video.VideoUpload, name="submit_post", handler_method="submit_post"),
    webapp2.Route(r'/cover_upload', video.CoverUpload, name="cover_upload"),
    webapp2.Route(r'/account/video', video.ManageVideo, name="manage_video"),
    webapp2.Route(r'/account/video/edit/dt<video_id:\d+>', video.VideoUpload, name="edit_video", handler_method="edit"),
    webapp2.Route(r'/account/video/edit_post/dt<video_id:\d+>', video.VideoUpload, name="edit_video_post", handler_method="edit_post"),
    webapp2.Route(r'/account/video/delete', video.DeleteVideo, name="delete_video"),

    webapp2.Route(r'/account/playlists', playlist.ManagePlaylist, name="manage_playlist"),
    webapp2.Route(r'/account/playlists/create', playlist.PlaylistInfo, name="create_playlist", handler_method="create"),
    webapp2.Route(r'/account/playlists/edit/<playlist_id:\d+>', playlist.EditPlaylist, name="edit_playlist"),
    webapp2.Route(r'/account/playlists/edit/info/<playlist_id:\d+>', playlist.PlaylistInfo, name="edit_playlist_info", handler_method="edit"),
    webapp2.Route(r'/account/playlists/delete', playlist.DeletePlaylist, name="delete_playlist"),
    webapp2.Route(r'/account/playlists/search_video', playlist.SearchVideo, name="search_video_to_list"),
    webapp2.Route(r'/account/playlists/edit/add/<playlist_id:\d+>', playlist.AddVideo, name="add_video_to_list"),
    webapp2.Route(r'/account/playlists/edit/remove/<playlist_id:\d+>', playlist.RemoveVideo, name="remove_video_from_list"),
    webapp2.Route(r'/account/playlists/edit/move/<playlist_id:\d+>', playlist.MoveVideo, name="move_video_in_list"),

    webapp2.Route(r'/video/dt<video_id:\d+>', watch.Video, name="watch"),
    webapp2.Route(r'/video/comment/dt<video_id:\d+>', watch.Comment, name="comment", handler_method="get_comment"),
    webapp2.Route(r'/video/comment/dt<video_id:\d+>', watch.Comment, name="comment", handler_method="get_comment"),
    webapp2.Route(r'/video/comment_post/dt<video_id:\d+>', watch.Comment, name="comment_post", handler_method="comment_post"),
    webapp2.Route(r'/video/reply_post/dt<video_id:\d+>', watch.Comment, name="reply_post", handler_method="reply_post"),
    webapp2.Route(r'/video/danmaku/dt<video_id:\d+>', watch.Danmaku, name="danmaku"),
    webapp2.Route(r'/video/like/dt<video_id:\d+>', watch.Like, name="like"),

    webapp2.Route(r'/video/category', views.CategoryVideo, name="category_video"),
    webapp2.Route(r'/video/random', video.RandomVideos, name="random_videos"),
    webapp2.Route(r'/search', views.Search, name="search"),
    webapp2.Route(r'/search/playlist', views.SearchPlaylist, name="search_playlist"),
    webapp2.Route(r'/search/uper', views.SearchUPer, name="search_uper"),

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
