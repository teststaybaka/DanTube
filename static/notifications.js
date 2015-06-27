(function(dt, $) {
$(document).ready(function() {
    $('#action-select div.option-entry.delete').click(function() {
        dt.delete_entries('/account/notifications/delete');
    });
    $('.messages-container').on('click', 'div.single-checkbox', function(evt) {
        $(this).toggleClass('checked');
    });

    $('.messages-container').on('click', 'a.notification-title', function() {
        var message_entry = $(this).parent().parent().parent();
        if (message_entry.hasClass('unread')) {
            $.ajax({
                type: "POST",
                url: '/account/notifications/read',
                data: {id: message_entry.attr('data-id')},
                success: function(result) {
                    if(!result.error) {
                        message_entry.removeClass('unread');
                    } else {
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

    dt.scrollUpdateMessage('/account/notifications', render_notification_div);
});

function render_notification_div(notification) {
    var div = '<div class="message-entry '
    if (!notification.read) {
        div += 'unread'
    }
    div += '" data-id="' + notification.id + '">\
        <div class="notification-type ' + notification.type + '"></div>\
        <div class="message-info">\
            <div class="info-line">\
                <a class="message-title notification-title">' + notification.title + '</a>\
            </div>\
            <div class="info-line">\
                <label>' + notification.created + '</label>\
            </div>\
            <div class="notification-detail">' + notification.content + '</div>\
        </div>\
        <div class="single-checkbox" data-id="' + notification.id + '"></div>\
    </div>'
    return div;
}
//end of the file
} (dt, jQuery));
