(function(dt, $) {
$(document).ready(function() {
    $('#send-veri').click(function() {
        var veri_link = $(this);
        if (veri_link.hasClass('disabled')) return

        veri_link.removeClass('blue-link')
                .addClass('disabled')
                .text('Sending...');
        $.ajax({
            type: "POST",
            url: "/verify",
            data: $('#signinform').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    dt.pop_ajax_message('Verfiication email sent. Please check it to activate your account!', 'success');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                    veri_link.remove();
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    veri_link.addClass('blue-link')
                            .removeClass('disabled')
                            .text('Send verification');
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                veri_link.addClass('blue-link')
                        .removeClass('disabled')
                        .text('Send verification');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            },
        });
    });

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
                        if (document.referrer && document.referrer.indexOf(window.location.hostname) != -1
                            && document.referrer.indexOf('/signin') == -1
                            && document.referrer.indexOf('/signup') == -1
                            && document.referrer.indexOf('/password/reset') == -1) {
                            window.location.replace(document.referrer);
                        } else {
                            window.location.replace('/');
                        }
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
