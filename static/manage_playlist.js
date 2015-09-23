(function(dt, $) {
$(document).ready(function() {
    dt.scrollUpdate(window.location.href, {}, 'content-entry', $('.manage-playlists-container'), function(result) {
        if (result.total_found) {
            $('#sub-title .commas_number').text(dt.numberWithCommas(result.total_found));
            if (result.total_found > 1) $('#sub-title .plural').text('s');
        }

        var div = '';
        for (var i = 0; i < result.playlists.length; i++) {
            var playlist = result.playlists[i];
            div += '<div class="content-entry '+playlist.id+'">\
                        <a class="video-img" href="'+playlist.url+'" target="_blank">\
                            <img src="'+playlist.thumbnail_url+'">\
                            <div class="video-num-box">\
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
                        </a>\
                        <div class="list-info">\
                            <div class="info-line">\
                                <a class="video-title normal-link" href="'+playlist.url+'" target="_blank">'+dt.escapeHTML(playlist.title)+'</a>\
                            </div>\
                            <div class="info-line">\
                                <div class="list-intro">'+dt.escapeHTML(playlist.intro)+'</div>\
                            </div>\
                            <div class="info-line">\
                                <a class="blue-link edit-button" href="/account/playlists/edit/'+playlist.id+'">[Edit Playlist]</a>\
                            </div>\
                        </div>\
                        <div class="single-checkbox" data-id="'+playlist.id+'" data-title="'+playlist.title+'"></div>\
                    </div>'
        }
        return div;
    });

    $('#playlist-create-button').click(function() {
        $('#playlist-create-dropdown').removeClass('hidden');
    });

    $('div.create-button').click(function() {
        $('#playlist-create-dropdown').addClass('hidden');
    });

    $('#playlist-create-button-box').submit(function(evt) {
        $(".create-button.special").prop('disabled', true);

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
            $(".create-button.special").prop('disabled', false);
            return false;
        }

        dt.pop_ajax_message('Creating...', 'info');
        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: $(evt.target).serialize(),
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    dt.pop_ajax_message('A new playlist is created!', 'success');
                    $('#playlist-create-dropdown').addClass('hidden');
                    setTimeout(function(){
                        window.location.reload();
                    }, 3000);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                    $(".create-button.special").prop('disabled', false);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(".create-button.special").prop('disabled', false);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));