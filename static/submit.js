$(document).ready(function() {
    $('#category').change(function() {
        var subcategory = video_subcategories[$(this).val()];
        $('#subcategory').empty();
        for(var i = 0; i < subcategory.length; i++) {
            $('#subcategory').append('<option value="' + subcategory[i] + '">' + subcategory[i] + '</option>');
        }
    });

    $('#submitform').submit(function() {
        var title = $('#submitform input[name="title"]')[0].value.trim();
        if(!title) {
            $('#submitform div.form-error').html('<p>title must not be empty!</p>')
            return false;
        }

        var video_url = $('#submitform input[name="video-url"]')[0].value.trim();
        if(!video_url) {
            $('#submitform div.form-error').html('<p>video url must not be empty!</p>')
            return false;
        }

        var description = $('#submitform textarea[name="description"]')[0].value.trim();
        if(!description) {
            $('#submitform div.form-error').html('<p>description must not be empty!</p>')
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
