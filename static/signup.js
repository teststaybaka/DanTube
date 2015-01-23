$(document).ready(function() {
    $('#signupform input[name="nickname"]').focusout(function(evt) {
        var nickname = evt.target.value.trim();
        var puncts = /[@.,?!;:/\\"']/;
        if (!nickname || puncts.test(nickname)) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Your nickname can\'t contain: @ . , ? ! ; : / \\ \" \'');
            $(evt.target).addClass('error');
        } else if (nickname.length > 30) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Nickname can\'t exceed 30 characters long.');
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
                        $('#nickname-error span').text('Someone has used this name.');
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
            $('#password-error span').text('Please enter a password.');
            $(evt.target).addClass('error');
        } else if (!password.trim()) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password can\'t be all spaces.');
            $(evt.target).addClass('error');
        } else if (password.length < 6) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password must contain at least 6 characters.');
            $(evt.target).addClass('error');
        } else if (password.length > 40) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password can\'t exceed 40 characters.');
            $(evt.target).addClass('error');
        } else {
            $('#password-error').removeClass('show');
            $(evt.target).removeClass('error');
        }
    })

    $('#signupform input[name="email"]').focusout(function(evt) {
        var email = evt.target.value.trim();
        var email_re = /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
        if (!email || !email_re.test(email)) {
            $('#email-error').addClass('show');
            $('#email-error span').text('Email address invalid.');
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
                        $('#email-error span').text('Email addres has been used.');
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
        var email_re = /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
        if (!email || !email_re.test(email)) {
            $('#email-error').addClass('show');
            $('#email-error span').text('Email address invalid.');
            $('#signupform input[name="email"]').addClass('error');
            error = true;
        }

        var password = $('#signupform input[name="password"]')[0].value;
        if (!password) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Please enter a password.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        } else if (!password.trim()) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password can\'t be all spaces.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        } else if (password.length < 6){
            $('#password-error').addClass('show');
            $('#password-error span').text('Password must contain at least 6 characters.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        }  else if (password.length > 40) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password can\'t exceed 40 characters.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        }

        var nickname = $('#signupform input[name="nickname"]')[0].value.trim();
        var puncts = /[@.,?!;:/\\"']/;
        if (!nickname || puncts.test(nickname)) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Your nickname can\'t contain: @ . , ? ! ; : / \\ \" \'');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        } else if (nickname.length > 30) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Nickname can\'t exceed 30 characters long.');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        }

        if (error) {
            button.disabled = false;
            $('#signup-header').removeClass('loading');
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/signup",
            data: $('#signupform').serialize(),
            success: function(result) {
                console.log(result);
                if(result === 'success') {
                    $('#signup-message').remove();
                    $('#signup-header').after('<div id="signup-message" class="success">Sign up successfully! An email has been sent to you to activate your account. Redirecting to home page in 3 seconds...</div>');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    $('#signup-message').remove();
                    $('#signup-header').after('<div id="signup-message" class="fail">Sign up failed for some reason.</div>');
                    button.disabled = false;
                }
                $('#signup-header').removeClass('loading');
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
