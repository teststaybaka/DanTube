(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.liked-videos-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry">\
                        <a class="video-img" href="'+video.url+'" target="_blank">\
                            <img class="video-img" src="'+video.thumbnail_url+'">\
                            <div class="preview-time">'+dt.secondsToTime(video.duration)+'</div>\
                        </a>\
                        <div class="video-info">\
                            <div class="video-info-line">\
                                <a href="'+video.url+'" class="normal-link" target="_blank">'+dt.escapeHTML(video.title)+'</a>\
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
                            <div class="video-info-line last-viewed">Liked at: '+video.liked+'</div>\
                        </div>\
                        <div class="unlike-button" data-id="'+video.id+'"></div>\
                    </div>'
        }
        return div;
    });

    $('.liked-videos-container').on('click', '.unlike-button', function() {
        var button = $(this);
        var video_id = button.attr('data-id');
        $.ajax({
            type: 'POST',
            url: '/video/unlike/'+video_id,
            success: function(result) {
                if(!result.error) {
                    button.parent().remove();
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });
})
//end of the file
} (dt, jQuery));
