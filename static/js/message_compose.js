(function(dt, $) {
function check_receiver() {
    if (!$('input[name=receiver]').val()) {
        $('input[name=receiver]').addClass('error')
                                .next().addClass('show')
                                        .text('Receiver cannot be empty.');
        return false;
    } else {
        $('input[name=receiver]').removeClass('error')
                                .next().removeClass('show');
        return true;
    }
}

function check_subject() {
    if (!$('input[name=subject').val()) {
        $('input[name=subject]').addClass('error')
                                .next().addClass('show')
                                        .text('Subject cannot be empty.');
        return false;
    } else if ($('input[name=subject]').val().length > 400) {
        $('input[name=subject]').addClass('error')
                                .next().addClass('show')
                                        .text('Subject is too long.');
        return false;
    } else {
        $('input[name=subject]').removeClass('error')
                                .next().removeClass('show');
        return true;
    }
}

function check_content() {
    if (!$('textarea[name=content]').val().trim()) {
        $('textarea[name=content]').addClass('error')
                                .next().addClass('show')
                                        .text('Content cannot be empty.');
        return false;
    } else if ($('textarea[name=content]').val().length > 2000) {
        $('textarea[name=content]').addClass('error')
                                .next().addClass('show')
                                        .text('Content is too long.');
        return false;
    } else {
        $('textarea[name=content]').removeClass('error')
                                .next().removeClass('show');
        return true;
    }
}

$(document).ready(function() {
    var target = dt.getParameterByName('to');
    if (target) {
        $('input[name=receiver]').val(target);
    }
    $('input[name=receiver]').focusout(check_receiver);
    $('input[name=subject]').focusout(check_subject);
    $('textarea[name=content]').focusout(check_content);

    $('#new-topic-form').submit(function(evt) {
        var button = document.getElementById('submit-message-button');
        button.disabled = true;

        if (!check_receiver() | !check_subject() | !check_content()) {
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: document.URL,
            data: $(this).serialize(),
            success: function(result) {
                if(result.error) {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                } else {
                    dt.pop_ajax_message('Message sent!', 'success');
                    setTimeout(function(){
                        window.location.replace('/account/messages'); 
                    }, 3000);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                button.disabled = false;
            }
        });
        return false;
    });
});
//end of the file
} (dt, jQuery));
