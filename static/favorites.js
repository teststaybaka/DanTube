$(document).ready(function() {
    var videos = [];
    var cur_page = 1;
    var total_videos, total_pages;
    var page_size = 10;
    var video_container = $('.favortite-video-container');
    var pagination_container = $('.video-pagination-line');

    get_video_list('/account/favorites', {'ajax': true}, function(err, result) {
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
            video_container.append('<div class="video-entry none">No video found.</div>');
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

    $('.unfavor-button').click(function(e) {
        var video_div = $(this).parent();
        var url = video_div.find('.video-thumbnail a').attr('href');
        $.ajax({
            type: "POST",
            url: url + '/unfavor',
            success: function(result) {
                if(!result.error) {
                    alert('success');
                    video_div.remove();
                } else {
                    console.log(result.message);                      
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });
});

render_video_div = function(video) {
    var div = '<div class="video-entry">' +
                '<a class="video-img" href="' + video.url + '" target="_blank">' +
                    '<img class="video-img" src="' + video.thumbnail_url + '">' +
                '</a>' +
                '<div class="video-info">' +
                    '<div>' +
                        '<div class="video-category">' + video.category + '</div>' +
                        '<div class="video-category-arrow"></div>' +
                        '<div class="video-category">' + video.subcategory + '</div>' +
                    '</div>' +
                    '<div>' +
                        '<a href="' + video.url + '" class="video-title favored" target="_blank">' + video.title + '</a>' +
                    '</div>' +
                    '<div class="video-statistic favored">' +
                        '<div class="video-statistic-entry">Views: ' + video.hits + '</div>' +
                        '<div class="video-statistic-entry">Favors: ' + video.favors + '</div>' +
                        '<div class="video-statistic-entry">Damaku: ' + video.danmaku_counter + '</div>' +
                        '<div class="video-statistic-entry">Comments: ' + video.comment_counter + '</div>' +
                    '</div>' +
                    '<div class="favored-time">' +
                      '<label>Favored at: </label>' +
                        video.favored_time +
                    '</div>' +
                    '<div class="video-delete"></div>' +
                '</div>' +
              '</div>';
    return div;
}