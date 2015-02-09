$(document).ready(function() {
    var videos = [];
    var cur_page = 1;
    var total_videos, total_pages;
    var page_size = 10;
    var video_container = $('.history-video-container');
    var pagination_container = $('.video-pagination-line');

    get_video_list('/history', {'ajax': true}, function(err, result) {
        if(err) console.log(err);
        else {
            videos = result.videos;
            total_videos = videos.length;
            total_pages = Math.ceil(total_videos / page_size);
            
            update_page(1);
        }
    });

    function update_page(page) {
        if (total_videos == 0) {
            video_container.append('<div class="no-history">No watch history found.</div>');
            return;
        }
        if (page < 1 || page > total_pages) return;
        video_container.empty();
        pagination_container.empty();
        var offset = page_size * (page - 1);
        for(var i = offset; i < Math.min(offset + page_size, total_videos); i++) {
            var video_div = render_video_div(videos[i]);
            video_container.append(video_div);
        }
        var pagination = render_pagination(page, total_pages);
        pagination_container.append(pagination);
    }

    $('.video-pagination-line').on('click', 'div', function() {
        var next_page = $(this).attr('data-page');
        update_page(next_page);
    });
});

render_video_div = function(video) {
    var div = '<div class="video-entry">' +
                  '<a class="video-img" href="' + video.url + '" target="_blank">' +
                    '<img src="' + video.thumbnail_url + '">' +
                  '</a>' +
                  '<div class="video-info">' +
                    '<div class="video-title">' +
                      '<a href="' + video.url + '" class="video-title" target="_blank">' + video.title + '</a>' +
                    '</div>' +
                    '<div class="uper-line">' +
                      '<label>by </label>' +
                      '<a target="_blank" href="' + video.uploader.space_url + '"> ' + video.uploader.nickname + '</a>' +
                    '</div>' +
                    '<div class="video-statistic">' +
                      '<div class="video-statistic-entry">Views: ' + video.hits + '</div>' +
                      '<div class="video-statistic-entry">Favors: ' + video.favors + '</div>' +
                      '<div class="video-statistic-entry">Damaku: ' + video.danmaku_counter + '</div>' +
                      '<div class="video-statistic-entry">Comments: ' + video.comment_counter + '</div>' +
                    '</div>' +
                    '<div class="last-viewed">Last watched: ' + video.last_viewed_time + '</div>' +
                  '</div>' +
                '</div>';
    return div;
}