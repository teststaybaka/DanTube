$(document).ready(function() {
    $('#signupform input[name="nickname"]').focusout(function(evt) {
        var nickname = evt.target.value;
        if (!nickname) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Your nickname is the name that will be seen by others.');
            $(evt.target).addClass('error');
        } else if (nickname.indexOf(' ') != -1) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Nickname can\'t contain any space.');
            $(evt.target).addClass('error');
        } else if (nickname.length > 30) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Nickname can\'t exceed 30 letters long.');
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
            $('#password-error span').text('Password must be something other than all spaces.');
            $(evt.target).addClass('error');
        } else if (password.length < 6) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password must contain at least 6 letters.');
            $(evt.target).addClass('error');
        } else if (password.length > 40) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password can\'t exceed 40 letters.');
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
            $('#password-error span').text('Password must be something other than all spaces.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        } else if (password.length < 6){
            $('#password-error').addClass('show');
            $('#password-error span').text('Password must contain at least 6 letters.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        }  else if (password.length > 40) {
            $('#password-error').addClass('show');
            $('#password-error span').text('Password can\'t exceed 40 letters.');
            $('#signupform input[name="password"]').addClass('error');
            error = true;
        }

        var nickname = $('#signupform input[name="nickname"]')[0].value;
        if (!nickname) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Your nickname is the name that will be seen by others.');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        } else if (nickname.indexOf(' ') != -1) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Nickname can\'t contain any space.');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        } else if (nickname.length > 30) {
            $('#nickname-error').addClass('show');
            $('#nickname-error span').text('Nickname can\'t exceed 30 letters long.');
            $('#signupform input[name="nickname"]').addClass('error');
            error = true;
        }

        if (error) {
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/signup",
            data: $('#signupform').serialize(),
            success: function(result) {
                console.log(result);
                if(result === 'success') {
                    $('#signup-success').addClass('show');
                    $('#signup-fail').removeClass('show');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    $('#signup-success').removeClass('show');
                    $('#signup-fail').addClass('show');
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
