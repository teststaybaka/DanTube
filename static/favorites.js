$(document).ready(function() {
    $('div.delete-button').click(function(evt) {
        if ($(evt.target).hasClass('delete')) {
            var ids= $(evt.target).attr('data-id').split(';');
            $(evt.target).text('Removing');
            $.ajax({
                type: "POST",
                url: '/account/favorites/remove',
                async: false,
                data: {ids: ids},
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        pop_ajax_message('Videos removed!', 'success');
                        ids = result.message;
                        for (var i = 0; i < ids.length; i++) {
                            $('div.video-entry.dt'+ids[i]).remove();
                        }
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

    $('#action-select div.option-entry.delete').click(function() {
        var checked_boxes = $('div.video-select-checkbox.checked');
        if (checked_boxes.length != 0) {
            $('div.delete-confirm-container').addClass('show');
            $('div.delete-target-name').remove();
            var ids = $(checked_boxes[0]).attr('data-id');
            var title = $(checked_boxes[0]).attr('data-title');
            $('div.delete-buttons-line').before('<div class="delete-target-name">'+title+'</div>');
            for (var i = 1; i < checked_boxes.length; i++) {
                ids += ';'+ $(checked_boxes[i]).attr('data-id');
                title = $(checked_boxes[i]).attr('data-title');
                $('div.delete-buttons-line').before('<div class="delete-target-name">'+title+'</div>');
            }
            $('div.delete-button.delete').attr('data-id', ids);
        }
    });

    $('div.favortite-video-container').on('click', 'div.video-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });

    var videos = [];
    var cur_page = 1;
    var total_videos, total_pages;
    var page_size = 10;
    var video_container = $('div.favortite-video-container');
    var pagination_container = $('div.pagination-line');

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

    $('div.pagination-line').on('click', 'div', function() {
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
                        '<div class="video-statistic-entry">Comments: ' + video.comment_counter + '</div>' +
                        '<div class="video-statistic-entry">Bullets: ' + video.bullets + '</div>' +
                    '</div>' +
                    '<div class="favored-time">' +
                      '<label>Favored at: </label>' +
                        video.favored_time +
                    '</div>' +
                    '<div class="video-select-checkbox" data-id="' + video.id_num + '" data-title="' + video.title + '"></div>' +
                '</div>' +
              '</div>';
    return div;
}