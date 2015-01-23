$(document).ready(function() {
    $('#signinform').submit(function(evt) {
        // evt.preventDefault();
        $('#signin-header').addClass('loading');

        var button = document.querySelector('#signinform input[type="submit"]');
        button.disabled = true;

        $.ajax({
            type: "POST",
            url: "/signin",
            data: $('#signinform').serialize(),
            success: function(result) {
                console.log(result);
                if(result === 'success') {
                    $('#signin-message').remove();
                    $('#signin-header').after('<div id="signin-message" class="success">Sign in successfully! Redirecting to home page in 3 seconds...</div>');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    $('#signin-message').remove();
                    $('#signin-header').after('<div id="signin-message" class="fail">Sign in failed! <br> Email and password doesn\'t match.</div>');
                    button.disabled = false;
                }
                $('#signin-header').removeClass('loading');
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
