(function(dt, $) {
$(document).ready(function() {
    $('.messages-container').on('click', 'a.notification-title', function() {
        var message_entry = $(this).parent().parent().parent();
        if (message_entry.hasClass('unread')) {
            message_entry.removeClass('unread');
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
