function user_box_show(evt) {
    $('#user-box').addClass('show');
    evt.stopPropagation();
}

$(document).click(function(evt) {
    $('#user-box').removeClass('show');
});

$(document).ready(function() {
    var portrait = document.getElementById('portrait');
    if (portrait != null) {
        portrait.addEventListener('click', user_box_show);
    }
});