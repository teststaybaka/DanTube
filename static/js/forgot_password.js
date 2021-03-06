(function(dt, $) {
$(document).ready(function() {
    $('#forgotpasswordform').submit(function(evt) {
        var button = document.querySelector('#forgotpasswordform input[type="submit"]');
        button.disabled = true;
        
        $.ajax({
            type: "POST",
            url: "/password/forgot",
            data: $('#forgotpasswordform').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    dt.pop_ajax_message('An email has been sent to reset your password.', 'success');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                }
                $('#signin_up-header').removeClass('loading');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));
