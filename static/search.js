(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.result-container'), function(result) {
        $('.search-result-num .commas_number').text(dt.numberWithCommas(result.total_found));
        if (result.total_found > 1) $('.search-result-num .plural').text('s');
        
        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry">\
                        <div class="video-img-uper">\
                            <a class="video-img" target="_blank" href="'+video.url+'">\
                                <img src="'+video.thumbnail_url+'">\
                                <div class="preview-time">'+dt.secondsToTime(video.duration)+'</div>\
                            </a>\
                            <div class="uper-line">\
                                <a href="'+video.uploader.space_url+'" target="_blank" class="blue-link">\
                                    <div class="uploader-avatar">\
                                        <img src="'+video.uploader.avatar_url_small+'">\
                                    </div>\
                                    <span class="video-uploader">'+video.uploader.nickname+'</span>\
                                </a>\
                            </div>\
                        </div>\
                        <div class="video-info">\
                            <div class="info-line">\
                                <div class="video-category">'+video.category+'</div>\
                                <div class="video-category-arrow"></div>\
                                <div class="video-category">'+video.subcategory+'</div>\
                                <div class="video-time">'+video.created+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a href="'+video.url+'" class="video-title normal-link">'+video.title+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="video-statistic-entry">Views: '+dt.numberWithCommas(video.hits)+'</div>\
                                <div class="video-statistic-entry">Likes: '+dt.numberWithCommas(video.likes)+'</div>\
                                <div class="video-statistic-entry">Comments: '+dt.numberWithCommas(video.comment_counter)+'</div>\
                                <div class="video-statistic-entry">Bullets: '+dt.numberWithCommas(video.bullets)+'</div>\
                            </div>\
                            <div class="info-line video-description">'+video.intro+'</div>\
                            <div class="info-line video-tags">'
                            for (var j = 0; j < video.tags.length; j++) {
                                var tag = video.tags[j];
                                div += '<a class="tag-entry" href="?keywords='+tag+'">'+tag+'</a>'
                            }
                            div += '</div>\
                        </div>\
                    </div>'
        }
        return div;
    });
});
//end of the file
} (dt, jQuery));
