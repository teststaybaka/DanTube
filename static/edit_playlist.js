$(document).ready(function() {
    $('input.delete-button').click(function(evt) {
        var ids= $(evt.target).attr('data-id').split(';');
        pop_ajax_message('Deleting...', 'info');
        $(evt.target).prop('disabled', true);
        var urls = window.location.href.split('/');
        $.ajax({
            type: "POST",
            url: '/account/playlists/edit/remove/'+urls[urls.length - 1],
            data: {ids: ids},
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    pop_ajax_message('Videos removed from the list!', 'success');
                    ids = result.message;
                    for (var i = 0; i < ids.length; i++) {
                        $('div.video-entry.dt'+ids[i]).remove();
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
        $('div.popup-window-container.remove').removeClass('show');
    });

    $('div.delete-button').click(function(evt) {
        $('div.popup-window-container.remove').removeClass('show');
    });

    $('#action-select div.option-entry.delete').click(function() {
        var checked_boxes = $('div.video-select-checkbox.checked');
        if (checked_boxes.length != 0) {
            $('div.popup-window-container.remove').addClass('show');
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

    $('div.edit-playlists-container').on('click', 'div.video-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });

    $('div.edit-title-button').click(function(evt) {
        $('#sub-title').addClass('hidden');
        $('#playlist-title-change-form').addClass('show');
        $('#playlist-title-change').val($('a.sub-title-link').text());
        $('#playlist-title-change').focus();
    });

    $('div.create-button').click(function() {
        $('#playlist-title-change-form').removeClass('show');
        $('#sub-title').removeClass('hidden');
    });

    $('#playlist-title-change-form').submit(function(evt) {
        $("input.create-button").prop('disabled', true);

        var error = false;
        var title = $('#playlist-title-change').val();
        if (!title) {
            pop_ajax_message('Title can not be empty.', 'error');
            $('#playlist-title-change').addClass('error');
            error = true;
        } else if (title.length > 400) {
            pop_ajax_message('Title can not be longer than 400 characters.', 'error');
            $('#playlist-title-change').addClass('error');
            error = true;
        } else {
            $('#playlist-title-change').removeClass('error');
        }

        var intro = $('#playlist-intro-change').val();
        if (intro.length > 2000) {
            pop_ajax_message('Introduction can not be longer than 2000 characters.', 'error');
            $('#playlist-intro-change').addClass('error');
            error = true;
        } else {
            $('#playlist-intro-change').removeClass('error');
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
                    pop_ajax_message('Playlist updated!', 'success');
                    $('#playlist-title-change-form').removeClass('show');
                    $('#sub-title').removeClass('hidden');
                    $('#sub-title a.sub-title-link').text(title);
                } else {
                    pop_ajax_message(result.message, 'error');
                }
                $("input.create-button").prop('disabled', false);
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

    $('#add-videos-button').click(function(evt) {
        $('div.popup-window-container.add-to').addClass('show');
    });

    $('div.add-button').click(function(evt) {
        $('div.popup-window-container.add-to').removeClass('show');
    });

    $('input.add-button').click(function(evt) {
        var entries = $('div.video-entry.popup.selected');
        if (entries.length == 0) return;

        $(evt.target).prop('disabled', true);
        pop_ajax_message('Adding videos to playlist...', 'info');
        ids = [];
        for (var i = 0; i < entries.length; i++) {
            ids.push($(entries[i]).attr('data-id'));
        }
        var urls = window.location.href.split('/');
        $.ajax({
            type: "POST",
            url: '/account/playlists/edit/add/'+urls[urls.length - 1], 
            data: {ids: ids},
            success: function(result) {
                if (!result.error) {
                    pop_ajax_message('Videos have been added to the playlist.', 'success');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                    $('div.popup-window-container.add-to').removeClass('show');
                } else {
                    pop_ajax_message(result.message, 'error');
                    $(evt.target).prop('disabled', false);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).prop('disabled', false);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });

    $('#search-video-form').submit(function() {
        search_video(1);
        return false;
    });

    $('div.pagination-line.popup').on('click', 'a', function() {
        var page = $(this).attr('data-page');
        search_video(page);
    });

    $('div.popup-video-container').on('click', 'div.video-entry.popup', function() {
        if ($(this).hasClass('belonged')) return;
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
        } else {
            $(this).addClass('selected');
        }
    });

    $('a.move-to').click(function() {
        var target = $(this).next();
        target.addClass('show');
        target.focus();
    });

    $("input.move-to-input").focusout(function(evt) {
        $(evt.target).removeClass('show');
    });

    $("input.move-to-input").keyup(function(evt){
        if(evt.keyCode == 13){
            var ori_idx = $(evt.target).parent().parent().siblings('div.list-No').text();
            var target_idx = $(evt.target).val();
            var urls = window.location.href.split('/');
            $.ajax({
                type: "POST",
                url: '/account/playlists/edit/move/'+urls[urls.length - 1],
                data: {ori_idx: ori_idx, target_idx: target_idx},
                success: function(result) {
                    if (!result.error) {
                        window.location.reload();
                    } else {
                        pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    pop_ajax_message(xhr.status+' '+thrownError, 'error');
                }
            });
            $(evt.target).val('')
            $(evt.target).removeClass('show');
        } else if (evt.keyCode == 27) {
            $(evt.target).val('');
            $(evt.target).removeClass('show');
        }
    });
});

function search_video(page) {
    var video_container = $('div.popup-video-container');
    var pagination_container = $('div.pagination-line.popup');
    var form = document.getElementById('search-video-form');
    video_container.empty();
    pagination_container.children('a.page-change').remove();
    pagination_container.children('a.page-num').remove();
    video_container.append('<div class="video-entry loading"></div>');
    $.ajax({
        type: "POST",
        url: form.action,
        data: $(form).serialize(),
        success: function(result) {
            video_container.empty();
            if (!result.error) {
                if(result.videos.length == 0) {
                    video_container.append('<div class="video-entry none">No videos found.</div>');
                } else {
                    for(var i = 0; i < result.videos.length; i++) {
                        var video_div;
                        video_div = render_popup_video_div(result.videos[i]);
                        video_container.append(video_div);
                    }

                    var pagination = render_pagination(page, result.total_pages);
                    pagination_container.append(pagination);
                }
            } else {
                console.log(result.message);
                video_container.append('<div class="video-entry none">Search error.</div>');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            video_container.empty();
            video_container.append('<div class="video-entry none">Load error.</div>');
        }
    });
    return false;
}

function render_popup_video_div(video) {
    belonged = ''
    if (video.belonged) {
        belonged = 'belonged'
    }
    var div = '<div class="video-entry popup ' + belonged + '" data-id="' + video.id_num +'">\
                    <img class="list-video-img" src="' + video.thumbnail_url + '">\
                    <div class="video-info playlist">\
                        <div class="video-title popup">' + video.title + '</div>\
                        <div class="list-video-time">' + video.created + '</div>\
                    </div>\
                </div>'

    return div;
}
