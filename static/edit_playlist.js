(function(dt, $) {
var url = '';
var params = {};
var popup_container;
var ids = [];

function detect_popup_scroll() {
    if (popup_container.children('.content-entry:last-child').offset().top - popup_container.offset().top < popup_container.height()) {
        load_more_search_result()
    }
}

function load_more_search_result() {
    dt.loadNextPage(url, params, function() {
        popup_container.append('<div class="content-entry popup loading"></div>');
    }, function(result, isOver) {
        popup_container.children('.content-entry.popup.loading').remove();

        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry popup'
                            if (video.belonged) {
                                div += ' belonged'
                            }
                            div += '" data-id="' + video.id +'">\
                            <img class="video-img playlist" src="' + video.thumbnail_url + '">\
                            <div class="video-info playlist">\
                                <div class="info-line">\
                                    <div class="video-title popup">' + dt.escapeHTML(video.title) + '</div>\
                                </div>\
                                <div class="info-line">\
                                    <div class="list-video-time">' + video.created + '</div>\
                                </div>\
                            </div>\
                        </div>'
        }

        if (div === '') {
            if ($('.content-entry.popup').length == 0) {
                div = '<div class="content-entry none">No results found.</div>'
            }
        }
        popup_container.append(div);

        if (isOver) popup_container.off('scroll');
        else detect_popup_scroll();
    }, function() {
        popup_container.children('.content-entry.popup.loading').remove();
    });
}

$(document).ready(function() {
    var playlist_type = $('#playlist-type').val();
    url = $('#search-video-form')[0].action;
    params = {type: playlist_type};
    popup_container = $('.popup-video-container');

    $('#add-videos-button').click(function(evt) {
        $('.popup-window-container.add-to').addClass('show');
        if (popup_container.children().length == 0) {
            popup_container.scroll(detect_popup_scroll);
            load_more_search_result();
        }
    });

    popup_container.on('click', 'div.content-entry.popup', function() {
        if ($(this).hasClass('belonged') || $(this).hasClass('loading')) return;
        
        if ($(this).hasClass('selected')) {
            $(this).removeClass('selected');
            var index = ids.indexOf($(this).attr('data-id'));
            ids.splice(index, 1);
        } else {
            $(this).addClass('selected');
            ids.push($(this).attr('data-id'));
        }
    });

    $('.add-button').click(function(evt) {
        $('.popup-window-container.add-to').removeClass('show');
    });

    $('#search-video-form').submit(function() {
        params = {keywords: $('.sub-search-input').val(), type: playlist_type};
        popup_container.empty()
                        .off('scroll')
                        .scroll(detect_popup_scroll);
        dt.resetLoad(url, params);
        load_more_search_result();
        return false;
    });

    $('input.add-button').click(function(evt) {
        if (ids.length == 0) return;

        $(evt.target).prop('disabled', true);
        dt.pop_ajax_message('Adding videos to the playlist...', 'info');
        $.ajax({
            type: "POST",
            url: window.location.pathname+'/add',
            data: {ids: ids},
            success: function(result) {
                if (!result.error) {
                    dt.pop_ajax_message('Videos have been added to the playlist.', 'success');
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    $(evt.target).prop('disabled', false);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).prop('disabled', false);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });

    dt.scrollUpdate(window.location.href, {type: playlist_type}, 'content-entry', $('.edit-playlists-container'), function(result) {
        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry list '+video.id+'">\
                        <div class="list-No">'+video.index+'</div>\
                        <a class="video-img playlist" href="'+video.url+'" target="_blank">\
                            <img src="'+video.thumbnail_url+'">\
                        </a>\
                        <div class="video-info playlist">\
                            <div class="info-line">\
                                <a class="video-title normal-link" href="'+video.url+'" target="_blank">'+dt.escapeHTML(video.title)+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="list-video-time">'+video.created+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a class="blue-link edit-button move-to">[Move to]</a>\
                                <input type="text" class="normal-input move-to-input" placeholder="1-'+result.videos_num+'">\
                            </div>\
                        </div>\
                        <div class="single-checkbox" data-id="'+video.id+'" data-title="'+video.title+'"></div>\
                    </div>'
        }
        return div;
    });

    $('div.edit-title-button').click(function(evt) {
        $('#sub-title').addClass('hidden');
        $('#playlist-title-change-form').removeClass('hidden');
        $('#playlist-title-change').focus();
    });

    $('div.create-button').click(function() {
        $('#playlist-title-change-form').addClass('hidden');
        $('#sub-title').removeClass('hidden');
    });

    $('#playlist-title-change-form').submit(function(evt) {
        $("input.create-button").prop('disabled', true);

        var error = false;
        var title = $('#playlist-title-change').val();
        if (!title) {
            dt.pop_ajax_message('Title can not be empty.', 'error');
            $('#playlist-title-change').addClass('error');
            error = true;
        } else if (title.length > 400) {
            dt.pop_ajax_message('Title can not be longer than 400 characters.', 'error');
            $('#playlist-title-change').addClass('error');
            error = true;
        } else {
            $('#playlist-title-change').removeClass('error');
        }

        var intro = $('#playlist-intro-change').val();
        if (intro.length > 2000) {
            dt.pop_ajax_message('Introduction can not be longer than 2000 characters.', 'error');
            $('#playlist-intro-change').addClass('error');
            error = true;
        } else {
            $('#playlist-intro-change').removeClass('error');
        }

        if (error) {
            $("input.create-button").prop('disabled', false);
            return false;
        }

        dt.pop_ajax_message('Updating...', 'info');
        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: $(evt.target).serialize(),
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    dt.pop_ajax_message('Playlist updated!', 'success');
                    $('#playlist-title-change-form').addClass('hidden');
                    $('#sub-title').removeClass('hidden');
                    $('#sub-title a.sub-title-link').text(title);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
                $("input.create-button").prop('disabled', false);
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

    $('.edit-playlists-container').on('click', 'a.move-to', function() {
        var target = $(this).next();
        target.addClass('show');
        target.focus();
    });

    $('.edit-playlists-container').on('focusout', "input.move-to-input", function(evt) {
        $(this).removeClass('show');
    });

    $('.edit-playlists-container').on('keyup', "input.move-to-input", function(evt) {
        if(evt.originalEvent.keyCode == 13) {
            if (!$(this).val()) {
                $(this).removeClass('show');
                return;
            }

            var ori_idx = $(this).parent().parent().siblings('.list-No').text();
            var target_idx = $(this).val();
            dt.pop_ajax_message('Moving...', 'info');
            $.ajax({
                type: "POST",
                url: window.location.pathname+'/move',
                data: {ori_idx: ori_idx, target_idx: target_idx},
                success: function(result) {
                    if (!result.error) {
                        // swapNodes($('.content-entry.list')[ori_idx - 1], $('.content-entry.list')[target_idx - 1]);
                        dt.pop_ajax_message('Moved!', 'success');
                    } else {
                        dt.pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                }
            });
            $(this).val('');
            $(this).removeClass('show');
        } else if (evt.originalEvent.keyCode == 27) {
            $(this).val('');
            $(this).removeClass('show');
        }
    });
});

// http://stackoverflow.com/questions/698301/is-there-a-native-jquery-function-to-switch-elements
function swapNodes(a, b) {
    var aparent = a.parentNode;
    var asibling = a.nextSibling === b ? a : a.nextSibling;
    b.parentNode.insertBefore(a, b);
    aparent.insertBefore(b, asibling);
}
//end of the file
} (dt, jQuery));
