(function(dt, $) {
$(document).ready(function() {
    $('#signinform').submit(function(evt) {
        // evt.preventDefault();
        $('#signin_up-header').addClass('loading');
        
        var button = document.querySelector('#signinform input[type="submit"]');
        button.disabled = true;

        $.ajax({
            type: "POST",
            url: "/signin",
            data: $('#signinform').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    dt.pop_ajax_message('Sign in successfully! Redirecting to home page in 3 seconds...', 'success');
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
