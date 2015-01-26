$(document).ready(function() {
    // Retrieve Videos
    $.ajax({
        type: "GET",
        url: "/video",
        success: function(results) {
            if(!results.error) {
                for(var i = 0; i < results.length; i++) {
                    console.log(results[i])
                    $('#video-list').append('<div class="video-item">' + 
                        '<div>' + results[i].title + '</div>' + 
                        '<a href="' + results[i].url + '"><div><img src="' + results[i].thumbnail_url + '"></a></div>' + 
                        '<div>Uploader: ' +  results[i].uploader.nickname + '</div>' + 
                        '<div>Created at: ' + results[i].created + '</div>' + 
                        '<div>Hits: ' + results[i].hits + ' Damakus: ' + results[i].danmaku_counter + ' </div></div>');
                }
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });
});