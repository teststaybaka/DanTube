(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.result-container'), function(result) {
        $('.search-result-num .commas_number').text(dt.numberWithCommas(result.total_found));
        if (result.total_found > 1) $('.search-result-num .plural').text('s');

        var div = '';
        for (var i = 0; i < result.upers.length; i++) {
            var uper = result.upers[i];
            div += '<div class="content-entry">\
                        <a class="uper-img" href="'+uper.space_url+'">\
                            <img src="'+uper.avatar_url+'">\
                        </a>\
                        <div class="uper-info">\
                            <div class="info-line">\
                                <a class="uploader-name blue-link" href="'+uper.space_url+'">'+uper.nickname+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="uper-detail-info">Views: '+dt.numberWithCommas(uper.videos_watched)+'</div>\
                                <div class="uper-detail-info">Videos: '+dt.numberWithCommas(uper.videos_submitted)+'</div>\
                                <div class="uper-detail-info">Subscribers: '+dt.numberWithCommas(uper.subscribers_counter)+'</div>\
                            </div>\
                            <div class="info-line uper-description">'
                            if (uper.intro) {
                                div += dt.escapeHTML(uper.intro)
                            }
                            div += '</div>\
                            <div class="info-line uper-buttons">\
                                <a class="inline-button upers-button" href="/account/messages/compose?to='+uper.nickname+'">Send Message</a>\
                                <div class="inline-button upers-button subscribe-button '
                                if (uper.subscribed) {
                                    div += 'unsubscribe'
                                }
                                div += '" data-id="'+uper.id+'">\
                                    <span class="subscribe-icon"></span>\
                                    <span class="subscribe-text">'
                                    if (uper.subscribed) {
                                        div += 'Subscribed'
                                    } else {
                                        div += 'Subscribe'
                                    }
                                    div += '</span>\
                                </div>\
                            </div>\
                        </div>\
                    </div>'
        }
        return div;
    });
});
//end of the file
} (dt, jQuery));
