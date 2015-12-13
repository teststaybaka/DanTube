(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.messages-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.entries.length; i++) {
            var comment = result.entries[i];
            div += '<div class="content-entry">\
                <a href="' + comment.creator.space_url + '" target="_blank" class="user-img">\
                    <img src="' + comment.creator.avatar_url_small + '">\
                </a>\
                <div class="message-info">\
                    <div class="info-line">\
                        <a href="' + comment.creator.space_url + '" target="_blank" class="blue-link">' + comment.creator.nickname + '</a>\
                        <label class="time">' + comment.created + '</label>\
                    </div>\
                    <div class="info-line">\
                        <label>Mentioned you in a '
                        if (comment.danmaku_type) {
                            div += 'danmaku'
                        } else if (comment.inner_floorth) {
                            div += 'reply'
                        } else {
                            div += 'comment'
                        }
                        div += ' in</label>\
                        <a class="normal-link" href="' + comment.video.url + '" target="_blank">' + dt.escapeHTML(comment.video.title) + '</a>\
                    </div>\
                    <div class="info-line">\
                        <div class="comment-content">' + dt.contentWrapper(comment.content) + '</div>\
                    </div>\
                    <div class="info-line">\
                        <a class="blue-link" href="'+comment.video.url+'?'
                        if (comment.danmaku_type) {
                            div += 'timestamp='+comment.timestamp
                        } else if (comment.inner_floorth) {
                            div += 'comment='+comment.parent_id+'&reply='+comment.id
                        } else {
                            div += 'comment='+comment.id
                        }
                        div += '" target="_blank">[Check it out]</a>\
                    </div>\
                </div>\
            </div>'
        }
        return div;
    });
});
//end of the file
} (dt, jQuery));
