(function(dt, $) {
var url = '';
var params = {};
var popup_container;

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
        for (var i = 0; i < result.playlists.length; i++) {
            var playlist = result.playlists[i];
            div += '<div class="content-entry popup" data-id="' + playlist.id +'">\
                            <div class="video-img playlist">\
                                <img src="' + playlist.thumbnail_url + '">\
                                <div class="video-num-box small">\
                                    <div class="vertical-align-relative">\
                                        <div class="video-num">'+playlist.videos_num+'</div>\
                                        <div class="video-num">Video'
                                        if (playlist.videos_num > 1) {
                                            div += 's'
                                        }
                                        if (playlist.type === 'Primary') {
                                            div += '(*)'
                                        }
                                        div += '</div>\
                                    </div>\
                                </div>\
                            </div>\
                            <div class="video-info playlist">\
                                <div class="info-line">\
                                    <div class="video-title popup">' + dt.escapeHTML(playlist.title) + '</div>\
                                </div>\
                                <div class="info-line">\
                                    <div class="list-video-time">' + playlist.modified + '</div>\
                                </div>\
                            </div>\
                        </div>'
        }

        if (div === '') {
            if ($('.content-entry.popup').length == 0) {
                div = '<div class="content-entry popup none">No results found.</div>'
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
    url = $('#search-playlist-form')[0].action;
    params = {type: 'Primary'};
    popup_container = $('.popup-playlist-container');

    $('.submitted-video-container').on('click', '.add-to', function() {
        $('.popup-window-container.add-to').addClass('show')
                                            .attr('data-id', $(this).attr('data-id'));
        if (popup_container.children().length == 0) {
            popup_container.scroll(detect_popup_scroll);
            load_more_search_result();
        }
    });

    popup_container.on('click', '.content-entry.popup', function() {
        if ($(this).hasClass('loading') || $(this).hasClass('none')) return;

        $('.content-entry.popup').removeClass('selected');
        $(this).addClass('selected');
    });

    $('.add-button').click(function(evt) {
        $('.popup-window-container.add-to').removeClass('show');
    });

    $('#search-playlist-form').submit(function() {
        params = {keywords: $('.sub-search-input.popup').val(), type: 'Primary'};
        popup_container.empty()
                        .off('scroll')
                        .scroll(detect_popup_scroll);
        dt.resetLoad(url, params);
        load_more_search_result();
        return false;
    });

    $('input.add-button').click(function(evt) {
        var entries = $('.content-entry.popup.selected');
        if (entries.length != 1) return;

        $(evt.target).prop('disabled', true);
        dt.pop_ajax_message('Adding the video to the playlist...', 'info');
        var playlist_id = entries.attr('data-id');
        var video_id = $('.popup-window-container.add-to').attr('data-id');
        var ids = [video_id];
        $.ajax({
            type: "POST",
            url: '/account/playlists/edit/'+playlist_id+'/add',
            data: {ids: ids},
            success: function(result) {
                if (!result.error) {
                    dt.pop_ajax_message('The video has been added to the playlist.', 'success');
                    $('.playlist-button.add-to[data-id='+video_id+']').removeClass('add-to')
                                                                        .addClass('remove-from')
                                                                        .text('[Remove from]')
                                                                        .attr('data-playlist-id', result.playlist.id)
                                                                        .prev().text(result.playlist.title);
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

    $('.submitted-video-container').on('click', '.remove-from', function() {
        dt.pop_ajax_message('Removing the video from the playlist...', 'info');
        var playlist_id = $(this).attr('data-playlist-id');
        var video_id = $(this).attr('data-id');
        var ids = [video_id];
        $.ajax({
            type: 'POST',
            url: '/account/playlists/edit/'+playlist_id+'/delete',
            data: {ids: ids},
            success: function(result) {
                if (!result.error) {
                    dt.pop_ajax_message('The video has been removed from the playlist.', 'success');
                    $('.playlist-button.remove-from[data-id='+video_id+']').removeClass('remove-from')
                                                                            .addClass('add-to')
                                                                            .text('[Add to]')
                                                                            .attr('data-playlist-id', '')
                                                                            .prev().text('Not listed');
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).prop('disabled', false);
            }
        });
    });

    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.submitted-video-container'), function(result) {
        if (result.total_found !== undefined) {
            $('#sub-title .commas_number').text(dt.numberWithCommas(result.total_found));
            if (result.total_found > 1) $('#sub-title .plural').text('s');
        }

        var div = '';
        for (var i = 0; i < result.videos.length; i++) {
            var video = result.videos[i];
            div += '<div class="content-entry '+video.id+'">\
                        <a class="video-img" href="'+video.url+'" target="_blank">\
                            <img src="'+video.thumbnail_url+'">\
                            <div class="preview-time">'+dt.secondsToTime(video.duration)+'</div>\
                        </a>\
                        <div class="video-info">\
                            <div class="info-line">\
                                <div class="video-category">'+video.category+'</div>\
                                <div class="video-category-arrow"></div>\
                                <div class="video-category">'+video.subcategory+'</div>\
                                <div class="video-time">'+video.created+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a href="'+video.url+'" class="video-title normal-link" target="_blank">'+dt.escapeHTML(video.title)+'</a>\
                            </div>\
                            <div class="info-line">\
                                <label class="video-list-belonged">Primary list: </label>'
                                if (video.playlist) {
                                    div += '<a class="video-list-belonged normal-link" href="/account/playlists/edit/'+video.playlist.id+'">'+dt.escapeHTML(video.playlist.title)+'</a><a class="blue-link playlist-button remove-from" data-id="'+video.id+'" data-playlist-id="'+video.playlist.id+'">[Remove from]</a>';
                                } else {
                                    div += '<label class="video-list-belonged">Not listed</label><a class="blue-link playlist-button add-to" data-id="'+video.id+'">[Add to]</a>';
                                }
                            div += '</div>\
                            <div class="info-line">\
                                <div class="video-statistic-entry">Views: '+dt.numberWithCommas(video.hits)+'</div>\
                                <div class="video-statistic-entry">Likes: '+dt.numberWithCommas(video.likes)+'</div>\
                                <div class="video-statistic-entry">Comments: '+dt.numberWithCommas(video.comment_counter)+'</div>\
                                <div class="video-statistic-entry">Bullets: '+dt.numberWithCommas(video.bullets)+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a href="/account/video/edit/'+video.id+'" class="blue-link edit-button">[Edit Video]</a>\
                                <a href="/account/video/parts/'+video.id+'" class="blue-link edit-button">[Manage Danmaku]</a>\
                            </div>\
                        </div>\
                        <div class="single-checkbox" data-id="'+video.id+'" data-title="'+video.title+'"></div>\
                    </div>'
        }
        return div;
    });
});
// end of the file
} (dt, jQuery))