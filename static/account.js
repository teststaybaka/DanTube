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

$(document).ready(function() {
    var urls = window.location.href.split('/');
    if (urls[urls.length-1] === "account") {
        $("#sub-overview").addClass("active");
        $("#account-top-title").text("Overview");
    } else if (urls[urls.length-1] === "password") {
        $("#sub-change-password").addClass("active");
        $("#account-top-title").text("Change Password");
    } else if (urls[urls.length-1] === "avatar") {
        $("#sub-change-avatar").addClass("active");
        $("#account-top-title").text("Change Avatar");
    } else if (urls[urls.length-1] === "nickname") {
        $("#sub-change-nickname").addClass("active");
        $("#account-top-title").text("Change Nickname");
    } else if (urls[urls.length-1] === "video") {
        $("#sub-videos").addClass("active");
        $("#account-top-title").text("Your videos");
    } else if (urls[urls.length-1] === "submit") {
        $("#sub-submit").addClass("active");
        $("#account-top-title").text("Video Submission");
    }

    $('#resend-email-link').click(function(evt) {
        if ($(evt.target).hasClass('send')) return;
        $(evt.target).addClass('send');
        $(evt.target).text('Sending');

        $.ajax({
            type: "POST",
            url: "/verify",
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    $(evt.target).text('An email has been sent.');
                } else {
                    $(evt.target).text(result.message);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).text('Resend email');
                $(evt.target).removeClass('send');
            }
        });
    });

    $('.statistic-entry span').each(function() {
        // var colors = [[163,163,163], [83,187,83], [39,143,250], [208,51,208], [255,138,34]]
        var count = parseInt($(this).text());
        $(this).text(numberWithCommas(count));
        if (count == 0) count = 1;
        var color = [220 - Math.log(count)/Math.log(100000000)*220, 9/10, 65/100];
        if (color[0] < 0) color[0] = 0;
        color = hsl2rgb(color);
        $(this).css('color', 'rgb('+color[0]+','+color[1]+','+color[2]+ ')');
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
        $('#save-change-message').remove();

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
                    $('input.save_change-button').after('<div id="save-change-message" class="success show">Change applied successfully!</div>');
                    setTimeout(function(){
                        window.location.replace('/account'); 
                    }, 1500);
                } else {
                    $('input.save_change-button').after('<div id="save-change-message" class="fail show">'+result.message+'</div>');
                    button.disabled = false;
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
            }
        });
        return false;
    });
    
    var cur_nickname = $('#nickname-change').val();
    $('#nickname-change').focusout(function(evt) {
        var nickname = evt.target.value.trim();
        var puncts = /[@.,?!;:/\\"']/;
        if (!nickname || puncts.test(nickname)) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Your nickname can\'t contain: @ . , ? ! ; : / \\ \" \'');
            $(evt.target).addClass('error');
        } else if (nickname.length > 30) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Nickname can\'t exceed 30 characters long.');
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

    $('#change-nickname-form').submit(function(evt) {
        $('#save-change-message').remove();

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
        } else if (nickname.length > 30) {
            $('#change-nickname-error').addClass('show');
            $('#change-nickname-error').text('Nickname can\'t exceed 30 characters long.');
            $('#nickname-change').addClass('error');
            error = true;
        } else if (nickname == cur_nickname) {
            $('#change-nickname-error').removeClass('show');
            $('#nickname-change').removeClass('error');

            $('input.save_change-button').after('<div id="save-change-message" class="fail show">Already applied!</div>');
            error = true;
        }

        if (error) {
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/account/nickname",
            data: {nickname: nickname},
            success: function(result) {
                console.log(result);
                if(!result.error) {
                    cur_nickname = nickname;
                    $('input.save_change-button').after('<div id="save-change-message" class="success show">Change applied successfully!</div>');
                    setTimeout(function(){
                        window.location.replace('/account'); 
                    }, 1500);
                } else {
                    $('input.save_change-button').after('<div id="save-change-message" class="fail show">'+result.message+'</div>');
                    button.disabled = false;
                }
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