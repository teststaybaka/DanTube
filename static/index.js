$(document).ready(function() {
    // Retrieve Videos
    $.ajax({
        type: "GET",
        url: "/videolist",
        success: function(result) {
            console.log(result);
            if(!result.error) {
                for(var i = 0; i < result.length; i++) {
                    console.log(result[i])
                    $('#video-list').append('<div class="video-item">' + 
                        '<a href="' + result[i].url + '"><div><img src="http://img.youtube.com/vi/' + result[i].vid + '/default.jpg"></a></div>' + 
                        '<div>Uploader: ' +  result[i].uploader + '</div>' + 
                        '<div>Created at: ' + result[i].created + '</div></div>');
                }
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });
});