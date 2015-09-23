(function(dt, $) {
$(document).ready(function() {
    var content_type = $('.search-scope.active').text();

    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.history-container'), function(result) {
        var div = '';
        if (content_type === 'Views') {
            for (var i = 0; i < result.entries.length; i++) {
                var video = result.entries[i];
                div += '<div class="content-entry">\
                            <a class="video-img" href="'+video.url+'" target="_blank">\
                                <img src="'+video.thumbnail_url+'">\
                                <div class="preview-time">'+dt.secondsToTime(video.duration)+'</div>\
                            </a>\
                            <div class="video-info">\
                                <div class="video-info-line">\
                                    <a href="'+video.url+'?index='+(video.index+1)+'" class="normal-link" target="_blank">'+dt.escapeHTML(video.title)+'</a>\
                                </div>\
                                <div class="video-info-line">\
                                    <label class="by-label">by</label>\
                                    <a class="blue-link" href="'+video.uploader.space_url+'" target="_blank">'+video.uploader.nickname+'</a>\
                                </div>\
                                <div class="video-info-line">\
                                    <div class="video-statistic-entry">Views: '+dt.numberWithCommas(video.hits)+'</div>\
                                    <div class="video-statistic-entry">Likes: '+dt.numberWithCommas(video.likes)+'</div>\
                                    <div class="video-statistic-entry">Comments: '+dt.numberWithCommas(video.comment_counter)+'</div>\
                                    <div class="video-statistic-entry">Bullets: '+dt.numberWithCommas(video.bullets)+'</div>\
                                </div>\
                                <div class="video-info-line last-viewed">Last watched: '+video.last_viewed_time+'</div>\
                            </div>\
                        </div>'
            }
        } else {
            for (var i = 0; i < result.entries.length; i++) {
                var comment = result.entries[i];
                var cur_div = '<div class="content-entry comment">\
                            <a href="'+comment.creator.space_url+'" target="_blank">\
                              <img class="user-img" src="'+comment.creator.avatar_url_small+'">\
                            </a>\
                            <div class="message-info">\
                                <div class="info-line">\
                                    <a href="'+comment.creator.space_url+'" target="_blank" class="blue-link user-name">'+comment.creator.nickname+'</a>\
                                    <label class="message-time">'+comment.created+'</label>\
                                </div>\
                                <div class="info-line">\
                                    <label class="info-label">Post a '
                                    if (comment.danmaku_type) {
                                        if (comment.danmaku_type === 'danmaku') {
                                            cur_div += 'danmaku'
                                        } else if (comment.danmaku_type === 'advanced') {
                                            cur_div = cur_div.replace('Post a ', 'Post an ')
                                            cur_div += 'advanced danmaku'
                                        } else if (comment.danmaku_type === 'subtitles') {
                                            cur_div += 'subtitles danmaku'
                                        } else if (comment.danmaku_type === 'code') {
                                            cur_div += 'piece of code'
                                        }
                                    } else if (comment.inner_floorth) {
                                        cur_div += 'reply'
                                    } else {
                                        cur_div += 'comment'
                                    }
                                    cur_div += ' in </label>\
                                    <a class="message-title normal-link" href="'+comment.video.url+'" target="_blank">'+dt.escapeHTML(comment.video.title)+'</a>\
                                </div>\
                                <div class="info-line">\
                                    <div class="comment-content">'+dt.contentWrapper(comment.content)+'</div>\
                                </div>\
                                <div class="info-line">\
                                  <a href="'+comment.video.url+'?'
                                    if (comment.danmaku_type) {
                                        cur_div += 'timestamp='+comment.timestamp
                                    } else if (comment.inner_floorth) {
                                        cur_div += 'comment='+comment.parent_id+'&reply='+comment.id
                                    } else {
                                        cur_div += 'comment='+comment.id
                                    }
                                    cur_div += '" class="blue-link" target="_blank">[Check it out]</a>\
                                </div>\
                            </div>\
                        </div>'
                div += cur_div;
            }
        }
        return div;
    });
})
//end of the file
} (dt, jQuery));
