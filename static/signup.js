$(document).ready(function() {
  $('#signupform').submit(function() {
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
        var email = $('#signupform input[name="email"]')[0].value.trim();
        if(!email) {
            $('#signupform div.form-error').html('<p>email must not be empty!</p>')
            return false;
        }
        var email_re = /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
        if(!email_re.test(email)) {
            $('#signupform div.form-error').html('<p>invalid email format!</p>')
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
