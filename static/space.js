(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('#space-list-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry">\
                        <a class="video-img" href="'+video.url+'" target="_blank">\
                            <img src="'+video.thumbnail_url+'">\
                            <div class="preview-time">'+dt.secondsToTime(video.duration)+'</div>\
                        </a>\
                        <div class="video-info">\
                            <div class="info-line">\
                                <div class="video-category">'+video.category+'</div>\
                                <span class="video-category-arrow"></span>\
                                <div class="video-category">'+video.subcategory+'</div>\
                                <div class="video-time">'+video.created+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a class="video-title normal-link" href="'+video.url+'" target="_blank">'+video.title+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="video-statistic-entry">Views: '+dt.numberWithCommas(video.hits)+'</div>\
                                <div class="video-statistic-entry">Likes: '+dt.numberWithCommas(video.likes)+'</div>\
                                <div class="video-statistic-entry">Comments: '+dt.numberWithCommas(video.comment_counter)+'</div>\
                                <div class="video-statistic-entry">Bullets: '+dt.numberWithCommas(video.bullets)+'</div>\
                            </div>\
                            <div class="video-intro info-line">'+video.intro+'</div>\
                        </div>\
                    </div>'
        }
        return div;
    })
});
//end of the file
} (dt, jQuery));
