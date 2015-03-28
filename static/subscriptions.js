function update_upers(page) {
    var uper_container = $('.upers-block');
    var pagination_container = uper_container.next();
    uper_container.empty();
    pagination_container.empty();
    uper_container.append('<div class="no-subscription quick loading"></div>');

    $.ajax({
        type: 'POST',
        url: '/subscription/load_upers',
        data: {page: page},
        success: function(result) {
            uper_container.empty();
            if (!result.error) {
                if(result.upers.length == 0) {
                    uper_container.append('<div class="no-subscription quick">You haven\'t subscribed to anyone.</div>');
                } else {
                    for(var i = 0; i < result.upers.length; i++) {
                        var div = render_uper_div(result.upers[i]);
                        uper_container.append(div);
                    }

                    var pagination = render_pagination(page, result.total_pages);
                    pagination_container.append(pagination);
                }
            } else {
                uper_container.empty();
                uper_container.append('<div class="no-subscription quick">Load failed.</div>');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            uper_container.empty();
            uper_container.append('<div class="no-subscription quick">Load failed.</div>');
        }
    });
}

$(document).ready(function() {
    var url = document.URL;
    var urls = url.split('?');
    var uploads = 0;
    if (urls.length > 1) {
        var index = urls[1].indexOf('uploads');
        if (index > -1 && urls[1].substr(index+8) === '1') {
            uploads = 1;
            $('.search-scope.active').removeClass('active');
            $('.search-scope:last-child').addClass('active');
        }
    }

    if ($('.upers-block').length != 0) {
        update_upers(1);
    }
    $('#subscription-upers .pagination-line').on('click', 'a', function() {
        var page = $(this).attr('data-page');
        update_upers(page);
    });

    var isLoading = false;
    var isOver = false;
    var cursor = '';

    $(window).scroll(function() {
        if(($(window).scrollTop() >= $(document).height() - $(window).height()) && !isLoading && !isOver) {
            update_activities(cursor);
        }
    });
    update_activities(cursor);

    function update_activities() {
        isLoading = true;
        $('.activity-container').append('<div class="activity-entry loading"></div>');
        $.ajax({
            type: 'POST',
            url: '/subscription/load_activities',
            data: {cursor: cursor, uploads: uploads},
            success: function(result) {
                $('.activity-entry.loading').remove();
                if(!result.error) {
                    for (var i = 0; i < result.activities.length; i++) {
                        var record = result.activities[i];
                        var div = render_activity_div(record);
                        $('.activity-container').append(div);
                    }
                    if (result.activities.length == 0 && !cursor) {
                        $('.activity-container').append('<div class="activity-entry none"> No activities found.</div>');
                    }
                    if (result.activities.length < 10) {
                        isOver = true;
                    }
                    cursor = result.cursor;
                } else {
                    pop_ajax_message(result.message, 'error');
                }
                isLoading = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                isLoading = false;
                $('.activity-entry.loading').remove();
                console.log(xhr.status);
                console.log(thrownError);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    }
});

function render_activity_div(record) {
    var div = '<div class="activity-entry">\
        <a class="uploader-img" href="' + record.creator.space_url + '" target="_blank">\
            <img class="uploader-img" src="' + record.creator.avatar_url_small + '">\
        </a>'
    if (record.type === 'upload' || record.type === 'edit') {
        div += '<div class="activity-detail">\
                <div class="activity-title">\
                    <label>'
        if (record.type === 'upload') {
            div += 'Uploaded'
        } else {//edit
            div += 'Edited'
        }
        div += '</label>\
                    <a href="' + record.video.url + '" class="activity-title" target="_blank">' + record.video.title + '</a>\
                </div>\
                <div class="uploader-name">\
                    <label>by</label>\
                    <a href="' + record.creator.space_url + '" class="uploader-name blue-link" target="_blank">' + record.creator.nickname + '</a>\
                    <div class="activity-time">' + record.created + '</div>\
                </div>\
                <div class="activity-intro">'
        if (record.type === 'upload') {
            div += record.video.description
        } else {//edit
            div += record.content
        }
         div += '</div>\
                <a class="video-img" href="' + record.video.url + '" target="_blank">\
                    <img class="video-img" src="' + record.video.thumbnail_url + '">\
                </a>\
            </div>\
        </div>'
    } else {
        div += '<div class="activity-detail">\
            <div class="activity-title">\
                <label>'
        if (record.type === 'comment') {
            div += 'Posted a comment in'
        } else if (record.type === 'inner_comment') {
            div += 'Replied a comment in'
        } else { //danmaku
            div += 'Posted a danmaku in'
        }
        div += '</label>\
                <a href="' + record.video.url + '" class="activity-title" target="_blank">' + record.video.title + '</a>\
            </div>\
            <div class="uploader-name">\
                <label>by</label>\
                <a href="' + record.creator.space_url + '" class="uploader-name blue-link" target="_blank">' + record.creator.nickname + '</a>\
                <div class="activity-time">' + record.created + '</div>\
            </div>\
            <div class="activity-intro">' + record.content + '</div>\
            <a class="comment-check blue-link" href="' + record.video.url + '?'
        if (record.type === 'comment') {
            div +=  'comment=' + record.floorth;
        } else if (record.type === 'inner_comment') {
            div +=  'comment=' + record.floorth + '&reply=' + record.inner_floorth;
        } else { //danmaku
            div += 'index=' + record.clip_index + '&timestamp=' + record.timestamp;
        }
        div += '" target="_blank">[Check it out]</a>\
        </div>'
    }
    return div;
}

function render_uper_div(uper) {
    var div = '<div class="quick-uper">\
            <a href="' + uper.space_url + '" class="user-img" title="' + uper.nickname + '" target="_blank">\
                <img src="' + uper.avatar_url_small + '">\
            </a>\
        </div>'
    return div;
}
