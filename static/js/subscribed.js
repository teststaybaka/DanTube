(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'subscription-user-box', $('#subs-user-list'), function(result) {
        var div = '';
        for (var i = 0; i < result.upers.length; i++) {
            var uper = result.upers[i];
            div += '<div class="subscription-user-box">\
                        <a class="user-img" href="'+uper.space_url+'" target="_blank">\
                            <img src="'+uper.avatar_url+'" title="'+uper.nickname+'">\
                        </a>\
                        <div class="user-details">\
                            <div>\
                                <a class="user-nickname blue-link" href="'+uper.space_url+'" target="_blank" title="'+uper.nickname+'">'+uper.nickname+'</a>\
                            </div>\
                            <div class="subscriber-number">Subscribers: '+dt.numberWithCommas(uper.subscribers_counter)+'</div>\
                            <a class="inline-button subscribed" href="/account/messages/compose?to='+uper.nickname+'">Send Message</a>\
                            <div class="inline-button subscribed subscribe-button unsubscribe" data-id="'+uper.id+'"><span class="subscribe-icon"></span><span class="subscribe-text">Subscribed</span></div>\
                        </div>\
                    </div>'
        }
        return div;
    });
});
}(dt, jQuery));