$(document).ready(function() {
    $('div.delete-button').click(function(evt) {
        if ($(evt.target).hasClass('delete')) {
            var id = $(evt.target).attr('data-id');
            $(evt.target).text('Deleting');
            $.ajax({
                type: "POST",
                url: '/account/video/delete/dt'+id,
                async: false,
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        pop_ajax_message('Video deleted! Refreshing...', 'success');
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

    $('div.submitted-video-container').on('click', 'div.video-delete', function(evt) {
        if (evt.target.className != 'video-delete') return;

        $('div.delete-confirm-container').addClass('show');
        var id = $(evt.target).attr('data-id');
        var title = $(evt.target).attr('data-title');
        $('div.delete-button.delete').attr('data-id', id);
        $('div.delete-video-name').text(title);
    });

    var cur_page = 1, cur_order = 'created';
    var cur_keywords = "";
    var order_labels = {
        'created': 'Newest',
        'hits': 'Most viewed',
        'favors': 'Moss favored'
    };
    var video_container = $('.submitted-video-container');
    var pagination_container = $('.video-pagination-line');

    var query = {
        'page': cur_page,
        'order': cur_order
    };
    update_page(query);
    
    $('div.video-pagination-line').on('click', 'div', function(evt) {
        var next_page = $(this).attr('data-page');
        if(next_page != cur_page) {
            if(cur_keywords) {
                query = {
                    'page': next_page,
                    'keywords': cur_keywords
                }
            } else {
                query = {
                    'page': next_page,
                    'order': cur_order
                };
            }
            update_page(query);
        }
    });

    $('.option-entry').click(function() {
        var next_order = $(this).attr('data-order');
        if(next_order != cur_order) {
            var query = {
                'page': 1,
                'order': next_order
            };
            update_page(query);
        }
    })

    $('#sub-search-button').click(function() {
        var next_keywords = $('#sub-search-input').val().trim();
        if(next_keywords) {
            var query = {
                'page': 1,
                'keywords': next_keywords
            };
            update_page(query);
        } else {
            if(cur_keywords) {
                var query = {
                    'page': 1,
                    'order': 'created'
                };
                update_page(query);
            }
        }
    });

    function update_page(query) {
        video_container.empty();
        video_container.append('<div class="video-entry loading"></div>');
        get_video_list('/account/video', query, function(err, result) {
            if(err) console.log(err);
            else {
                video_container.empty();
                pagination_container.empty();
                cur_page = query.page;
                if(query.order)
                    cur_order = query.order;
                if(query.keywords) {
                    cur_keywords = query.keywords;
                    cur_order = 'created';
                }
                else {
                    cur_keywords = "";
                    $('#sub-search-input').val('');
                }
                $('#view-method .selected').html(order_labels[cur_order]);
                // $('.order-option a.on').removeClass("on");
                // $('.order-option a[prop="' + cur_order + '"]').addClass("on");
                if(result.videos.length == 0) {
                    video_container.append('<div class="video-entry none">No video found.</div>');
                } else {
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
    var div = '<div class="video-entry dt' + video.id_num + '">' + 
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
                        '<a href="/account/video/edit/dt' + video.id_num + '" class="edit-entry">[Edit Video]</a>' +
                        '<a class="edit-entry">[Manage Danmaku]</a>' +
                    '</div>' +
                    '<div class="video-delete" data-id="' + video.id_num + '" data-title="' + video.title + '"></div>' +
                '</div>' +
            '</div>';
    return div;
}