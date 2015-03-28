$(document).ready(function() {
    $('#action-select div.option-entry.delete').click(function() {
        var checked_boxes = $('div.message-select-checkbox.checked');
        if (checked_boxes.length != 0) {
            var ids = [];
            for (var i = 0; i < checked_boxes.length; i++) {
                ids.push($(checked_boxes[i]).attr('data-id'));
            }
            $.ajax({
                type: "POST",
                url: '/account/notifications/delete',
                data: {ids: ids},
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        ids = result.message;
                        for (var i = 0; i < ids.length; i++) {
                            $('.message-entry[data-id="'+ids[i]+'"]').remove();
                        }
                    } else {
                        pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    pop_ajax_message(xhr.status+' '+thrownError, 'error');
                }
            });
        }
    });

    $('.messages-container').on('click', 'div.message-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });

    $('.messages-container').on('click', 'a.notification-title', function() {
        var message_entry = $(this).parent().parent().parent();
        if (message_entry.hasClass('unread')) {
            $.ajax({
                type: "POST",
                url: '/account/notifications/read?id='+message_entry.attr('data-id'),
                success: function(result) {
                    if(!result.error) {
                        message_entry.removeClass('unread');
                    } else {
                        pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    pop_ajax_message(xhr.status+' '+thrownError, 'error');
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
    })

    var isLoading = false;
    var isOver = false;
    var cursor = '';

    $(window).scroll(function() {
        if(($(window).scrollTop() >= $(document).height() - $(window).height()) && !isLoading && !isOver) {
            update_notifications(cursor);
        }
    });
    update_notifications(cursor);

    function update_notifications() {
        isLoading = true;
        $('.messages-container').append('<div class="message-entry loading"></div>');
        $.ajax({
            type: "POST",
            url: '/account/notifications?cursor='+cursor,
            success: function(result) {
                $('.message-entry.loading').remove();
                if(!result.error) {
                    for (var i = 0; i < result.notifications.length; i++) {
                        var div = render_notification_div(result.notifications[i]);
                        $('.messages-container').append(div);
                    }
                    if (result.notifications.length == 0 && !cursor) {
                        $('.messages-container').append('<div class="message-entry none"> No notifications found.</div>');
                    }
                    if (result.notifications.length < 20) {
                        isOver = true;
                    }
                    cursor = result.cursor;
                } else {
                    pop_ajax_message(result.message, 'error');
                }
                isLoading = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                isLoading = false;
                $('.message-entry.loading').remove();
                console.log(xhr.status);
                console.log(thrownError);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    }
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
            <div class="message-select-checkbox" data-id="' + notification.id + '"></div>\
            <div class="notification-detail">' + notification.content + '</div>\
        </div>\
    </div>'
    return div;
}
