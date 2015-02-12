function slideChange() {
    var preIndex = 4 - $('div.slide-dot').index($('div.slide-dot.active'));
    var index = (preIndex + 1)%5;
    $('div.slide-dot.active').removeClass('active');
    $('div.slide-dot:eq('+(4-index)+')').addClass('active');
    $('div.slide-title.active').removeClass('active');
    $('div.slide-title:eq('+(4-index)+')').addClass('active');
    var len = index*document.getElementById('ranking-slides').offsetWidth;
    var slides = document.getElementById('slide-container');
    slides.style.WebkitTransform = "translateX(-"+len+"px)";
    slides.style.msTransform = "translateX(-"+len+"px)";
    slides.style.transform = "translateX(-"+len+"px)";
    window.slideTimeout = setTimeout(slideChange, 5000);
}

$(document).ready(function() {
    
    update_random_videos();
    $('.more-video.fresh').on('click', update_random_videos);
    function update_random_videos() {
        $.ajax({
            type: "GET",
            url: "/video/random",
            data: {'size': 5},
            success: function(result) {
                if(result.error)
                    console.log(result.message);
                else {
                    $('.video-preview.random').remove();
                    for(var i = 0; i < result.videos.length; i++) {
                        var video_div = render_random_video_div(result.videos[i]);
                        $('.sub-category-block.random').append(video_div);
                    }
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    }

    var ranking_page_size = 11;

    $('.sub-category-block.category').each(function() {
        var category = $(this).attr('data-category');
        var dynamic_video_container = $(this).find('.sub-category-dynamic-list .video-preview-container');
        var dynamic_pagination_container = $(this).find('.sub-category-dynamic-list .pagination-line');
        var dynamic_query = {'category': category, 'order': 'last_liked', 'page': 1};
        update_page(dynamic_query, dynamic_video_container, dynamic_pagination_container, 'dynamic');
        var ranking_video_container = $(this).find('.sub-category-side-line .ranking-video-container');
        var ranking_pagination_container = $(this).find('.sub-category-side-line .pagination-line');
        var ranking_query = {'category': category, 'order': 'hits', 'page': 1, 'page_size': ranking_page_size};
        update_page(ranking_query, ranking_video_container, ranking_pagination_container, 'ranking');
    });

    $('.sub-category-dynamic-list .pagination-line').on('click', 'div', function() {
        var pagination_container = $(this).parent();
        var video_container = pagination_container.prev();
        var category = video_container.parent().parent().attr('data-category');
        var page = $(this).attr('data-page');
        query = {'category': category, 'order': 'last_liked', 'page': page};
        update_page(query, video_container, pagination_container, 'dynamic');
    });

    $('.sub-category-side-line .pagination-line').on('click', 'div', function() {
        var pagination_container = $(this).parent();
        var video_container = pagination_container.prev();
        var category = video_container.parent().parent().attr('data-category');
        var page = $(this).attr('data-page');
        query = {'category': category, 'order': 'hits', 'page': page, 'page_size': ranking_page_size};
        update_page(query, video_container, pagination_container, 'ranking');
    });

    function update_page(query, video_container, pagination_container, video_div_type) {
        get_video_list('/video', query, function(err, result) {
            if(err) console.log(err);
            else {
                video_container.empty();
                pagination_container.empty();
                if(result.videos.length == 0)
                    video_container.append('<p>No video</p>');
                else {
                    for(var i = 0; i < result.videos.length; i++) {
                        var video_div;
                        if(video_div_type == 'dynamic')
                            video_div = render_dynamic_video_div(result.videos[i]);
                        else if (video_div_type == 'ranking') {
                            var rank = (query.page - 1) * ranking_page_size + i + 1;
                            video_div = render_ranking_video_div(result.videos[i], rank);
                        }
                        video_container.append(video_div);
                    }
                    var pagination = render_pagination(query.page, result.total_pages);
                    pagination_container.append(pagination);
                }
            }
        });
    }

    window.slideTimeout = setTimeout(slideChange, 5000);
    $('div.slide-dot').click(function(evt) {
        if ($(evt.target).hasClass('active')) return;
        
        clearTimeout(window.slideTimeout);
        window.slideTimeout = setTimeout(slideChange, 5000);
        var preIndex = 4 - $('div.slide-dot').index($('div.slide-dot.active'));
        $('div.slide-dot.active').removeClass('active');
        $(evt.target).addClass('active');
        var index = 4 - $('div.slide-dot').index(evt.target);
        $('div.slide-title.active').removeClass('active');
        $('div.slide-title:eq('+(4-index)+')').addClass('active');
        var len = index*document.getElementById('ranking-slides').offsetWidth;
        var slides = document.getElementById('slide-container');
        slides.style.WebkitTransform = "translateX(-"+len+"px)";
        slides.style.msTransform = "translateX(-"+len+"px)";
        slides.style.transform = "translateX(-"+len+"px)";
    });
});

render_random_video_div = function(video) {
    var preview_div = render_preview_video_div(video);
    return '<a class="video-preview random" target="_blank" href="' + video.url + '">' + preview_div + '</a>';
}

render_dynamic_video_div = function(video) {
    var preview_div = render_preview_video_div(video);
    return '<a class="video-preview" target="_blank" href="' + video.url + '">' + preview_div + '</a>';
}

render_preview_video_div = function(video) {
    var div =   '<div class="video-preview-thumbnail">' + 
                    '<img src="' + video.thumbnail_url + '">' + 
                    '<!-- <div class="preview-time">23:20</div> -->' + 
                '</div>' + 
                '<div class="video-preview-statistic">' + 
                    '<div class="video-preview-title">' + video.title + '</div>' + 
                    '<div class="video-preview-hits">' + video.hits + '</div>' + 
                    '<div class="video-preview-danmaku-num">' + video.danmaku_counter + '</div>' + 
                '</div>' + 
                '<div class="video-preview-popup">' + 
                    '<div class="popup-title">' + video.title + '</div>' + 
                    '<div class="popup-statistic-line">' + 
                        '<div class="popup-statistic-entry views">' + video.hits + '</div>' + 
                        '<div class="popup-statistic-entry favorites">' + video.favors + '</div>' + 
                        '<div class="popup-statistic-entry danmaku">' + video.danmaku_counter + '</div>' + 
                        '<div class="popup-statistic-entry bullets">' + video.bullets + '</div>' + 
                    '</div>' + 
                    '<div class="popup-intro">' + 
                        '<div class="popup-thumbnail">' + 
                            '<img src="' + video.thumbnail_url + '">' + 
                        '</div>' + 
                        '<div class="popup-descript">' + 
                            video.description + 
                        '</div>' + 
                    '</div>' + 
                    '<div class="popup-upload-info">' + 
                        '<div class="popup-uploader">UPer: ' + video.uploader.nickname + '</div>' + 
                        '<div class="popup-upload-time">' + video.created + '</div>' + 
                    '</div>' + 
                '</div>';
    return div;
}

render_ranking_video_div = function(video, rank) {
    var div = "";
    if (rank <= 3) {
        div = '<a class="ranking-video-entry" target="_blank" href="' + video.url + '">' + 
            '<div class="ranking-top-video">' + 
                '<div class="top-video-thumbnail">' + 
                    '<img src="' + video.thumbnail_url + '">' + 
                '</div>' + 
                '<div class="top-No">' + rank + '</div>' + 
                '<div class="top-video-title">' + video.title + '</div>' + 
            '</div>' + 
            '<div class="top-video-hits">' + video.hits + '</div>' + 
            '<div class="top-video-danmaku-num">' + video.danmaku_counter + '</div>';
    } else {
        div = '<a class="ranking-video-entry" target="_blank" href="' + video.url + '">' + 
                '<div class="ranking-No">' + rank + '</div>' + 
                '<div class="ranking-video-title">' + video.title + '</div>';
    }
    div += '<div class="video-preview-popup">' + 
                '<div class="popup-title">' + video.title + '</div>' + 
                '<div class="popup-statistic-line">' + 
                    '<div class="popup-statistic-entry views">' + video.hits + '</div>' + 
                    '<div class="popup-statistic-entry favorites">' + video.favors + '</div>' + 
                    '<div class="popup-statistic-entry danmaku">' + video.danmaku_counter + '</div>' + 
                    '<div class="popup-statistic-entry bullets">' + video.bullets + '</div>' + 
                '</div>' + 
                '<div class="popup-intro">' + 
                    '<div class="popup-thumbnail">' + 
                        '<img src="' + video.thumbnail_url + '">' + 
                    '</div>' + 
                    '<div class="popup-descript">' + 
                        video.description + 
                    '</div>' + 
                '</div>' + 
                '<div class="popup-upload-info">' + 
                    '<div class="popup-uploader">UPer: ' + video.uploader.nickname + '</div>' + 
                    '<div class="popup-upload-time">' + video.created + '</div>' + 
                '</div>' + 
            '</div>' + 
        '</a>';
    return div;
}