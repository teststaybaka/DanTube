$(document).ready(function() {
    // Retrieve Videos
    $.ajax({
        type: "GET",
        url: document.URL,
        success: function(results) {
            if(!results.error) {
                $('.subcategory').each(function() {
                    var subcategory = $(this).attr('id');
                    if(results[subcategory]) {
                        if(results[subcategory].length == 0) {
                            $(this).append('<p>No video</p>');
                        } else {
                            for(var i = 0; i < results[subcategory].length; i++) {
                                $(this).append('<div class="video-item">' + 
                                '<a href="' + results[subcategory][i].url + '"><div><img src="http://img.youtube.com/vi/' + 
                                results[subcategory][i].vid + '/default.jpg"></a></div>' + 
                                '<div>Uploader: ' +  results[subcategory][i].uploader + '</div>' + 
                                '<div>Created at: ' + results[subcategory][i].created + '</div></div>');
                            }
                        }
                    } else {
                        $(this).append('<p>No video</p>');
                    }
                });
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });
});