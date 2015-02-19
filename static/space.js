$(document).ready(function() {
    $('div.emoticons-select').click(function(evt) {
        if ($('div.emoticons-select').hasClass('show')) {
            $('div.emoticons-select').removeClass('show');
        } else {
            $('div.emoticons-select').addClass('show')
        }
    });

    $('div.emoticons-option').click(function(evt) {
        var textarea = document.getElementById('write-text');
        textarea.value += $(evt.target).text();
    });
});