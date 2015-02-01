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
                    $('#signup-message').remove();
                    $('#forgotpasswordform').prepend('<div id="signup-message" class="success">An email has been sent to activate your account.</div>');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    $('#signup-message').remove();
                    $('#forgotpasswordform').prepend('<div id="signup-message" class="fail">'+result.message+'</div>');
                    button.disabled = false;
                }
                $('#signin_up-header').removeClass('loading');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
            }
        });
        return false;
    });
});