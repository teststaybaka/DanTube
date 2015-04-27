function cur_password_check(cur_pw) {
    if (!cur_pw) {
        $('#cur-password-error').addClass('show');
        $('#cur-password-error').text('Please enter your password.');
        $("#cur-password").addClass('error');
        return false;
    } else {
        $('#cur-password-error').removeClass('show');
        $("#cur-password").removeClass('error');
        return true;
    }
}

function new_password_check(new_pw) {
    if (!new_pw) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Please enter a new password.');
        $("#new-password").addClass('error');
        return false;
    } else if (!new_pw.trim()) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Password can\'t be all spaces.');
        $("#new-password").addClass('error');
        return false;
    } else if (new_pw.length < 6) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Password must contain at least 6 characters.');
        $("#new-password").addClass('error');
        return false;
    } else if (new_pw.length > 40) {
        $('#new-password-error').addClass('show');
        $('#new-password-error').text('Password can\'t exceed 40 characters.');
        $("#new-password").addClass('error');
        return false;
    } else {
        $('#new-password-error').removeClass('show');
        $("#new-password").removeClass('error');
        return true;
    }
}

function confirm_password_check(confirm_pw) {
    var new_pw = $("#new-password")[0].value;
    if (confirm_pw != new_pw) {
        $('#confirm-password-error').addClass('show');
        $('#confirm-password-error').text('Password doesn\'t match.');
        $("#confirm-password").addClass('error');
        return false;
    } else {
        $('#confirm-password-error').removeClass('show');
        $("#confirm-password").removeClass('error');
        return true;
    }
}

function self_intro_check(ori_intro) {
    var intro = $('#self-intro-change').val();
    if (intro.length > 2000) {
        $('#self-intro-error').addClass('show');
        $('#self-intro-error').text('Your intro can\'t exceed 2000 characters.');
        $("#self-intro-change").addClass('error');
        return false;
    } else {
        $('#self-intro-error').removeClass('show');
        $("#self-intro-change").removeClass('error');
        return true;
    }
}

$(document).ready(function() {
    $('#resend-email-link').click(function(evt) {
        if ($(evt.target).hasClass('send')) return;
        $(evt.target).addClass('send');
        $(evt.target).text('Sending...');

        $.ajax({
            type: "POST",
            url: "/verify",
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    pop_ajax_message('Please check your email to activate your account.', 'success');
                    $(evt.target).text('An email has been sent.');
                } else {
                    pop_ajax_message(result.message, 'error');
                    $(evt.target).text(result.message);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).text('Resend email');
                $(evt.target).removeClass('send');
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });

    $('div.statistic-entry span').each(function() {
        // var colors = [[163,163,163], [83,187,83], [39,143,250], [208,51,208], [255,138,34]]
        var count = parseInt($(this).text());
        $(this).text(numberWithCommas(count));
        if (count == 0) count = 1;
        var color = [220 - Math.log(count)/Math.log(100000000)*220, 9*10, 65];
        $(this).css('color', 'hsl('+color[0]+','+color[1]+'%,'+color[2]+ '%)');
    });

    $("#cur-password").focusout(function(evt) {
        var cur_pw = evt.target.value;
        cur_password_check(cur_pw);
    });

    $("#new-password").focusout(function(evt) {
        var new_pw = evt.target.value;
        new_password_check(new_pw);
    });

    $("#confirm-password").focusout(function(evt) {
        var confirm_pw = evt.target.value;
        confirm_password_check(confirm_pw);
    });

    $('#change-password-form').submit(function(evt) {
        $('#change-applying').addClass('show');

        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        var cur_pw = $("#cur-password")[0].value;
        var new_pw = $("#new-password")[0].value;
        var confirm_pw = $("#confirm-password")[0].value;

        var error = false;
        if (!cur_password_check(cur_pw)) {
            error = true;
        }
        if (!new_password_check(new_pw)) {
            error = true;
        }
        if (!confirm_password_check(confirm_pw)) {
            error = true;
        }
        if (error) {
            $('#change-applying').removeClass('show');
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/account/password",
            data: [{name: 'cur_password', value: cur_pw}, {name: 'new_password', value: new_pw}],
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    pop_ajax_message('Change applied successfully!', 'success');
                    setTimeout(function(){
                        window.location.replace('/account'); 
                    }, 3000);
                } else {
                    pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                }
                $('#change-applying').removeClass('show');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').removeClass('show');
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
    
    var cur_intro = $('#self-intro-change').val();
    $('#self-intro-change').focusout(function(evt) {
        self_intro_check(cur_intro);
    });

    var cur_nickname = $('#nickname-change').val();
    $('#nickname-change').focusout(function(evt) {
        var nickname = evt.target.value.trim();
        var puncts = /[@.,?!;:/\\"']/;
        if (!nickname || puncts.test(nickname)) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Your nickname can\'t contain: @ . , ? ! ; : / \\ \" \'');
            $(evt.target).addClass('error');
        } else if (nickname.length > 50) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Nickname can\'t exceed 50 characters long.');
            $(evt.target).addClass('error');
        } else if (nickname == cur_nickname) {
            $('#change-nickname-error').removeClass('show');
            $(evt.target).removeClass('error');
        } else {
            $.ajax({
                type: "POST",
                url: "/nickname_check",
                data: {nickname: nickname},
                success: function(result) {
                    console.log(result);
                    if (result === 'valid') {
                        $('#change-nickname-error').removeClass('show');
                        $(evt.target).removeClass('error');
                    } else {
                        $('#change-nickname-error').addClass('show');
                        $('#change-nickname-error').text('Someone has used this name.');
                        $(evt.target).addClass('error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                }
            });
        }
    });

    $('#change-info-form').submit(function(evt) {
        $('#change-applying').addClass('show');

        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        var nickname = $('#nickname-change')[0].value.trim();
        var puncts = /[@.,?!;:/\\"']/;

        var error = false;
        if (!nickname || puncts.test(nickname)) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Your nickname can\'t contain: @ . , ? ! ; : / \\ \" \'');
            $('#nickname-change').addClass('error');
            error = true;
        } else if (nickname.length > 50) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Nickname can\'t exceed 50 characters long.');
            $('#nickname-change').addClass('error');
            error = true;
        } else {
            $('#change-nickname-error').removeClass('show');
            $('#nickname-change').removeClass('error');
        }

        if (!self_intro_check(cur_intro)) {
            error = true;
        }

        if (error) {
            $('#change-applying').removeClass('show');
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/account/info",
            data: $('#change-info-form').serialize(),
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    pop_ajax_message('Change applied successfully!', 'success');
                    setTimeout(function(){
                        window.location.replace('/account'); 
                    }, 3000);
                } else {
                    pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                }
                $('#change-applying').removeClass('show');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').removeClass('show');
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});