$(document).ready(function() {
    $('div.delete-button').click(function(evt) {
        if ($(evt.target).hasClass('delete')) {
            var ids= $(evt.target).attr('data-id').split(';');
            $(evt.target).text('Deleting');
            $.ajax({
                type: "POST",
                url: '/account/video/delete',
                async: false,
                data: {ids: ids},
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        pop_ajax_message('Videos deleted!', 'success');
                        ids = result.message;
                        for (var i = 0; i < ids.length; i++) {
                            $('div.video-entry.dt'+ids[i]).remove();
                        }
                    } else {
                        pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                }
            });
        }
        $('div.delete-confirm-container').removeClass('show');
    });

    $('#action-select div.option-entry.delete').click(function() {
        var checked_boxes = $('div.video-select-checkbox.checked');
        if (checked_boxes.length != 0) {
            $('div.delete-confirm-container').addClass('show');
            $('div.delete-target-name').remove();
            var ids = $(checked_boxes[0]).attr('data-id');
            var title = $(checked_boxes[0]).attr('data-title');
            $('div.delete-buttons-line').before('<div class="delete-target-name">'+title+'</div>');
            for (var i = 1; i < checked_boxes.length; i++) {
                ids += ';'+ $(checked_boxes[i]).attr('data-id');
                title = $(checked_boxes[i]).attr('data-title');
                $('div.delete-buttons-line').before('<div class="delete-target-name">'+title+'</div>');
            }
            $('div.delete-button.delete').attr('data-id', ids);
        }
    });

    $('div.submitted-video-container').on('click', 'div.video-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });
});
