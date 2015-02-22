function update_page(page) {
    var query = {
        'page': page, 
        'page_size': 10, 
        'keywords': $('#sub-search-input').val().trim(), 
        'order': $('#view-method div.selected').attr('data-order')
    };
    video_container = $('div.submitted-video-container');
    pagination_container = $('div.pagination-line');

    video_container.empty();
    pagination_container.empty();
    video_container.append('<div class="video-entry loading"></div>');

    $.ajax({
        type: 'POST',
        url: window.location,
        data: query,
        success: function(result) {
            video_container.empty();
            if (!result.error) {
                $('#sub-title').text(result.total_found + ' Videos');
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
            } else {
                console.log(result);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            video_container.empty();
            video_container.append('<div class="video-entry none">Load failed.</div>');
        }
    });
}

var order_labels = {
    'created': 'Newest',
    'hits': 'Most viewed',
    'favors': 'Moss favored'
};

$(document).ready(function() {
    $('div.delete-button').click(function(evt) {
        if ($(evt.target).hasClass('delete')) {
            var ids= $(evt.target).attr('data-id').split(';');
            $(evt.target).text('Deleting');
            $.ajax({
                type: "POST",
                url: '/account/video/delete',
                async: false,
                data: {ids: ids},
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        pop_ajax_message('Videos deleted!', 'success');
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

    $('div.submitted-video-container').on('click', 'div.video-select-checkbox', function(evt) {
        if ($(evt.target).hasClass('checked')) {
            $(evt.target).removeClass('checked');
        } else {
            $(evt.target).addClass('checked');
        }
    });

    $('#view-method div.option-entry').click(function(evt) {
        $('#sub-search-input').val('');
        var selected = $('#view-method div.selected');
        selected.attr('data-order', $(evt.target).attr('data-order'));
        selected.text(order_labels[selected.attr('data-order')])
        update_page(1);
    })

    $('#sub-search-block').submit(function() {
        var selected = $('#view-method div.selected');
        selected.attr('data-order', 'created');
        selected.text(order_labels[selected.attr('data-order')])
        update_page(1);
        return false;
    });

    $('div.pagination-line').on('click', 'div', function() {
        var page = $(this).attr('data-page');
        update_page(page);
    });
    update_page(1);
});

function render_video_div(video) {
    var div = '<div class="video-entry dt' + video.id_num + '">\
                <a class="video-img" href="' + video.url + '" target="_blank">\
                    <img class="video-img" src="' + video.thumbnail_url + '">\
                </a>\
                <div class="video-info">\
                    <div>\
                        <div class="video-category">' + video.category + '</div>\
                        <div class="video-category-arrow"></div>\
                        <div class="video-category">' + video.subcategory + '</div>\
                        <div class="video-time">' + video.created + '</div>\
                    </div>\
                    <div class="video-title">\
                        <a href="' + video.url + '" class="video-title" target="_blank">' + video.title + '</a>\
                    </div>\
                    <div class="video-playlist">\
                        <label>Prime list: </label>\
                        <label class="list-title">Not listed</label>\
                    </div>\
                    <div class="video-statistic">\
                        <div class="video-statistic-entry">Views: ' + numberWithCommas(video.hits) + '</div>\
                        <div class="video-statistic-entry">Favors: ' + numberWithCommas(video.favors) + '</div>\
                        <div class="video-statistic-entry">Comments: ' + numberWithCommas(video.comment_counter) + '</div>\
                        <div class="video-statistic-entry">Bullets: ' + numberWithCommas(video.bullets) + '</div>\
                    </div>\
                    <div class="video-edit">\
                        <a href="/account/video/edit/dt' + video.id_num + '" class="edit-entry">[Edit Video]</a>\
                        <a class="edit-entry">[Manage Danmaku]</a>\
                    </div>\
                    <div class="video-select-checkbox" data-id="' + video.id_num + '" data-title="' + video.title + '"></div>\
                </div>\
            </div>';
    return div;
}
