(function(dt, $) {
function slideMove(index) {
    var total_slides = $('div.slide-dot').length;
    var preIndex = total_slides - 1 - $('div.slide-dot').index($('div.slide-dot.active'));
    $('div.slide-dot.active').removeClass('active');
    $('div.slide-dot:eq('+(total_slides - 1 - index)+')').addClass('active');
    $('div.slide-title.active').removeClass('active');
    $('div.slide-title:eq('+(total_slides - 1 - index)+')').addClass('active');
    var len = index*document.getElementById('ranking-slides').offsetWidth;
    var slides = document.getElementById('slide-container');
    slides.style.WebkitTransform = "translateX(-"+len+"px)";
    slides.style.msTransform = "translateX(-"+len+"px)";
    slides.style.transform = "translateX(-"+len+"px)";
}

function slideChange() {
    var total_slides = $('div.slide-dot').length;
    var preIndex = total_slides - 1 - $('div.slide-dot').index($('div.slide-dot.active'));
    var index = (preIndex + 1)%total_slides;
    slideMove(index);
    window.slideTimeout = setTimeout(slideChange, 5000);
}

function update_random_videos() {
    $('div.single-preview-line').empty();
    $('div.single-preview-line').append('<div class="preview-status loading"></div>');

    $.ajax({
        type: 'POST',
        url: '/video/random',
        data: {size: 5},
        success: function(result) {
            console.log(result)
            $('div.single-preview-line').empty();
            if(!result.error) {
                for(var i = 0; i < result.videos.length; i++) {
                    var video_div = render_wide_preview_video_div(result.videos[i]);
                    $('div.single-preview-line').append(video_div);
                }
            } else {
                console.log('ssssssss')
                $('div.single-preview-line').empty();
                $('div.single-preview-line').append('<div class="preview-status">Load failed.</div>');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            console.log('ddddddddd')
            $('div.single-preview-line').empty();
            $('div.single-preview-line').append('<div class="preview-status">Load failed.</div>');
        }
    });
}

function update_page(query, video_container, pagination_container, video_div_type) {
    video_container.empty();
    pagination_container.empty();
    video_container.append('<div class="preview-status loading"></div>');

    $.ajax({
        type: 'POST',
        url: '/video/category',
        data: query,
        success: function(result) {
            video_container.empty();
            if (!result.error) {
                if(result.videos.length == 0) {
                    video_container.append('<div class="preview-status">No video.</div>');
                } else {
                    for(var i = 0; i < result.videos.length; i++) {
                        var video_div;
                        if(video_div_type == 'dynamic') {
                            video_div = render_dynamic_video_div(result.videos[i]);
                        } else if (video_div_type == 'wide_preview') {
                            video_div = render_wide_preview_video_div(result.videos[i]);
                        } else { // ranking
                            var rank = (query.page - 1) * ranking_page_size + i;
                            video_div = render_ranking_video_div(result.videos[i], rank);
                        }
                        video_container.append(video_div);
                    }

                    var pagination = dt.render_pagination(query.page, result.total_pages);
                    pagination_container.append(pagination);

                    video_container.prev().children('a.refresh-video').attr('data-page', query.page);
                }
            } else {
                video_container.empty();
                video_container.append('<div class="preview-status">Load failed.</div>');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            video_container.empty();
            video_container.append('<div class="preview-status">Load failed.</div>');
        }
    });
}

var ranking_page_size = 10;
var dynamic_page_size = 12;
var wide_dynamic_page_size = 15;
$(document).ready(function() {
    window.slideTimeout = setTimeout(slideChange, 5000);
    $('div.slide-dot').click(function(evt) {
        if ($(evt.target).hasClass('active')) return;
        
        clearTimeout(window.slideTimeout);
        var total_slides = $('div.slide-dot').length;
        var index = total_slides - 1 - $('div.slide-dot').index(evt.target);
        slideMove(index);
        window.slideTimeout = setTimeout(slideChange, 5000);
    });

    $('a.refresh-video.random').click(update_random_videos);
    if ($('div.sub-category-block.random').length == 1) update_random_videos();

    var initialize_check = function() {
        $('div.sub-category-block.category').each(function() {
            var category = $(this).attr('data-category');
            var subcategory = $(this).attr('data-subcategory');
            var dynamic_video_container = $(this).find('div.video-preview-container');
            var dynamic_pagination_container = $(this).find('div.sub-category-dynamic-list div.pagination-line');
            if (dynamic_video_container.children().length > 0
                || $(window).scrollTop() < $(this).offset().top - 30 - $(window).height()) return;

            var page_size = dynamic_page_size;
            var renderType = 'dynamic';
            if ($(this).hasClass('wide')) {
                page_size = wide_dynamic_page_size;
                renderType = 'wide_preview';
            }
            var order = 'last_updated';
            if ($(this).hasClass('newest')) {
                order = 'created';
            }
            var dynamic_query = {'category': category, 'subcategory': subcategory, 'order': order, 'page': 1, 'page_size': page_size};
            update_page(dynamic_query, dynamic_video_container, dynamic_pagination_container, renderType);

            if (!($(this).hasClass('wide')) ) {
                var ranking_video_container = $(this).find('div.ranking-video-container');
                var ranking_pagination_container = $(this).find('div.sub-category-side-line div.pagination-line');
                // var ranking_query = {'category': category, 'subcategory': subcategory, 'order': 'hits', 'page': 1, 'page_size': ranking_page_size};
                var ranking_query = {'category': category, 'subcategory': subcategory, 'order': 'hot_score', 'page': 1, 'page_size': ranking_page_size};
                update_page(ranking_query, ranking_video_container, ranking_pagination_container, 'ranking');
            }
        });
    }
    $(window).scroll(initialize_check);
    initialize_check();

    $('div.sub-category-dynamic-list div.pagination-line').on('click', 'a', function() {
        var pagination_container = $(this).parent();
        var video_container = pagination_container.prev();
        var sub_category_block = video_container.parent().parent();
        var category = sub_category_block.attr('data-category');
        var subcategory = sub_category_block.parent().attr('data-subcategory');
        var page = $(this).attr('data-page');
        var page_size = dynamic_page_size;
        var renderType = 'dynamic';
        if (sub_category_block.hasClass('wide')) {
            page_size = wide_dynamic_page_size;
            renderType = 'wide_preview';
        }
        var order = 'last_updated';
        if (sub_category_block.hasClass('newest')) {
            order = 'created';
        }
        var query = {'category': category, 'subcategory': subcategory, 'order': order, 'page': page, 'page_size': page_size};
        update_page(query, video_container, pagination_container, renderType);
    });

    $('div.sub-category-side-line div.pagination-line').on('click', 'a', function() {
        var pagination_container = $(this).parent();
        var video_container = pagination_container.prev();
        var sub_category_block = video_container.parent().parent();
        var category = sub_category_block.attr('data-category');
        var subcategory = sub_category_block.attr('data-subcategory');
        var page = $(this).attr('data-page');
        // var query = {'category': category, 'subcategory': subcategory, 'order': 'hits', 'page': page, 'page_size': ranking_page_size};
        var query = {'category': category, 'subcategory': subcategory, 'order': 'hot_score', 'page': page, 'page_size': ranking_page_size};
        update_page(query, video_container, pagination_container, 'ranking');
    });

    $('a.refresh-video').click(function() {
        var page = $(this).attr('data-page');
        if (!page) page = '1';
        var video_container = $(this).parent().next();
        var pagination_container = video_container.next();
        var sub_category_block = video_container.parent().parent();
        var category = sub_category_block.attr('data-category');
        var subcategory = sub_category_block.attr('data-subcategory');
        var page_size = dynamic_page_size;
        var renderType = 'dynamic';
        if (sub_category_block.hasClass('wide')) {
            page_size = wide_dynamic_page_size;
            renderType = 'wide_preview';
        }
        var order = 'last_updated';
        if (sub_category_block.hasClass('newest')) {
            order = 'created';
        }
        var query = {'category': category, 'subcategory': subcategory, 'order': order, 'page': page, 'page_size': page_size};
        update_page(query, video_container, pagination_container, renderType);
    });
});

function render_dynamic_video_div(video) {
    var preview_div = render_preview_video_div(video);
    return '<a class="video-preview" target="_blank" href="' + video.url + '">' + preview_div + '</a>';
}

function render_wide_preview_video_div(video) {
    var preview_div = render_preview_video_div(video);
    return '<a class="video-preview wide" target="_blank" href="' + video.url + '">' + preview_div + '</a>';
}

function render_preview_video_div(video) {
    var div =   '<div class="video-preview-thumbnail">\
                    <img src="' + video.thumbnail_url + '">\
                </div>\
                <div class="video-preview-statistic">\
                    <div class="video-preview-title">' + video.title + '</div>\
                    <div class="video-preview-hits"><span class="preview-icon views"></span>' + dt.numberWithCommas(video.hits) + '</div>\
                    <div class="video-preview-comment-num"><span class="preview-icon comment"></span>' + dt.numberWithCommas(video.comment_counter) + '</div>\
                </div>\
                <div class="video-preview-popup">\
                    <div class="popup-title">' + video.title + '</div>\
                    <div class="popup-statistic-line">\
                        <div class="popup-statistic-entry"><span class="preview-icon views"></span>' + dt.numberWithCommas(video.hits) + '</div>\
                        <div class="popup-statistic-entry"><span class="preview-icon favorites"></span>' + dt.numberWithCommas(video.favors) + '</div>\
                        <div class="popup-statistic-entry"><span class="preview-icon comment"></span>' + dt.numberWithCommas(video.comment_counter) + '</div>\
                        <div class="popup-statistic-entry"><span class="preview-icon bullets"></span>' + dt.numberWithCommas(video.bullets) + '</div>\
                    </div>\
                    <div class="popup-intro">\
                        <div class="popup-thumbnail">\
                            <img src="' + video.thumbnail_url + '">\
                            <div class="preview-time">' + dt.secondsToTime(video.duration) + '</div>\
                        </div>\
                        <div class="popup-descript">' + video.description + '</div>\
                    </div>\
                    <div class="popup-upload-info">\
                        <div class="popup-uploader">UPer: ' + video.uploader.nickname + '</div>\
                        <div class="popup-upload-time">' + video.created + '</div>\
                    </div>\
                </div>';
    return div;
}

function render_ranking_video_div(video, rank) {
    var div = "";
    if (rank%ranking_page_size < 3) {
        div = '<a class="ranking-content-entry" target="_blank" href="' + video.url + '">\
            <div class="ranking-top-video">\
                <div class="top-video-thumbnail">\
                    <img src="' + video.thumbnail_url + '">\
                </div>\
                <div class="top-No">' + (rank+1) + '</div>\
                <div class="top-video-title">' + video.title + '</div>\
            </div>\
            <div class="top-video-hits"><span class="preview-icon views"></span>' + dt.numberWithCommas(video.hits) + '</div>\
            <div class="top-video-comment-num"><span class="preview-icon comment"></span>' + dt.numberWithCommas(video.comment_counter) + '</div>';
    } else {
        div = '<a class="ranking-content-entry" target="_blank" href="' + video.url + '">\
                <div class="ranking-No">' + (rank+1) + '</div>\
                <div class="ranking-video-title">' + video.title + '</div>';
    }

    div += '<div class="video-preview-popup">\
                <div class="popup-title">' + video.title + '</div>\
                <div class="popup-statistic-line">\
                    <div class="popup-statistic-entry"><span class="preview-icon views"></span>' + dt.numberWithCommas(video.hits) + '</div>\
                    <div class="popup-statistic-entry"><span class="preview-icon favorites"></span>' + dt.numberWithCommas(video.favors) + '</div>\
                    <div class="popup-statistic-entry"><span class="preview-icon comment"></span>' + dt.numberWithCommas(video.comment_counter) + '</div>\
                    <div class="popup-statistic-entry"><span class="preview-icon bullets"></span>' + dt.numberWithCommas(video.bullets) + '</div>\
                </div>\
                <div class="popup-intro">\
                    <div class="popup-thumbnail">\
                        <img src="' + video.thumbnail_url + '">\
                        <div class="preview-time">' + dt.secondsToTime(video.duration) + '</div>\
                    </div>\
                    <div class="popup-descript">' + video.description + '</div>\
                </div>\
                <div class="popup-upload-info">\
                    <div class="popup-uploader">UPer: ' + video.uploader.nickname + '</div>\
                    <div class="popup-upload-time">' + video.created + '</div>\
                </div>\
            </div>\
        </a>';
    return div;
}
//end of the file
} (dt, jQuery));
