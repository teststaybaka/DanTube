$(document).ready(function() {
    $('input.delete-button').click(function(evt) {
        var ids= $(evt.target).attr('data-id').split(';');
        pop_ajax_message('Deleting...', 'info');
        $(evt.target).prop('disabled', true);
        $.ajax({
            type: "POST",
            url: '/account/playlists/delete',
            data: {ids: ids},
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    pop_ajax_message('Playlists deleted!', 'success');
                    ids = result.message;
                    for (var i = 0; i < ids.length; i++) {
                        $('div.video-entry.'+ids[i]).remove();
                    }
                } else {
                    pop_ajax_message(result.message, 'error');
                }
                $(evt.target).prop('disabled', false);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).prop('disabled', false);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        $('div.popup-window-container').removeClass('show');
    });

    $('div.delete-button').click(function(evt) {
        $('div.popup-window-container').removeClass('show');
    });

    $('#action-select div.option-entry.delete').click(function() {
        var checked_boxes = $('div.video-select-checkbox.checked');
        if (checked_boxes.length != 0) {
            $('div.popup-window-container').addClass('show');
            $('div.delete-target-name').remove();
            var ids = $(checked_boxes[0]).attr('data-id');
            var title = $(checked_boxes[0]).attr('data-title');
            $('div.delete-buttons-line').before('<div class="delete-target-name">'+title+'</div>');
            for (var i = 1; i < checked_boxes.length; i++) {
                ids += ';'+ $(checked_boxes[i]).attr('data-id');
                title = $(checked_boxes[i]).attr('data-title');
                $('div.delete-buttons-line').before('<div class="delete-target-name">'+title+'</div>');
            }
            $('input.delete-button').attr('data-id', ids);
        }
    });

    $('div.manage-playlists-container').on('click', 'div.video-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });

    $('#playlist-create-button').click(function() {
        $('#playlist-create-dropdown').addClass('show');
    });

    $('div.create-button').click(function() {
        $('#playlist-create-dropdown').removeClass('show');
    });

    $('#playlist-create-button-box').submit(function(evt) {
        $("input.create-button").prop('disabled', true);

        var error = false;
        var title = $('#playlist-title-input').val();
        if (!title) {
            pop_ajax_message('Title can not be empty.', 'error');
            $('#playlist-title-input').addClass('error');
            error = true;
        } else if (title.length > 100) {
            pop_ajax_message('Title can not be longer than 100 characters.', 'error');
            $('#playlist-title-input').addClass('error');
            error = true;
        } else {
            $('#playlist-title-input').removeClass('error');
        }

        var intro = $('#playlist-intro-input').val();
        if (intro.length > 100) {
            pop_ajax_message('Introduction can not be longer than 2000 characters.', 'error');
            $('#playlist-intro-input').addClass('error');
            error = true;
        } else {
            $('#playlist-intro-input').removeClass('error');
        }

        if (error) {
            $("input.create-button").prop('disabled', false);
            return false;
        }

        pop_ajax_message('Creating new playlist...', 'info');
        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: $(evt.target).serialize(),
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    pop_ajax_message('A new playlist is created!', 'success');
                    $('#playlist-create-dropdown').removeClass('show');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                } else {
                    pop_ajax_message(result.message, 'error');
                    $("input.create-button").prop('disabled', false);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $("input.create-button").prop('disabled', false);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});
