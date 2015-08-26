(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.result-container'), function(result) {
        $('.search-result-num .commas_number').text(dt.numberWithCommas(result.total_found));
        if (result.total_found > 1) $('.search-result-num .plural').text('s');
        
        var div = '';
        for (var i = 0; i < result.playlists.length; i++) {
            var playlist = result.playlists[i];
            div += '<div class="content-entry">\
                        <div class="video-img-uper">\
                            <a class="video-img" '
                            if (playlist.url) {
                                div += 'href="'+playlist.url+'"'
                            }
                            div += ' target="_blank">\
                                <img src="'+playlist.thumbnail_url+'">\
                                <div class="video-num-box">\
                                    <div class="vertical-align-relative">\
                                        <div class="video-num">'+playlist.videos_num+'</div>\
                                        <div class="video-num">Video'
                                        if (playlist.videos_num > 1) {
                                            div += 's'
                                        }
                                        if (playlist.type === 'Primary') {
                                            div += '(*)'
                                        }
                                        div += '</div>\
                                    </div>\
                                </div>\
                            </a>\
                        </div>\
                        <div class="video-info">\
                            <div class="info-line">\
                                <a '
                                if (playlist.url) {
                                    div += 'href="'+playlist.url+'"'
                                }
                                div += ' class="video-title normal-link" target="_blank">'+playlist.title+'</a>\
                            </div>\
                            <div class="info-line playlist-description">'+playlist.intro+'</div>\
                        </div>\
                    </div>'
        }
        return div;
    });
});
//end of the file
} (dt, jQuery));
