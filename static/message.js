(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.messages-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.entries.length; i++) {
            var thread = result.entries[i];
            div += '<div class="content-entry '+thread.id+' ';
                    if (!thread.unread) {
                        div += 'read'
                    } 
                    div += '">\
                        <a href="'+thread.partner.space_url+'" target="_blank" class="user-img">\
                            <img src="'+thread.partner.avatar_url+'">\
                        </a>\
                        <div class="message-info">\
                            <div class="info-line">\
                                <label>About</label>\
                                <a class="normal-link" href="/account/messages/'+thread.id+'">'+thread.subject+'</a>\
                            </div>\
                            <div class="info-line">\
                                <label>With</label>\
                                <a href="'+thread.partner.space_url+'" target="_blank" class="user-name blue-link">'+thread.partner.nickname+'</a>\
                            </div>\
                            <div class="info-line">\
                                <label>'
                                if (thread.is_sender) { 
                                    div += 'You'
                                } else {
                                    div += 'He'
                                }
                                div += ' said: '+thread.last_message+'</label>\
                                <label>'+thread.updated+'</label>\
                            </div>\
                        </div>\
                        <div class="single-checkbox" data-id="'+thread.id+'" data-title="'+thread.subject+'"></div>\
                    </div>'
        }
        return div;
    });
});
// end of the file
} (dt, jQuery))
