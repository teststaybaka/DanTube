$(document).ready(function() {
    var message_show = document.getElementById('message-contain-body');
    if (message_show != null) {
        message_show.scrollTop = message_show.scrollHeight;
    }
    
    $('div.emoticons-select').click(function(evt) {
        if ($('div.emoticons-select').hasClass('show')) {
            $('div.emoticons-select').removeClass('show');
        } else {
            $('div.emoticons-select').addClass('show')
        }
    });

    $('div.emoticons-option').click(function(evt) {
        var textarea = document.getElementById('send-message');
        textarea.value += $(evt.target).text();
    });
});