$(document).ready(function() {

    var cur_page = 1, cur_order = 'created';

    var video_container = $('.submitted-video-container');
    var pagination_container = $('.video-pagination-line');

    var query = {
        'page': cur_page,
        'order': cur_order
    };
    update_page(query);
    
    $('.video-pagination-line').on('click', 'div', function() {
        var next_page = $(this).attr('data-page');
        query = {
            'page': next_page,
            'order': cur_order
        };
        update_page(query);
    });

    function update_page(query) {
        get_video_list('/account/video', query, function(err, result) {
            if(err) console.log(err);
            else {
                video_container.empty();
                pagination_container.empty();
                cur_order = query.order;
                cur_page = query.page;
                // $('.order-option a.on').removeClass("on");
                // $('.order-option a[prop="' + cur_order + '"]').addClass("on");
                if(result.videos.length == 0)
                    video_container.append('<div class="video-entry none">No video found.</div>');
                else {
                    for(var i = 0; i < result.videos.length; i++) {
                        var video_div = render_video_div(result.videos[i]);
                        video_container.append(video_div);
                    }
                    var pagination = render_pagination(query.page, result.total_pages);
                    pagination_container.append(pagination);
                }
            }
        });
    }
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
                        '<div class="video-time">' + video.created + '</div>' +
                    '</div>' +
                    '<div class="video-title">' +
                        '<a href="' + video.url + '" class="video-title" target="_blank">' + video.title + '</a>' +
                    '</div>' +
                    '<div class="video-playlist">' +
                        '<label>Playlist: </label>' +
                        '<label class="list-title">Not listed</label>' +
                        '<a class="edit-entry">[Add to Playlist]</a>' +
                    '</div>' +
                    '<div class="video-statistic">' +
                        '<div class="video-statistic-entry">Views: ' + video.hits + '</div>' +
                        '<div class="video-statistic-entry">Favors: ' + video.favors + '</div>' +
                        '<div class="video-statistic-entry">Damaku: ' + video.danmaku_counter + '</div>' +
                        '<div class="video-statistic-entry">Comments: ' + video.comment_counter + '</div>' +
                    '</div>' +
                    '<div class="video-edit">' +
                        '<a href="/account/video/edit/dt'+video.id_num+'" class="edit-entry">[Edit Video]</a>' +
                        '<a class="edit-entry">[Manage Danmaku]</a>' +
                    '</div>' +
                    '<div class="video-delete"></div>' +
                '</div>' +
            '</div>';
    return div;
}