get_video_list = function(url, query, callback) {
    $.ajax({
        type: "GET",
        url: url,
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