(function(dt, $) {
$(document).ready(function() {
    $('#message-contain-body').scrollTop($('#message-contain-body')[0].scrollHeight);

    var user_avatar_url = $('#self-img').attr('src');
    $('#reply-form').submit(function() {
        var button = document.getElementById('reply-message-send');
        button.disabled = true;

        var error = false;
        if (!$('#send-message').val().trim()) {
            dt.pop_ajax_message('Content cannot be empty', 'error');
            error = true;
        } else if ($('#send-message').val().trim().length > 2000) {
            dt.pop_ajax_message('Content is too long.', 'error');
            error = true;
        }

        if (error) {
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: window.location.href,
            data: $(this).serialize(),
            success: function(result) {
                if(result.error) {
                    dt.pop_ajax_message(result.message, 'error');
                } else {
                    $('#send-message').val('');
                    $('#message-contain-body').append(
                        '<div class="message-detail-entry container">' + 
                            '<div class="message-date send">' + result.when + '</div>' +
                            '<a class="user-img send"><img src="' + user_avatar_url + '"></a>' + 
                            '<div class="message-content send">' + result.content + '</div>' +
                        '</div>');
                    $('#message-contain-body').scrollTop($('#message-contain-body')[0].scrollHeight);
                }
                button.disabled = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                button.disabled = false;
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));
