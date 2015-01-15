$(document).ready(function() {
    $('#submitform').submit(function() {
        var video_url = $('#submitform input[name="video-url"]')[0].value.trim();
        if(!video_url) {
            $('#submitform div.form-error').html('<p>video url must not be empty!</p>')
            return false;
        }
        $.ajax({
            type: "POST",
            url: "/video",
            data: $('#submitform').serialize(),
            success: function(result) {
                console.log(result);
                if(result.error) {
                    $('#submitform div.form-error').html('<p>' + result.error + '</p>');
                } else {
                    $('#submitform div.form-error').html('<p>Submit successfully! <a href="' + result.url + '">video link</a></p>');
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
        return false;
    });  
});
