$(document).ready(function() {
    $('.send-button').click(function() {
        $.ajax({
            type: "POST",
            url: document.URL,
            data: $('#new-topic-form').serialize(),
            success: function(result) {
                if(result.error)
                    pop_ajax_message(result.message, 'error');
                else {
                    pop_ajax_message('Message sent!', 'success');
                    setTimeout(function(){
                        window.location.replace('/account/messages'); 
                    }, 3000);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });
});
