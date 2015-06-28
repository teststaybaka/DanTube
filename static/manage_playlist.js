(function(dt, $) {
$(document).ready(function() {
    $('#playlist-create-button').click(function() {
        $('#playlist-create-dropdown').addClass('show');
    });

    $('div.create-button').click(function() {
        $('#playlist-create-dropdown').removeClass('show');
    });

    $('#playlist-create-button-box').submit(function(evt) {
        $("input.create-button").prop('disabled', true);

        var error = false;
        var title = $('#playlist-title-input').val().trim();
        if (!title) {
            dt.pop_ajax_message('Title can not be empty.', 'error');
            $('#playlist-title-input').addClass('error');
            error = true;
        } else if (title.length > 400) {
            dt.pop_ajax_message('Title can not be longer than 400 characters.', 'error');
            $('#playlist-title-input').addClass('error');
            error = true;
        } else {
            $('#playlist-title-input').removeClass('error');
        }

        var intro = $('#playlist-intro-input').val().trim();
        if (intro.length > 2000) {
            dt.pop_ajax_message('Introduction can not be longer than 2000 characters.', 'error');
            $('#playlist-intro-input').addClass('error');
            error = true;
        } else {
            $('#playlist-intro-input').removeClass('error');
        }

        if (error) {
            $("input.create-button").prop('disabled', false);
            return false;
        }

        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: $(evt.target).serialize(),
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    dt.pop_ajax_message('A new playlist is created!', 'success');
                    $('#playlist-create-dropdown').removeClass('show');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    $("input.create-button").prop('disabled', false);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $("input.create-button").prop('disabled', false);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));