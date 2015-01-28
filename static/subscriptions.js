$(document).ready(function() {
    $('.user-unsubscribe').click(function(e) {
        var user_id = $(this).attr('uid');
        var user_div = $(this).parent().parent();
        $.ajax({
            type: "POST",
            url: "/user/" + user_id + "/unsubscribe",
            success: function(result) {
                if(!result.error) {
                    alert('success!');
                    user_div.remove();
                } else {
                    alert(result.message);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    })
});