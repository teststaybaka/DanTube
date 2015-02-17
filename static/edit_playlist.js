$(document).ready(function() {
    $('div.edit-title-button').click(function(evt) {
        $('#sub-title').addClass('hide');
        $('#playlist-title-change-form').addClass('show');
        $('#playlist-title-change').val($('a.sub-title-link').text());
        $('#playlist-title-change').focus();
    });

    $('div.create-button').click(function() {
        $('#playlist-title-change-form').removeClass('show');
        $('#sub-title').removeClass('hide');
    });

    $('#playlist-title-change-form').submit(function() {
        $('#playlist-title-change-form').removeClass('show');
        $('#sub-title').removeClass('hide');

        return false;
    });

    $('div.edit-playlists-container').on('click', 'div.video-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });
});