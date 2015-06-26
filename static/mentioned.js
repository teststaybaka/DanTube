(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdateMessage('/account/mentioned', render_comment_div);
});

function render_comment_div(comment) {
    var div = '<div class="message-entry mentioned">\
        <a href="' + comment.sender.space_url + '" target="_blank" class="user-img">\
            <img src="' + comment.sender.avatar_url_small + '">\
        </a>\
        <div class="message-info">\
            <div class="info-line">\
                <a href="' + comment.sender.space_url + '" target="_blank" class="blue-link user-name">' + comment.sender.nickname + '</a>\
                <label class="time">' + comment.created + '</label>\
            </div>\
            <div class="info-line">\
                <label>Mentioned you in a '
    if (comment.type === 'danmaku') {
        div += 'danmaku'
    } else {
        div += 'comment'
    }
        div += ' in</label>\
                <a class="message-title" href="' + comment.video.url + '" target="_blank">' + comment.video.title + '</a>\
            </div>\
            <div class="info-line">\
                <div class="comment-content">' + comment.content + '</div>\
            </div>\
            <div class="info-line">\
                <a class="reply-link" href="' + comment.video.url + '?'
    if (comment.type === 'comment') {
        div +=  'comment=' + comment.floorth;
    } else if (comment.type === 'inner_comment') {
        div +=  'comment=' + comment.floorth + '&reply=' + comment.inner_floorth;
    } else { //danmaku
        div += 'index=' + comment.clip_index + '&timestamp=' + comment.timestamp;
    }
    div += '" target="_blank">[Check it out]</a>\
            </div>\
        </div>\
    </div>'
    return div;
}
//end of the file
} (dt, jQuery));
