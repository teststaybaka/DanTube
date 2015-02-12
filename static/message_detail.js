$(document).ready(function() {
    var user_avatar_url = $('#self-img').attr('src');
    $('.send-button').click(function() {
        $.ajax({
            type: "POST",
            url: document.URL,
            data: $('#reply-form').serialize(),
            success: function(result) {
                if(result.error)
                    pop_ajax_message(result.message, 'error');
                else {
                    $('#send-message').val('');
                    $('#message-contain-body').append(
                        '<div class="message-detail-entry container">' + 
                            '<div class="message-date receive">' + result.when + '</div>' +
                            '<a class="user-img receive"><img src="' + user_avatar_url + '"></a>' + 
                            '<div class="message-content receive">' + result.content + '</div>' +
                        '</div>');
                    $('#message-contain-body').animate({scrollTop: $('#message-contain-body').prop("scrollHeight")}, 500);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });
});
