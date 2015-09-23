(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.notifications-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.entries.length; i++) {
            var note = result.entries[i];
            div += '<div class="content-entry '
                    if (note.read) { 
                        div += 'read'
                    }
                    div += ' '+note.id+'">\
                        <div class="notification-type '+note.type+'"></div>\
                        <div class="message-info">\
                            <div class="info-line">\
                                <a class="notification-title normal-link" data-id="'+note.id+'">'+note.title+'</a>\
                            </div>\
                            <div class="info-line">\
                                <label>'+note.created+'</label>\
                            </div>\
                            <div class="notification-detail">'+dt.escapeHTML(note.content)+'</div>\
                        </div>\
                        <div class="single-checkbox" data-id="'+note.id+'" data-title="'+note.title+'"></div>\
                    </div>'
        }
        return div;
    });

    $('.notifications-container').on('click', 'a.notification-title', function() {
        var message_entry = $(this).parent().parent().parent();
        if (!message_entry.hasClass('read')) {
            message_entry.addClass('read');
            $.ajax({
                type: "POST",
                url: '/account/notifications/read',
                data: {id: $(this).attr('data-id')},
                success: function(result) {
                    if(result.error) {
                        dt.pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                }
            });
        }

        var content = $(this).parent().siblings('div.notification-detail');
        if (content.hasClass('show')) {
            content.height(0);
            content.removeClass('show');
        } else {
            content.height(content[0].scrollHeight);
            content.addClass('show');
        }
    });
});
//end of the file
} (dt, jQuery));
