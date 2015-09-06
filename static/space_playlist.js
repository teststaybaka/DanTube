(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('#space-list-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.playlists.length; i++) {
            var playlist = result.playlists[i];
            div += '<div class="content-entry">\
                        <a class="video-img"'
                        if (playlist.url) {
                            div += 'href="'+playlist.url+'"'
                        }
                        div += ' target="_blank">\
                            <img class="video-img" src="'+playlist.thumbnail_url+'">\
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
                        <div class="video-info">\
                            <div class="info-line">\
                                <a '
                                if (playlist.url) {
                                    div += 'href="'+playlist.url+'"'
                                }
                                div += ' class="video-title normal-link" target="_blank">'+playlist.title+'</a>\
                            </div>\
                            <div class="info-line playlist-intro">'+dt.escapeHTML(playlist.intro)+'</div>\
                        </div>\
                    </div>'
        }
        return div;
    })
});
//end of the file
} (dt, jQuery));
