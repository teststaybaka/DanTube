$(document).ready(function() {
    $('div.delete-button').click(function(evt) {
        if ($(evt.target).hasClass('delete')) {
            var id = $(evt.target).attr('data-id');
            $(evt.target).text('Removing');
            $.ajax({
                type: "POST",
                url: '/account/favorites/remove/dt'+id,
                async: false,
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        pop_ajax_message('Video removed!', 'success');
                        $('div.video-entry.dt'+id).remove();
                    } else {
                        pop_ajax_message(result.message, 'error');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                }
            });
        }
        $('div.delete-confirm-container').removeClass('show');
    });

    $('div.favortite-video-container').on('click', 'div.video-delete', function(evt) {
        $('div.delete-confirm-container').addClass('show');
        var id = $(evt.target).attr('data-id');
        var title = $(evt.target).attr('data-title');
        $('div.delete-button.delete').attr('data-id', id);
        $('div.delete-video-name').text(title);
    });

    var videos = [];
    var cur_page = 1;
    var total_videos, total_pages;
    var page_size = 10;
    var video_container = $('div.favortite-video-container');
    var pagination_container = $('div.video-pagination-line');

    video_container.empty();
    video_container.append('<div class="video-entry loading"></div>');
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
        video_container.empty();
        pagination_container.empty();
        if (total_videos == 0) {
            video_container.append('<div class="video-entry none">No video found.</div>');
            return;
        }
        if (page < 1 || page > total_pages) return;
        
        var offset = page_size * (page - 1);
        for(var i = offset; i < Math.min(offset + page_size, total_videos); i++) {
            var video_div = render_video_div(videos[i]);
            video_container.append(video_div);
        }
        var pagination = render_pagination(page, total_pages);
        pagination_container.append(pagination);
    }

    $('div.video-pagination-line').on('click', 'div', function() {
        var next_page = $(this).attr('data-page');
        update_page(next_page);
    });
});

render_video_div = function(video) {
    var div = '<div class="video-entry dt' + video.id_num + '">' + 
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
                    '<div class="video-delete" data-id="' + video.id_num + '" data-title="' + video.title + '"></div>' +
                '</div>' +
              '</div>';
    return div;
}