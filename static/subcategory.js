$(document).ready(function() {

    var cur_page = 1, cur_order = 'last_liked';

    var urlparts = window.location.pathname.split('/');
    var category = urlparts[1];
    var subcategory = urlparts[2];
    var video_container = $('.video-preview-container');
    var pagination_container = $('.video-pagination-line');

    var hash = window.location.hash;
    if(hash) {
        hash = hash.slice(1).split('&');
        for(var i = 0; i < hash.length; i++) {
            var pair = hash[i].split('=');
            var key = pair[0];
            var value = pair[1];
            if(key == 'page') {
                value = parseInt(value, 10);
                if(!isNaN(value)) {
                    cur_page = Math.min(Math.max(1, value), 100);
                } else {
                    console.log('page number is not integer');
                    cur_page = 1;
                }
            } else if(key == 'order') {
                console.log(value);
                if(value == 'hits' || value == 'last_liked' || value == 'created') {
                    cur_order = value;
                } else {
                    console.log('unknown value for order');
                    cur_order = 'last_liked';
                }
            } else {
                console.log('unknown key');
            }
        }
    }

    var query = {
        'category': category,
        'subcategory': subcategory,
        'page': cur_page,
        'order': cur_order
    };
    update_page(query);
    
    $('.video-pagination-line').on('click', 'div', function() {
        var next_page = $(this).attr('data-page');
        query = {
            'category': category,
            'subcategory': subcategory,
            'page': next_page,
            'order': cur_order
        };
        update_page(query);
    });

    $('.order-option').on('click', 'a', function() {
        var next_order = $(this).attr('prop');
        if(next_order == 'hits' || next_order == 'last_liked' || next_order == 'created' && next_order != cur_order) {
            var query = {
                'category': category,
                'subcategory': subcategory,
                'page': 1,
                'order': next_order
            };
            update_page(query);
        }
    });

    function update_page(query) {
        get_video_list(query, function(err, result) {
            if(err) console.log(err);
            else {
                video_container.empty();
                pagination_container.empty();
                cur_order = query.order;
                cur_page = query.page;
                $('.order-option a.on').removeClass("on");
                $('.order-option a[prop="' + cur_order + '"]').addClass("on");
                if(result.videos.length == 0)
                    video_container.append('<p>No video</p>');
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
    var div = '<div class="video-item">' + 
        '<div>' + video.title + '</div>' + 
        '<a href="' + video.url + '"><div><img src="' + video.thumbnail_url + '"></a></div>' + 
        '<div>Uploader: ' +  video.uploader.nickname + '</div>' + 
        '<div>Created at: ' + video.created + '</div>' + 
        '<div>Hits: ' + video.hits + ' Damakus: ' + video.danmaku_counter + ' </div>' + 
        '<div>Likes: ' + video.likes + ' Last liked: ' + video.last_liked + ' </div></div>';
    return div;
}