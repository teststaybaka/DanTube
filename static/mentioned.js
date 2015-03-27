$(document).ready(function() {
    var isLoading = false;
    var isOver = false;
    var cursor = '';

    $(window).scroll(function() {
        if(($(window).scrollTop() >= $(document).height() - $(window).height()) && !isLoading && !isOver) {
            update_mentioned_message(cursor);
        }
    });
    update_mentioned_message(cursor);

    function update_mentioned_message() {
        isLoading = true;
        $('.messages-container').append('<div class="message-entry loading"></div>');
        $.ajax({
            type: "POST",
            url: '/account/mentioned?cursor='+cursor,
            success: function(result) {
                $('.message-entry.loading').remove();
                if(!result.error) {
                    for (var i = 0; i < result.comments.length; i++) {
                        comment = result.comments[i];
                        var div = render_comment_div(comment);
                        $('.messages-container').append(div);
                    }
                    if (result.comments.length == 0) {
                        isOver = true;
                        if (!cursor) {
                            $('.messages-container').append('<div class="message-entry none"> No messages found. </div>');
                        }
                    } else {
                        cursor = result.cursor;
                    }
                } else {
                    pop_ajax_message(result.message, 'error');
                }
                isLoading = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                isLoading = false;
                $('.message-entry.loading').remove();
                console.log(xhr.status);
                console.log(thrownError);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    }
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
                <label>Mentioned you in </label>\
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
    } else {
        div += 'index=' + comment.clip_index + '&timestamp=' + comment.timestamp;
    }
    div += '" target="_blank">[Check it out]</a>\
            </div>\
        </div>\
    </div>'
    return div;
}
