$(document).ready(function() {
    var old_nickname = $('#basicsform input[name="nickname"]').val();
    var old_intro = $('#basicsform textarea[name="intro"]').val();

    $('#basicsform').submit(function(e) {
        e.preventDefault();
        var nickname = $('#basicsform input[name="nickname"]').val();
        var intro = $('#basicsform textarea[name="intro"]').val();
        if( nickname != old_nickname || intro != old_intro) {
            $.ajax({
                type: "POST",
                url: "/settings/basics",
                data: $('#basicsform').serialize(),
                success: function(result) {
                    console.log(result);
                    if(result.error) {
                        alert(result.message);
                    } else {
                        alert('success');
                        old_nickname = result.nickname;
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    button.disabled = false;
                }
            });
        }
        return false;
    });

    $('#basicsform input[name="nickname"]').focusout(function(evt) {
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
        } else if (nickname == old_nickname) {
            console.log('no change to nickname');
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
});