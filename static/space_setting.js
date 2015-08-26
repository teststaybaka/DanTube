(function(dt, $) {
function space_name_check() {
    var space_name = $('#space-name-change').val();
    if (!space_name) {
        $('#change-space-name-error').addClass('show');
        $('#change-space-name-error').text('Please enter a name.');
        $("#space-name-change").addClass('error');
    } else if (space_name.length > 50) {
        $('#change-space-name-error').addClass('show')
                                        .text('No longer than 50 characters.');
        $("#space-name-change").addClass('error');
        return false;
    } else {
        $('#change-space-name-error').removeClass('show');
        $("#space-name-change").removeClass('error');
        return true;
    }
}

function css_file_check() {
    var file = document.getElementById("space-css-file").files[0];
    $('#space-css-change').val('');
    if (file) {
        if (file.size <= 0) {
            $('#change-space-css-error').addClass('show')
                                        .text('Invalid file.')
            $('#space-css-change').addClass('error');
            $('#space-css-file').val('');
        } else if (file.size > 1*1024*1024) {
            $('#change-space-css-error').addClass('show')
                                        .text('No larger than 1MB.');
            $('#space-css-change').addClass('error');
            $('#space-css-file').val('');
        } else {
            var types = file.type.split('/');
            // console.log(types)
            if (types[1] != 'css') {
                $('#change-space-css-error').addClass('show')
                                            .text('Please select a css file.');
                $('#space-css-change').addClass('error');
                $('#space-css-file').val('');
            } else {
                $('#change-space-css-error').removeClass('show');
                $('#space-css-change').removeClass('error');
                $('#space-css-change').val(file.name);
            }
        }
    } else {
        $('#change-space-css-error').removeClass('show');
        $('#space-css-change').removeClass('error');
    }
}

$(document).ready(function() {
    $('#user-space-url').text(window.location.host + $('#user-space-url').text());

    $('#space-name-change').focusout(space_name_check);
    $('#space-css-file').on("change", css_file_check);

    $('#space-reset').click(function() {
        $('#change-space-css-error').removeClass('show');
        $('#space-css-change').removeClass('error');
        $('#change-applying').removeClass('hidden');

        var buttons = document.querySelectorAll('input.save_change-button');
        for (var i = 0; i < buttons.length; i++) {
            buttons[i].disabled = true;
        }

        $.ajax({
            type: "POST",
            url: "/account/space_reset",
            success: function(result) {
                if(!result.error) {
                    dt.pop_ajax_message('Space settings have been reset!', 'success');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    for (var i = 0; i < buttons.length; i++) {
                        buttons[i].disabled = false;
                    }
                }
                $('#change-applying').addClass('hidden');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                for (var i = 0; i < buttons.length; i++) {
                    buttons[i].disabled = false;
                }
                $('#change-applying').addClass('hidden');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });

    $('#change-space-form').submit(function(evt) {
        $('#change-space-css-error').removeClass('show');
        $('#space-css-change').removeClass('error');

        var buttons = document.querySelectorAll('input.save_change-button');
        for (var i = 0; i < buttons.length; i++) {
            buttons[i].disabled = true;
        }

        if (!space_name_check()) {
            for (var i = 0; i < buttons.length; i++) {
                buttons[i].disabled = false;
            }
            return false;
        }

        $('#change-applying').removeClass('hidden');
        var formData = new FormData(document.getElementById('change-space-form'));
        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            success: function(result) {
                if(result.error) {
                    dt.pop_ajax_message(result.message, 'error');
                    for (var i = 0; i < buttons.length; i++) {
                        buttons[i].disabled = false;
                    }
                } else {
                    dt.pop_ajax_message('Change applied successfully!', 'success');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                }
                $('#change-applying').addClass('hidden');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                for (var i = 0; i < buttons.length; i++) {
                    buttons[i].disabled = false;
                }
                $('#change-applying').addClass('hidden');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));
