$(document).ready(function() {
    $('#signinform').submit(function(evt) {
        // evt.preventDefault();
        $('#signin_up-header').addClass('loading');
        $('#signin-message').remove();

        var button = document.querySelector('#signinform input[type="submit"]');
        button.disabled = true;

        $.ajax({
            type: "POST",
            url: "/signin",
            data: $('#signinform').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    $('#signinform').prepend('<div id="signin-message" class="success">Sign in successfully! Redirecting to home page in 3 seconds...</div>');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    $('#signinform').prepend('<div id="signin-message" class="fail">'+result.message+'</div>');
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
