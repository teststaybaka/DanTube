$(document).ready(function() {
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
});