(function(dt, $) {
function render_video_div(video) {
    var div = '<div class="content-entry">\
                  <a class="video-img" href="' + video.url +'" target="_blank">\
                    <img class="video-img" src="' + video.thumbnail_url + '">\
                  </a>\
                  <div class="video-info">\
                    <div class="category-and-time">\
                      <div class="video-category">' + video.category + '</div>\
                      <div class="video-category-arrow"></div>\
                      <div class="video-category">' + video.subcategory + '</div>\
                      <div class="video-time">' + video.created + '</div>\
                    </div>\
                    <div class="video-title">\
                      <a class="video-title" href="' + video.url + '" target="_blank">' + video.title + '</a>\
                    </div>\
                    <div class="video-intro">' + video.description + '</div>\
                  </div>\
                </div>';
    return div;
}

var is_vid_valid = false;

function vid_check() {
    var vid = $('#video-id').val().trim();
    var vid_re = /^dt[1-9][0-9]*$/;
    if (!vid || !vid_re.test(vid)) {
        $('#video-id-error').addClass('show');
        $('#video-id-error').text('Invalid video ID.');
        $('#video-id').addClass('error');
        $('#video-detail').html('');
        is_vid_valid = false;
        return false;
    } else {
        $.ajax({
            type: "GET",
            url: "/vid_check",
            data: {vid: vid},
            success: function(result) {
                if (result.valid) {
                    $('#video-id-error').removeClass('show');
                    $('#video-id').removeClass('error');
                    var div = render_video_div(result.video);
                    $('#video-detail').html(div);
                    is_vid_valid = true;
                    return true;
                } else {
                    $('#video-id-error').addClass('show');
                    $('#video-id-error').text('Video does not exist.');
                    $('#video-id').addClass('error');
                    $('#video-detail').html('');
                    is_vid_valid = false;
                    return false;
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                is_vid_valid = false;
                return false;
            }
        });
    }
}

$(document).ready(function() {

    $('#report-submission-form input[name="vid"]').focusout(function(evt) {
        vid_check();
    })

    $('#report-submission-form').submit(function(evt) {
        evt.preventDefault();
        $('#change-applying').removeClass('hidden');

        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        if (!is_vid_valid) {
            button.disabled = false;
            $('#change-applying').addClass('hidden');
            return false;
        }

        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: $('#report-submission-form').serialize(),
            success: function(result) {
                console.log(result);
                if(result.error) {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                } else {
                    dt.pop_ajax_message(result.message, 'success');
                    setTimeout(function(){
                        window.location.reload(); 
                    }, 3000);
                }
                $('#change-applying').addClass('hidden');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').addClass('hidden');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });  
});
//end of the file
} (dt, jQuery));
