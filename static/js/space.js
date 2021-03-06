(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('#space-list-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry">\
                        <a class="video-img" href="'+video.url+'" target="_blank" data-id="'+video.id+'">\
                            <img src="'+video.thumbnail_url+'">\
                            <div class="preview-time">'+dt.secondsToTime(video.duration)+'</div>\
                        </a>\
                        <div class="video-info">\
                            <div class="info-line">\
                                <a class="video-title normal-link" href="'+video.url+'" target="_blank">'+dt.escapeHTML(video.title)+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="video-statistic-entry">Views: '+dt.numberWithCommas(video.hits)+'</div>\
                                <div class="video-statistic-entry">Likes: '+dt.numberWithCommas(video.likes)+'</div>\
                                <div class="video-time">'
                                if (video.is_edited) {
                                    div += 'Edited: '
                                } else {
                                    div += 'Uploaded: '
                                }
                                div += video.created+'</div>\
                            </div>\
                            <div class="video-intro info-line">'+dt.escapeHTML(video.intro)+'</div>\
                        </div>\
                    </div>'
        }
        return div;
    }, function() {
        $('#space-list-container .page-container:last-child a.video-img').on('mouseenter', dt.watched_or_not)
                                                                        .on('mouseleave', dt.cancel_watched);
    })
});
//end of the file
} (dt, jQuery));
