$(document).ready(function() {
    $('#signinform').submit(function() {
        var username = $('#signinform input[name="username"]')[0].value.trim();
        if(!username) {
            $('#signinform div.form-error').html('<p>username must not be empty!</p>')
            return false;
        }

        var password = $('#signinform input[name="password"]')[0].value.trim();
        if(!password) {
            $('#signinform div.form-error').html('<p>password must not be empty!</p>')
            return false;
        }
        return true;
    });
});
