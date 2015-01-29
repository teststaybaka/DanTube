$(document).ready(function() {
    // Retrieve Videos
    var urlparts = window.location.pathname.split('/');
    var query = {'category': urlparts[1], 'subcategory': urlparts[2], 'limit': 10};
    get_video_list(query, function(err, videos) {
        if(err) console.log(err);
        else {
            for(var i = 0; i < videos.length; i++) {
                var div = render_video_div(videos[i]);
                $('#video-list').append(div);
            }
        }
    });
});