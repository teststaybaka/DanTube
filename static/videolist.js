render_pagination = function(cur_page, total_pages) {
    var pagination = "";
    var min_page = Math.max(cur_page-2, 1);
    var max_page = Math.min(min_page + 4, total_pages);
    
    if(cur_page > 1) {
        pagination += '<div data-page="' + 1 + '"><<</div>';
        pagination += '<div data-page="' + (cur_page - 1) + '"><</div>';
    }
    for(var i = min_page; i <= max_page; i++) {
        if(i == cur_page) {
            pagination += '<div class="active" data-page="' + i + '">' + i + '</div>';
        } else {
            pagination += '<div data-page="' + i + '">' + i + '</div>';
        }
    }
    if(cur_page < total_pages) {
        pagination += '<div data-page="' + (cur_page + 1) + '">></div>';
        pagination += '<div data-page="' + total_pages + '">>></div>';
    }
    return pagination;
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