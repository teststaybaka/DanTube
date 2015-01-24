$(document).ready(function() {
    $('#portrait').mouseover(function() {
        $('#user-box').addClass('show');
        $('#user-box').removeClass('hide');
        clearTimeout(window.user_box_hide);
        clearTimeout(window.user_box_clear);
    });
    $('#portrait').mouseout(function() {
        window.user_box_hide = setTimeout(function() {
            $('#user-box').addClass('hide');
            window.user_box_clear = setTimeout(function() {
                $('#user-box').removeClass('show');
            }, 200);
        }, 100);
    });
});