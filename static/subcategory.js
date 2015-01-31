$(document).ready(function() {

    var cur_page = 1, cur_order = 'hits';
    var total_page = parseInt(document.getElementById('page-count').innerHTML, 10);
    // Retrieve Videos
    var urlparts = window.location.pathname.split('/');
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
                    cur_page = Math.min(Math.max(1, value), total_page);
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
                    cur_order = 'hits';
                }
            } else {
                console.log('unknown key');
            }
        }
    }

    var query = {
        'category': urlparts[1],
        'subcategory': urlparts[2],
        'page': cur_page,
        'order': cur_order
    };
    console.log(query);
    refresh_page(query);
    
    $('.page-navigator').on('click', 'a', function() {
        var next_page = parseInt($(this).attr('pagenum'), 10);
        if(!isNaN(next_page)) {
            next_page = Math.min(Math.max(1, next_page), total_page);
            var query = {
                'category': urlparts[1],
                'subcategory': urlparts[2],
                'page': next_page,
                'order': cur_order
            };
            refresh_page(query);
        }
    });

    $('.order-option').on('click', 'a', function() {
        var next_order = $(this).attr('prop');
        console.log(next_order);
        if(next_order == 'last_liked') { alert('like function not finished yet!'); return;}
        if(next_order == 'hits' || next_order == 'last_liked' || next_order == 'created' && next_order != cur_order) {
            var query = {
                'category': urlparts[1],
                'subcategory': urlparts[2],
                'page': cur_page,
                'order': next_order
            };
            refresh_page(query);
        }
    });

    function refresh_page(query) {
        get_video_list(query, function(err, videos) {
            if(err) console.log(err);
            else {
                cur_page = query.page;
                cur_order = query.order;
                window.location.hash = '#page=' + cur_page + '&order=' + cur_order;
                $('.order-option a.on').removeClass("on");
                $('.order-option a[prop="' + cur_order + '"').addClass("on");
                $('#video-list').empty();
                for(var i = 0; i < videos.length; i++) {
                    var div = render_video_div(videos[i]);
                    $('#video-list').append(div);
                }
                $('.page-navigator a').remove();
                $('.page-navigator strong').remove();
                var min_page = Math.max(cur_page-2, 1);
                var max_page = Math.min(min_page + 4, total_page);
                var $head = $('#total-count');
                if(cur_page > 1) {
                    $head.after('<a pagenum="' + 1 + '">First</a>');
                    $head = $head.next();
                    $head.after('<a pagenum="' + (cur_page - 1) + '">Previous</a>');
                    $head = $head.next();
                }
                for(var i = min_page; i <= max_page; i++) {
                    if(i == cur_page) {
                        $head.after('<strong>' + i + '</strong>');
                    } else {
                        $head.after('<a pagenum="' + i + '">' + i + '</a>');
                    }
                    $head = $head.next();
                }
                if(cur_page < total_page) {
                    $head.after('<a pagenum="' + (cur_page + 1) + '">Next</a>');
                    $head = $head.next();
                    $head.after('<a pagenum="' + total_page + '">Last</a>');
                    $head = $head.next();
                }
            }
        });
    }
});
