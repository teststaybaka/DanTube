(function(dt, $) {
function cur_password_check() {
    var cur_pw = $('#cur-password').val();
    if (!cur_pw) {
        $('#cur-password-error').addClass('show')
                                .text('Please enter your password.');
        $("#cur-password").addClass('error');
        return false;
    } else {
        $('#cur-password-error').removeClass('show');
        $("#cur-password").removeClass('error');
        return true;
    }
}

function new_password_check() {
    var new_pw = $("#new-password").val();
    var confirm_pw = $('#confirm-password').val();
    var no_error = true;
    if (!new_pw) {
        $('#new-password-error').addClass('show')
                                .text('Please enter a new password.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else if (!new_pw.trim()) {
        $('#new-password-error').addClass('show')
                                .text('Password can\'t be all spaces.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else if (new_pw.length < 6) {
        $('#new-password-error').addClass('show')
                                .text('Password must contain at least 6 characters.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else if (new_pw.length > 40) {
        $('#new-password-error').addClass('show')
                                .text('Password can\'t exceed 40 characters.');
        $("#new-password").addClass('error');
        no_error &= false;
    } else {
        $('#new-password-error').removeClass('show');
        $("#new-password").removeClass('error');
        no_error &= true;
    }

    if (confirm_pw != new_pw) {
        $('#confirm-password-error').addClass('show')
                                    .text('Password doesn\'t match.');
        $("#confirm-password").addClass('error');
        no_error &= false;
    } else {
        $('#confirm-password-error').removeClass('show');
        $("#confirm-password").removeClass('error');
        no_error &= true;
    }
    return no_error;
}

var cur_nickname;
function nickname_check(ajax_check) {
    ajax_check = typeof ajax_check !== 'undefined' ?  ajax_check : true;

    var nickname = $('#nickname-change').val().trim();
    if (!nickname || dt.puncts.test(nickname)) {
        $('#change-nickname-error').addClass('show')
                                    .text('Your nickname can\'t contain: & @ . , ? ! : / \\ \" \' < >');
        $('#nickname-change').addClass('error');
        return false;
    } else if (nickname.length > 50) {
        $('#change-nickname-error').addClass('show')
                                    .text('Nickname can\'t exceed 50 characters long.');
        $('#nickname-change').addClass('error');
        return false;
    } else if (nickname === cur_nickname) {
        $('#change-nickname-error').removeClass('show');
        $('#nickname-change').removeClass('error');
        return true;
    } else if (ajax_check) {
        $.ajax({
            type: "POST",
            url: "/nickname_check",
            data: {nickname: nickname},
            success: function(result) {
                if (result === 'valid') {
                    $('#change-nickname-error').removeClass('show');
                    $('#nickname-change').removeClass('error');
                } else {
                    $('#change-nickname-error').addClass('show')
                                                .text('Someone has used this name.');
                    $('#nickname-change').addClass('error');
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
        return false;
    } else {
        $('#change-nickname-error').removeClass('show');
        $('#nickname-change').removeClass('error');
        return true;
    }
}

function self_intro_check() {
    var intro = $('#self-intro-change').val();
    if (intro.length > 2000) {
        $('#self-intro-error').addClass('show')
                                .text('Your intro can\'t exceed 2000 characters.');
        $("#self-intro-change").addClass('error');
        return false;
    } else {
        $('#self-intro-error').removeClass('show');
        $("#self-intro-change").removeClass('error');
        return true;
    }
}

$(document).ready(function() {
    $('div.statistic-entry span').each(function() {
        // var colors = [[163,163,163], [83,187,83], [39,143,250], [208,51,208], [255,138,34]]
        var count = parseInt($(this).text());
        $(this).text(dt.numberWithCommas(count));
        if (count == 0) count = 1;
        var color = [220 - Math.log(count)/Math.log(100000000)*220, 9*10, 65];
        $(this).css('color', 'hsl('+color[0]+','+color[1]+'%,'+color[2]+ '%)');
    });

    cur_nickname = $('#nickname-change').val();
    $('#nickname-change').focusout(nickname_check);
    $('#self-intro-change').focusout(self_intro_check);
    $("#cur-password").focusout(cur_password_check);
    $("#new-password").focusout(new_password_check);
    $("#confirm-password").focusout(new_password_check);

    $('#change-password-form').submit(function(evt) {
        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        if (!cur_password_check() | !new_password_check()) {
            button.disabled = false;
            return false;
        }

        $('#change-applying').removeClass('hidden');
        $.ajax({
            type: "POST",
            url: window.location.href,
            data: $(this).serialize(),
            success: function(result) {
                if(!result.error) {
                    dt.pop_ajax_message('Change applied successfully!', 'success');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                }
                $('#change-applying').addClass('hidden');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').addClass('hidden');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });

    $('#change-info-form').submit(function(evt) {
        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        if (!nickname_check(false) | !self_intro_check()) {
            button.disabled = false;
            return false;
        }

        $('#change-applying').removeClass('hidden');
        $.ajax({
            type: "POST",
            url: window.location.href,
            data: $(this).serialize(),
            success: function(result) {
                if(!result.error) {
                    dt.pop_ajax_message('Change applied successfully!', 'success');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                }
                $('#change-applying').addClass('hidden');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').addClass('hidden');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));
