import webapp2

import views, admin, login, account, video, message, user, playlist, watch, report, tasks
import models

secret_key = 'Mfrghtrrouhsmvnmxdiosjkgjfds68_=iooijgrdxuihbvc97yutcivbhugd409k'
developer_key = 'AIzaSyBbf3cs6Nw483po40jw7hZLejmdrgwozWc'
config = {
    'secret_key': secret_key,
    'developer_key': developer_key,
}

routes = [
    webapp2.Route(r'/', views.Home, name="home"),
    webapp2.Route(r'/signin', login.Signin, name="signin"),
    webapp2.Route(r'/signup', login.Signup, name="signup"),
    webapp2.Route(r'/email_check', login.EmailCheck, name="email_check"),
    webapp2.Route(r'/nickname_check', login.NicknameCheck, name="nickname_check"),
    webapp2.Route(r'/logout', login.Logout, name="logout"),
    webapp2.Route(r'/password/forgot', login.ForgotPassword, name="forgot_password"),
    webapp2.Route(r'/verify', login.SendVerification, name='send_verification'),
    webapp2.Route(r'/password/reset/<user_id:\d+>-<pwdreset_token:.+>', login.ForgotPasswordReset, name="forgot_password_reset"),
    webapp2.Route(r'/verify/<user_id:\d+>-<signup_token:.+>', login.Verification, name='verification'),

    webapp2.Route(r'/account', account.Account, name="account"),
    webapp2.Route(r'/account/info', account.ChangeInfo, name="change_info"),
    webapp2.Route(r'/account/avatar', account.ChangeAvatar, name="change_avatar"),
    # webapp2.Route(r'/account/avatar/upload/<user_id:\d+>', account.AvatarUpload, name="avatar_upload"),
    webapp2.Route(r'/account/password', account.ChangePassword, name="change_password"),
    webapp2.Route(r'/account/subscribed', account.Subscribed, name="subscribed_users"),
    webapp2.Route(r'/account/subscriptions', account.Subscriptions, name="subscriptions"),
    webapp2.Route(r'/subscriptions', account.SubscriptionQuick, name="subscriptions_quick"),
    # webapp2.Route(r'/user/new_subscriptions', account.Subscriptions, name="count_new_subscriptions", handler_method="get_count"),
    webapp2.Route(r'/account/space', account.SpaceSetting, name="space_setting"),
    webapp2.Route(r'/account/space_reset', account.SpaceSettingReset, name="space_setting_reset"),
    webapp2.Route(r'/account/css_upload', account.CSSUpload, name="css_upload"),
    webapp2.Route(r'/user/css/<resource:.+>', account.SpaceCSS, name="space_css"),
    webapp2.Route(r'/history', account.History, name="history"),
    webapp2.Route(r'/likes', account.Likes, name="likes"),
    
    webapp2.Route(r'/account/messages', message.Message, name='message'),
    webapp2.Route(r'/account/messages/<thread_id:\d+>', message.Detail, name='message_detail'),
    webapp2.Route(r'/account/messages/delete', message.DeleteMessage, name='delete_message'),
    webapp2.Route(r'/account/messages/compose', message.Compose, name='message_compose'),
    webapp2.Route(r'/account/mentioned', message.Mentioned, name='mentioned'),
    webapp2.Route(r'/account/notifications', message.Notifications, name='notifications'),
    webapp2.Route(r'/account/notifications/read', message.ReadNotification, name='read_note'),
    webapp2.Route(r'/account/notifications/delete', message.DeleteNotifications, name='delete_note'),

    webapp2.Route(r'/user/<user_id:\d+>', user.SpaceVideo, name='space_home'),
    webapp2.Route(r'/user/playlists/<user_id:\d+>', user.SpacePlaylist, name='space_playlist'),
    webapp2.Route(r'/user/comments/<user_id:\d+>', user.SpaceComment, name='space_comment'),
    webapp2.Route(r'/user/upers/<user_id:\d+>', user.FeaturedUpers, name='featured_upers'),
    webapp2.Route(r'/user/subscribe/<user_id:\d+>', user.Subscribe, name='subscribe'),
    webapp2.Route(r'/user/unsubscribe/<user_id:\d+>', user.Unsubscribe, name='unsubscribe'),

    webapp2.Route(r'/submit', video.VideoUpload, name="submit", handler_method="submit"),
    webapp2.Route(r'/submit_post', video.VideoUpload, name="submit_post", handler_method="submit_post"),
    webapp2.Route(r'/cover_upload', video.CoverUpload, name="cover_upload"),
    webapp2.Route(r'/video/new_tag/<video_id:dt\d+>', video.AddTag, name="add_tag"),
    webapp2.Route(r'/account/video', video.ManageVideo, name="manage_video"),
    webapp2.Route(r'/account/video/edit/<video_id:dt\d+>', video.VideoUpload, name="edit_video", handler_method="edit"),
    webapp2.Route(r'/account/video/edit_post/<video_id:dt\d+>', video.VideoUpload, name="edit_video_post", handler_method="edit_post"),
    webapp2.Route(r'/account/video/delete', video.DeleteVideo, name="delete_video"),
    webapp2.Route(r'/account/video/parts/<video_id:dt\d+>', video.ManageDanmaku, name="manage_danmaku"),
    webapp2.Route(r'/account/video/parts/danmaku/<video_id:dt\d+>/<clip_id:\d+>', video.ManageDanmakuDetail, name="manage_danmaku_detail"),
    webapp2.Route(r'/account/video/parts/danmaku/<video_id:dt\d+>/<clip_id:\d+>/delete', video.ManageDanmakuDetail, name="delete_danmaku", handler_method="delete"),
    webapp2.Route(r'/account/video/parts/danmaku/<video_id:dt\d+>/<clip_id:\d+>/confirm', video.ManageDanmakuDetail, name="confirm_danmaku", handler_method="confirm"),

    webapp2.Route(r'/account/playlists', playlist.ManagePlaylist, name="manage_playlist"),
    webapp2.Route(r'/account/playlists/create', playlist.PlaylistInfo, name="create_playlist", handler_method="create"),
    webapp2.Route(r'/account/playlists/edit/<playlist_id:\d+>', playlist.EditPlaylist, name="edit_playlist"),
    webapp2.Route(r'/account/playlists/edit/info/<playlist_id:\d+>', playlist.PlaylistInfo, name="edit_playlist_info", handler_method="edit"),
    webapp2.Route(r'/account/playlists/delete', playlist.DeletePlaylist, name="delete_playlist"),
    webapp2.Route(r'/account/playlists/search_video', playlist.SearchVideo, name="search_video_to_list"),
    webapp2.Route(r'/account/playlists/edit/<playlist_id:\d+>/add', playlist.AddVideo, name="add_video_to_list"),
    webapp2.Route(r'/account/playlists/edit/<playlist_id:\d+>/delete', playlist.RemoveVideo, name="remove_video_from_list"),
    webapp2.Route(r'/account/playlists/edit/<playlist_id:\d+>/move', playlist.MoveVideo, name="move_video_in_list"),

    webapp2.Route(r'/video/<video_id:dt\d+>', watch.Video, name="watch"),
    webapp2.Route(r'/video/list/<video_id:dt\d+>/<playlist_id:\d+>', watch.GetPlaylistVideo, name="get_list"),
    webapp2.Route(r'/video/comment/<video_id:dt\d+>', watch.Comment, name="comment", handler_method="get_comment"),
    webapp2.Route(r'/video/inner_comment/<video_id:dt\d+>', watch.Comment, name="inner_comment", handler_method="get_inner_comment"),
    webapp2.Route(r'/video/comment_post/<video_id:dt\d+>', watch.Comment, name="comment_post", handler_method="comment_post"),
    webapp2.Route(r'/video/reply_post/<video_id:dt\d+>', watch.Comment, name="reply_post", handler_method="reply_post"),
    webapp2.Route(r'/video/check_comment/<video_id:dt\d+>', watch.CheckComment, name="check_comment"),
    webapp2.Route(r'/video/danmaku/<video_id:dt\d+>/<clip_id:\d+>', watch.Danmaku, name="post_danmaku"),
    webapp2.Route(r'/video/advanced_danmaku/<video_id:dt\d+>/<clip_id:\d+>', watch.Danmaku, name="advanced_danmaku", handler_method="post_advanced"),
    webapp2.Route(r'/video/subtitles_danmaku/<video_id:dt\d+>/<clip_id:\d+>', watch.Danmaku, name="subtitles_danmaku", handler_method="post_subtitles"),
    webapp2.Route(r'/video/code_danmaku/<video_id:dt\d+>/<clip_id:\d+>', watch.Danmaku, name="code_danmaku", handler_method="post_code"),
    webapp2.Route(r'/video/like/<video_id:dt\d+>', watch.Like, name="like"),
    webapp2.Route(r'/video/unlike/<video_id:dt\d+>', watch.Unlike, name="unlike"),
    webapp2.Route(r'/video/watched/<video_id:dt\d+>', watch.Watched, name="watched"),
    webapp2.Route(r'/video/test', watch.Test, name="testwatch"),

    webapp2.Route(r'/category_videos', views.LoadByCategory, name="load_by_category"),
    webapp2.Route(r'/uper_videos', views.LoadByUper, name="load_by_uper"),
    webapp2.Route(r'/feelinglucky', views.FeelingLucky, name="feeling_lucky"),
    webapp2.Route(r'/search', views.SearchVideos, name="search"),
    webapp2.Route(r'/search/playlist', views.SearchPlaylists, name="search_playlist"),
    webapp2.Route(r'/search/uper', views.SearchUPers, name="search_uper"),

    webapp2.Route(r'/contact', report.Contact, name="contact"),
    webapp2.Route(r'/report/video/<video_id:dt\d+>/<clip_id:\d+>', report.Report, name="report_video", handler_method="video"),
    webapp2.Route(r'/report/comment/<video_id:dt\d+>/<clip_id:\d+>', report.Report, name="report_comment", handler_method="comment"),
    webapp2.Route(r'/report/danmaku/<video_id:dt\d+>/<clip_id:\d+>', report.Report, name="report_danmaku", handler_method="danmaku"),

    # webapp2.Route(r'/admin', admin.Home, name="Admin_Home"),
    webapp2.Route(r'/admin/delete/all', admin.DeleteAll, name="delete_all"),
    webapp2.Route(r'/admin/delete/videos', admin.DeleteVideos, name="delete_video"),
    webapp2.Route(r'/admin/nickname', admin.Nickname, name="nickname_change"),
    # webapp2.Route(r'/admin/video', admin.VideoPageTest, name="Admin_Video"),
    # webapp2.Route(r'/admin/danmaku', admin.DanmakuTest, name="Admin_Danmaku"),
    # webapp2.Route(r'/admin/notify', admin.Notify, name="Admin_Notify"),
    # webapp2.Route(r'/admin/feedbacks', admin.Feedbacks, name="Admin_Feedbacks"),
    # webapp2.Route(r'/admin/reports', admin.Reports, name="Admin_Reports"),
    webapp2.Route(r'/tasks/update_index', tasks.UpdateIndex, name="update_index"),
    webapp2.Route(r'/tasks/new_activites', tasks.NewActivity, name="new_activities"),
]
for category in models.Video_Category:
    route = webapp2.Route(r'/%s' % models.URL_NAME_DICT[category][0], views.Home, name=category, handler_method="second_level")
    routes.append(route)
    for subcategory in models.Video_SubCategory[category]:
        route = webapp2.Route(r'/%s/%s' % (models.URL_NAME_DICT[category][0], models.URL_NAME_DICT[category][1][subcategory]),
            views.Home, name=category + '-' + subcategory, handler_method="third_level")
        routes.append(route)

application = webapp2.WSGIApplication(routes, debug=True, config=config)
