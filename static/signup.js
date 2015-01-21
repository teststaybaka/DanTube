$(document).ready(function() {
    $('#signupform input[name="nickname"]').focusout(function(evt) {
        var nickname = evt.target.value;
        if (!nickname) {
            $('#nickname-invalid').removeClass('show');
            $('#nickname-required').addClass('show');
            $('#nickname-used').removeClass('show');
            $(evt.target).addClass('error');
        } else if (nickname.indexOf(' ') != -1) {
            $('#nickname-invalid').addClass('show');
            $('#nickname-required').removeClass('show');
            $('#nickname-used').removeClass('show');
            $(evt.target).addClass('error');
        } else {
            $.ajax({
                type: "POST",
                url: "/nickname_check",
                data: {nickname: nickname},
                success: function(result) {
                    console.log(result);
                    if (result === 'valid') {
                        $('#nickname-invalid').removeClass('show');
                        $('#nickname-used').removeClass('show');
                        $('#nickname-required').removeClass('show');
                        $(evt.target).removeClass('error');
                    } else {
                        $('#nickname-invalid').removeClass('show');
                        $('#nickname-required').removeClass('show');
                        $('#nickname-used').addClass('show');
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
            $('#password-invalid').addClass('show');
            $(evt.target).addClass('error');
        } else {
            $('#password-invalid').removeClass('show');
            $(evt.target).removeClass('error');
        }
    })

    $('#signupform input[name="email"]').focusout(function(evt) {
        var email = evt.target.value.trim();
        var email_re = /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
        if (!email || !email_re.test(email)) {
            $('#email-invalid').addClass('show');
            $('#email-used').removeClass('show');
            $(evt.target).addClass('error');
        } else {
            $.ajax({
                type: "POST",
                url: "/email_check",
                data: {email: email},
                success: function(result) {
                    console.log(result);
                    if (result === 'valid') {
                        $('#email-used').removeClass('show');
                        $('#email-invalid').removeClass('show');
                        $(evt.target).removeClass('error');
                    } else {
                        $('#email-invalid').removeClass('show');
                        $('#email-used').addClass('show');
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

    $('#signupform').submit(function() {
        var email = $('#signupform input[name="email"]')[0].value.trim();
        if(!email) {
            $('#signupform div.form-error').html('<p>email must not be empty!</p>')
            return false;
        }

        var username = $('#signupform input[name="username"]')[0].value.trim();
        if(!username) {
            $('#signupform div.form-error').html('<p>username must not be empty!</p>')
            return false;
        }
        if(username.length < 8) {
            $('#signupform div.form-error').html('<p>username must have at least 8 characters!</p>')
            return false;
        }
        if(username.length > 20) {
            $('#signupform div.form-error').html('<p>username can not exceed 20 characters!</p>')
            return false;
        }
        var username_re = /^[a-z|A-Z|0-9|\-|_]*$/;
        if(!username_re.test(username)) {
            $('#signupform div.form-error').html('<p>username can only contain a-z, A-Z, 0-9, underline and dash!</p>')
            return false;
        }

        var password = $('#signupform input[name="password"]')[0].value;
        if(!password.trim()) {
            $('#signupform div.form-error').html('<p>password must not be empty!</p>')
            return false;
        }
        if(password.length < 8) {
            $('#signupform div.form-error').html('<p>password must have at least 8 characters!</p>')
            return false;
        }
        var password_confirm = $('#signupform input[name="password-confirm"]')[0].value;
        if(password != password_confirm) {
            $('#signupform div.form-error').html('<p>password confirmation does not match!</p>')
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/signup",
            data: $('#signupform').serialize(),
            success: function(result) {
                console.log(result);
                if(result.error) {
                    $('#signupform div.form-error').html('<p>' + result.error + '</p>');
                } else {
                    $('#signupform div.form-error').html('<p>Signup successfully! An email has been sent to you to activate your account. Redirecting to home page in 5 seconds...</p>');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 5000);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
        return false;
    });
});
