$(document).ready(function() {
    // Retrieve Videos
    var urlparts = window.location.pathname.split('/');
    $.ajax({
        type: "GET",
        url: "/video",
        data: [{name: 'category', value: urlparts[1]}, {name: 'subcategory', value: urlparts[2]}],
        success: function(results) {
            if(!results.error) {
                for(var i = 0; i < results.length; i++) {
                    console.log(results[i])
                    $('#video-list').append('<div class="video-item">' + 
                        '<a href="' + results[i].url + '"><div><img src="http://img.youtube.com/vi/' + results[i].vid + '/default.jpg"></a></div>' + 
                        '<div>Uploader: ' +  results[i].uploader + '</div>' + 
                        '<div>Created at: ' + results[i].created + '</div></div>');
                }
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });
});