$(document).ready(function() {
    $('div.unsubscribe-button').click(function(e) {
        var user_id = $(this).attr('uid');
        var user_div = $(this).parent().parent();
        $.ajax({
            type: "POST",
            url: "/user/" + user_id + "/unsubscribe",
            async: false,
            success: function(result) {
                if(!result.error) {
                    pop_ajax_message('UPer unsubscribed!', 'success');
                    user_div.remove();
                } else {
                    pop_ajax_message(result.message, 'error');
                    console.log(result.message);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });
});