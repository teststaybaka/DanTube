$(document).ready(function() {
    // Retrieve Videos
    var category = window.location.pathname.split('/')[1];
    $('.subcategory').each(function() {
        var subcategory = $(this).attr('id');
        var current_div = $(this);
        var query = {'category': category, 'subcategory': subcategory, 'limit': 10};
        get_video_list(query, function(err, videos) {
            if(err) console.log(err);
            else {
                if(videos.length == 0)
                    current_div.append('<p>No video</p>');
                else {
                    for(var i = 0; i < videos.length; i++) {
                        var div = render_video_div(videos[i]);
                        current_div.append(div);
                    }
                }
            }
        });
    });
});