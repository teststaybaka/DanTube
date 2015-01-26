$(document).ready(function() {
    $('.unfavor-button').click(function(e) {
        var video_div = $(this).parent();
        var url = video_div.find('.video-thumbnail a').attr('href');
        $.ajax({
            type: "POST",
            url: url + '/unfavor',
            success: function(result) {
                if(!result.error) {
                    alert('success');
                    video_div.remove();
                } else {
                    console.log(result.message);                      
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });
});