$(document).ready(function() {
    // Retrieve Videos
    var category = window.location.pathname.split('/')[1];
    $('.subcategory').each(function() {
        var subcategory = $(this).attr('id');
        var current_div = $(this);
        $.ajax({
            type: "GET",
            url: '/video',
            data: [{name: 'category', value: category}, {name: 'subcategory', value: subcategory}],
            success: function(results) {
                if(!results.error) {
                    if(results.length == 0) {
                        console.log($(this));
                        current_div.append('<p>No video</p>');
                    } else {
                        for(var i = 0; i < results.length; i++) {
                            current_div.append('<div class="video-item">' + 
                            '<div>' + results[i].title + '</div>' + 
                            '<a href="' + results[i].url + '"><div><img src="' + results[i].thumbnail_url + '"></a></div>' + 
                            '<div>Uploader: ' +  results[i].uploader.nickname + '</div>' + 
                            '<div>Created at: ' + results[i].created + '</div>' + 
                            '<div>Hits: ' + results[i].hits + ' Damakus: ' + results[i].danmaku_counter + ' </div></div>');
                        }
                    }                
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });
});