$(document).ready(function() {
    $('.send-button').click(function() {
        $.ajax({
            type: "POST",
            url: document.URL,
            data: $('#new-topic-form').serialize(),
            success: function(result) {
                if(result.error)
                    console.log(result.message);
                else
                    alert('success!')
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });
});
