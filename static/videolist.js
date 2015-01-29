render_video_div = function(video) {
    var div = '<div class="video-item">' + 
        '<div>' + video.title + '</div>' + 
        '<a href="' + video.url + '"><div><img src="' + video.thumbnail_url + '"></a></div>' + 
        '<div>Uploader: ' +  video.uploader.nickname + '</div>' + 
        '<div>Created at: ' + video.created + '</div>' + 
        '<div>Hits: ' + video.hits + ' Damakus: ' + video.danmaku_counter + ' </div></div>';
    return div;
}

get_video_list = function(query, callback) {
    $.ajax({
        type: "GET",
        url: "/video",
        data: query,
        success: function(result) {
            if (callback && typeof(callback) === "function") {
                if(result.error)
                    callback(result, []);
                else
                    callback(null, result);
            }
            else
                return result;
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            var err = {'error': true, 'message': thrownError};
            if (callback && typeof(callback) === "function")
                callback(err, []);
            else
                return err;
        }
    });
}