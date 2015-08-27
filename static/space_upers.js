(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('#space-list-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.upers.length; i++) {
            var uper = result.upers[i];
            div += '<div class="content-entry uper">\
                        <a class="uper-img" href="'+uper.space_url+'">\
                            <img src="'+uper.avatar_url_small+'">\
                        </a>\
                        <div class="uper-info">\
                            <div class="info-line">\
                                <a class="uploader-link blue-link" href="'+uper.space_url+'">'+uper.nickname+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="uper-detail-info">Subscribers: '+dt.numberWithCommas(uper.subscribers_counter)+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a class="inline-button uper" href="/account/messages/compose?to='+uper.nickname+'">Send Message</a>\
                                <div class="inline-button uper subscribe-button '
                                if (uper.subscribed) {
                                    div += 'unsubscribe'
                                }
                                div += '" data-id="'+uper.id+'"><span class="subscribe-icon"></span><span class="subscribe-text">'
                                if (uper.subscribed) {
                                    div += 'Subscribed'
                                } else {
                                    div += 'Subscribe'
                                }
                                div += '</span></div>\
                            </div>\
                        </div>\
                    </div>'
        }
        return div;
    })
});
//end of the file
} (dt, jQuery));
