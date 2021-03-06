(function(dt, $) {
$(document).ready(function() {
    $('#signupform input[name="nickname"]').focusout(function(evt) {
        var nickname = evt.target.value.trim();
        if (!nickname) {
            $('#nickname-error').addClass('show');
            $('#nickname-error').text('Your nickname can\'t be empty');
            $(evt.target).addClass('error');
        } else if (dt.puncts.test(nickname)) {
            $('#nickname-error').addClass('show');
            $('#nickname-error').text('Your nickname can\'t contain: & @ . , ? ! : / \\ \" \' < > =');
            $(evt.target).addClass('error');
        } else if (nickname.length > 50) {
            $('#nickname-error').addClass('show');
            $('#nickname-error').text('Nickname can\'t exceed 50 characters.');
            $(evt.target).addClass('error');
        } else {
            $.ajax({
                type: "POST",
                url: "/nickname_check",
                data: {nickname: nickname},
                success: function(result) {
                    console.log(result);
                    if (result === 'valid') {
                        $('#nickname-error').removeClass('show');
                        $(evt.target).removeClass('error');
                    } else {
                        $('#nickname-error').addClass('show');
                        $('#nickname-error').text('Someone has used this name.');
                        $(evt.target).addClass('error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                }
            });
        }
    })

    $('#signupform input[name="password"]').focusout(function(evt) {
        var password = evt.target.value;
        if (!password) {
            $('#password-error').addClass('show');
            $('#password-error').text('Please enter a password.');
            $(evt.target).addClass('error');
        } else if (!password.trim()) {
            $('#password-error').addClass('show');
            $('#password-error').text('Password can\'t be all spaces.');
            $(evt.target).addClass('error');
        } else if (password.length < 6) {
            $('#password-error').addClass('show');
            $('#password-error').text('Password must contain at least 6 characters.');
            $(evt.target).addClass('error');
        } else if (password.length > 40) {
            $('#password-error').addClass('show');
            $('#password-error').text('Password can\'t exceed 40 characters.');
            $(evt.target).addClass('error');
        } else {
            $('#password-error').removeClass('show');
            $(evt.target).removeClass('error');
        }
    })

    $('#signupform input[name="email"]').focusout(function(evt) {
        var email = evt.target.value.trim();
        if (!email || !dt.email_format.test(email)) {
            $('#email-error').addClass('show');
            $('#email-error').text('Email address invalid.');
            $(evt.target).addClass('error');
        } else {
            $.ajax({
                type: "POST",
                url: "/email_check",
                data: {email: email},
                success: function(result) {
                    console.log(result);
                    if (result === 'valid') {
                        $('#email-error').removeClass('show');
                        $(evt.target).removeClass('error');
                    } else {
                        $('#email-error').addClass('show');
                        $('#email-error').text('Email addres has been used.');
                        $(evt.target).addClass('error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                }
            });
        }
    })

    $('#signupform').submit(function(evt) {
        // evt.preventDefault();
        $('#signup-header').addClass('loading');
        
        var button = document.querySelector('#signupform input[type="submit"]');
        button.disabled = true;

        var error = false;
        var email = $('#signupform input[name="email"]')[0].value.trim();
        if (!email || !dt.email_format.test(email)) {
            $('#email-error').addClass('show');
            $('#email-error').text('Email address invalid.');
            $('#signupform input[name="email"]').addClass('error');
            error = true;
        }

        var password = $('#signupform input[name="password"]')[0].value;
        if (!password) {
            $('#password-error').addClass('show');
            $('#password-error').text('Please enter a password.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        } else if (!password.trim()) {
            $('#password-error').addClass('show');
            $('#password-error').text('Password can\'t be all spaces.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        } else if (password.length < 6){
            $('#password-error').addClass('show');
            $('#password-error').text('Password must contain at least 6 characters.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        }  else if (password.length > 40) {
            $('#password-error').addClass('show');
            $('#password-error').text('Password can\'t exceed 40 characters.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        }

        var nickname = $('#signupform input[name="nickname"]')[0].value.trim();
        if (!nickname) {
            $('#nickname-error').addClass('show');
            $('#nickname-error').text('Your nickname can\'t be empty');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        } else if (dt.puncts.test(nickname)) {
            $('#nickname-error').addClass('show');
            $('#nickname-error').text('Your nickname can\'t contain: & @ . , ? ! : / \\ \" \' < > =');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        } else if (nickname.length > 50) {
            $('#nickname-error').addClass('show');
            $('#nickname-error').text('Nickname can\'t exceed 50 characters.');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        }

        if (error) {
            button.disabled = false;
            $('#signin_up-header').removeClass('loading');
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/signup",
            data: $('#signupform').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    dt.pop_ajax_message('Sign up successfully! Please check your email to activate your account.', 'success');
                    setTimeout(function() {
                        window.location.replace('/');
                    }, 5000);
                } else {
                    // $('#signupform').prepend('<div id="signup-message" class="fail">Sign up failed.</div>');
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
