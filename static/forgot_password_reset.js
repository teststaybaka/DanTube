(function(dt, $) {
    function new_password_check() {
    var new_pw = $("#new-password").val();
    var confirm_pw = $('#confirm-password').val();

    var no_error = true;
    if (!new_pw) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Please enter a new password.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else if (!new_pw.trim()) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Password can\'t be all spaces.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else if (new_pw.length < 6) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Password must contain at least 6 characters.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else if (new_pw.length > 40) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Password can\'t exceed 40 characters.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else {
        $('#new-password-error').removeClass('show');
        $("#new-password").removeClass('error');
        no_error &= true;
    }

    if (confirm_pw != new_pw) {
        $('#confirm-password-error').addClass('show');
        $('#confirm-password-error').text('Password doesn\'t match.');
        $("#confirm-password").addClass('error');
        no_error &= false;
    } else {
        $('#confirm-password-error').removeClass('show');
        $("#confirm-password").removeClass('error');
        no_error &= true;
    }
    return no_error;
}

$(document).ready(function() {
    $("#new-password").focusout(new_password_check);
    $("#confirm-password").focusout(new_password_check);

    $('#resetpasswordform').submit(function(evt) {
        var button = document.querySelector('#resetpasswordform input[type="submit"]');
        button.disabled = true;

        if (!new_password_check()) {
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: window.location,
            data: $('#resetpasswordform').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    dt.pop_ajax_message('Password has been reset. Please sign in with the new password.', 'success');
                    setTimeout(function(){
                        window.location.replace('/signin'); 
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                }
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
