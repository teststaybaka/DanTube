(function(dt, $) {
var video_hover_timeout;
var slide_timeout;
var right_margin = 11;
var element_width = 196;
var page_columns;
var page_width;

function slideMove(index) {
    var total_slides = $('div.slide-dot').length;
    var preIndex = total_slides - 1 - $('div.slide-dot').index($('div.slide-dot.active'));
    $('div.slide-dot.active').removeClass('active');
    $('div.slide-dot:eq('+(total_slides - 1 - index)+')').addClass('active');
    $('div.slide-title.active').removeClass('active');
    $('div.slide-title:eq('+(total_slides - 1 - index)+')').addClass('active');
    var slide_container = document.getElementById('slide-container');
    var len = index*slide_container.offsetWidth;
    slide_container.style.WebkitTransform = "translateX(-"+len+"px)";
    slide_container.style.msTransform = "translateX(-"+len+"px)";
    slide_container.style.transform = "translateX(-"+len+"px)";
}

function slideChange() {
    var total_slides = $('div.slide-dot').length;
    var preIndex = total_slides - 1 - $('div.slide-dot').index($('div.slide-dot.active'));
    var index = (preIndex + 1)%total_slides;
    slideMove(index);
    slide_timeout = setTimeout(slideChange, 5000);
}

$(document).ready(function() {
    $(window).resize(function() {
        page_width = $('#body-container').width() + right_margin;
        page_columns = page_width/(element_width + right_margin);
    });
    page_width = $('#body-container').width() + right_margin;
    page_columns = page_width/(element_width + right_margin);

    slide_timeout = setTimeout(slideChange, 5000);
    $('div.slide-dot').click(function(evt) {
        if ($(evt.target).hasClass('active')) return;
        
        clearTimeout(slide_timeout);
        var total_slides = $('div.slide-dot').length;
        var index = total_slides - 1 - $('div.slide-dot').index(evt.target);
        slideMove(index);
        slide_timeout = setTimeout(slideChange, 5000);
    });
    
    var preview_popup = $('.video-preview-popup');
    $('.video-slide-container').on('mouseenter', 'a.video-preview', function() {
        var video_preview = $(this);
        var offset = video_preview.offset();

        video_hover_timeout = setTimeout(function() {
            preview_popup.find('.popup-title').text(video_preview.find('.video-preview-title').text());
            preview_popup.find('.popup-descript').text(video_preview.find('.video-preview-popup-info[data-type="intro"]').text());
            preview_popup.find('.popup-statistic-entry .hits-num').text(video_preview.find('.video-preview-popup-info[data-type="hits"]').text());
            preview_popup.find('.popup-statistic-entry .likes-num').text(video_preview.find('.video-preview-popup-info[data-type="likes"]').text());
            preview_popup.find('.popup-statistic-entry .comment-num').text(video_preview.find('.video-preview-popup-info[data-type="comments"]').text());
            preview_popup.find('.popup-statistic-entry .bullets-num').text(video_preview.find('.video-preview-popup-info[data-type="bullets"]').text());
            preview_popup.find('.preview-time').text(video_preview.find('.video-preview-popup-info[data-type="duration"]').text());
            preview_popup.find('.popup-uploader').text(video_preview.find('.video-preview-popup-info[data-type="nickname"]').text());
            preview_popup.find('.popup-upload-time').text(video_preview.find('.video-preview-popup-info[data-type="created"]').text());
            preview_popup.find('.popup-upload-time').text(video_preview.find('.video-preview-popup-info[data-type="created"]').text());
            preview_popup.find('.popup-thumbnail img').attr('src', video_preview.find('.video-preview-thumbnail img').attr('src'));
            preview_popup.find('.popup-uploader-avatar img').attr('src', video_preview.find('.video-preview-popup-info[data-type="avatar"]').text());

            if (video_preview.width() + offset.left >= $('#body-container').width()) {
                preview_popup.addClass('show').css({left: offset.left - video_preview.width() - right_margin, top: offset.top - 5 - preview_popup[0].scrollHeight});
            } else {
                preview_popup.addClass('show').css({left: offset.left, top: offset.top - 5 - preview_popup[0].scrollHeight});
            }
        }, 400);
    });
    $('.video-slide-container').on('mouseleave', 'a.video-preview', function() {
        $('.video-preview-popup').removeClass('show');
        clearTimeout(video_hover_timeout);
    });

    $('.video-slide-container').on('mouseenter', 'a.video-preview, a.next-top-videos', dt.watched_or_not)
                        .on('mouseleave', 'a.video-preview, a.next-top-videos', dt.cancel_watched);
    $('a.slide').on('mouseenter', dt.watched_or_not)
                .on('mouseleave', dt.cancel_watched);


    $('.search-scope').click(function() {
        if ($(this).hasClass('active')) return;

        $(this).siblings('.search-scope.active').removeClass('active');
        $(this).addClass('active');
        var column = $(this).parent().parent();
        column.find('.video-slide-container').addClass('hidden');
        column.find('.video-slide-container[data-order='+$(this).text()+']').removeClass('hidden').trigger('show');
    });

    $('.refresh-button').click(function() {
        var column = $(this).parent().parent();
        column.find('.video-slide-container').not('.hidden').trigger('refresh');
    });

    $('.video-column .video-slide-container').each(function() {
        var slide_container = $(this)[0];
        var column = $(this).parent().parent();
        var lines = slide_container.getAttribute('data-lines');
        var load_over, video_columns;
        var initial = true;

        var left_arrow = column.find('.horizontal-page-roll.left');
        var right_arrow = column.find('.horizontal-page-roll.right');

        var url, params;
        if (slide_container.getAttribute('data-id')) {
            url = '/uper_videos';
            var uper_id = slide_container.getAttribute('data-id');
            params = {user_id: uper_id};
        } else {
            url = '/category_videos';
            var category = slide_container.getAttribute('data-category');
            var subcategory = slide_container.getAttribute('data-subcategory');
            var order = slide_container.getAttribute('data-order');
            params = {category: category, subcategory: subcategory, order: order};
        }

        function load_video_column() {
            dt.loadNextPage(url, {key: params, more: {page_size: lines*page_columns}}, function() {
                if (initial) {
                    var lists = $(slide_container).find('.video-list-line');
                    for (var i = 1; i < lists.length; i++) {
                        $(lists[i]).remove();
                    }
                    $(lists[0]).empty();
                    video_columns = 0;
                    load_over = false;
                    slide_container.setAttribute('data-offset', 0);
                    slide_container.style.WebkitTransform = "translateX(-0px)";
                    slide_container.style.msTransform = "translateX(-0px)";
                    slide_container.style.transform = "translateX(-0px)";

                    $(slide_container).find('.video-list-line').append('<div class="video-list-load loading"></div>')
                }
            }, function(result, isOver) {
                // console.log(result)
                if (initial) {
                    initial = false;
                    $('.video-list-load').remove();
                    if (result.videos.length == 0) {
                        $(slide_container).find('.video-list-line').append('<div class="line-empty">No videos found.</div>')
                    } else {
                        lines = Math.ceil(result.videos.length/page_columns);
                        for (var i = 1; i < lines; i++) {
                            $(slide_container).append('<div class="video-list-line"></div>')
                        }
                    }
                }

                load_over = isOver;
                video_columns += Math.ceil(result.videos.length/lines);
                for (var i = 0; i < result.videos.length; i++) {
                    var video = result.videos[i];
                    var div = '<a class="video-preview" target="_blank" href="' + video.url + '" data-id="' + video.id + '">\
                                    <div class="video-preview-thumbnail">\
                                        <img src="' + video.thumbnail_url + '">\
                                    </div>\
                                    <div class="video-preview-statistic">\
                                        <div class="video-preview-title">' + dt.escapeHTML(video.title) + '</div>\
                                        <div class="video-preview-hits"><span class="preview-icon views"></span>' + dt.numberWithCommas(video.hits) + '</div>\
                                        <div class="video-preview-comment-num"><span class="preview-icon comment"></span>' + dt.numberWithCommas(video.comment_counter) + '</div>\
                                    </div>\
                                    <div class="video-preview-popup-info hidden" data-type="intro">' + video.intro + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="hits">' + dt.numberWithCommas(video.hits) + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="likes">' + dt.numberWithCommas(video.likes) + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="comments">' + dt.numberWithCommas(video.comment_counter) + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="bullets">' + dt.numberWithCommas(video.bullets) + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="duration">' + dt.secondsToTime(video.duration) + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="nickname">' + video.uploader.nickname + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="avatar">' + video.uploader.avatar_url_small + '</div>\
                                    <div class="video-preview-popup-info hidden" data-type="created">' + video.created + '</div>\
                                </a>'
                    $(slide_container).find('.video-list-line:eq('+Math.floor(i/page_columns)+')').append(div);
                }

                var x = parseInt(slide_container.getAttribute('data-offset'));
                if (x >= (video_columns/page_columns - 1)*page_width && load_over) right_arrow.addClass('hidden');
                else right_arrow.removeClass('hidden');
            }, function() {
                if (initial) {
                    $('.video-list-load').remove();
                    $(slide_container).find('.video-list-line').append('<div class="line-empty">Load error</div>');
                }
            });
        }

        function check_arrow_display() {
            var x = parseInt(slide_container.getAttribute('data-offset'));
            if (x <= 0) left_arrow.addClass('hidden');
            else left_arrow.removeClass('hidden');
            
            if (load_over) {
                if (x >= (video_columns/page_columns - 1)*page_width) right_arrow.addClass('hidden');
                else right_arrow.removeClass('hidden');
            } else {
                if (x > (video_columns/page_columns - 1)*page_width) {
                    load_video_column();
                    right_arrow.addClass('hidden');
                } else right_arrow.removeClass('hidden');
            }
        }

        right_arrow.add(left_arrow).click(function() {
            if ($(slide_container).hasClass('hidden')) return;

            var x = parseInt(slide_container.getAttribute('data-offset'));
            if ($(this).hasClass('left')) {
                x = Math.max(0, x - page_width);
            } else {// right
                if (load_over) {
                    x = Math.min((video_columns/page_columns - 1)*page_width, x + page_width);
                } else {
                    x = Math.min(video_columns/page_columns*page_width, x + page_width);
                }
            }
            slide_container.setAttribute('data-offset', x);
            slide_container.style.WebkitTransform = "translateX(-"+x+"px)";
            slide_container.style.msTransform = "translateX(-"+x+"px)";
            slide_container.style.transform = "translateX(-"+x+"px)";

            check_arrow_display();
        });

        $(window).resize(function() {
            if ($(slide_container).hasClass('hidden')) return;

            check_arrow_display();
        });

        $(slide_container).on('refresh', function() {
            initial = true;
            dt.resetLoad(url, params);
            load_video_column();
        });

        $(slide_container).on('show', function() {
            if (initial) load_video_column();
        });

        function detectReach() {
            if ($(window).scrollTop() >= $(slide_container).offset().top - 40 - $(window).height()) {
                $(window).off('scroll', detectReach);
                if (!$(slide_container).hasClass('hidden'))
                    $(slide_container).trigger('show');
            }
        }
        $(window).scroll(detectReach);
        detectReach();
    });

    $('.ranking-and-topic .video-slide-container').each(function() {
        var slide_container = $(this)[0];
        var column = $(this).parent().parent();
        var lines = $(slide_container).find('.video-list-line').length;
        var load_over = false;
        var video_columns = 2 + Math.ceil($(slide_container).find('.next-top-videos').length/lines);
        slide_container.setAttribute('data-offset', 0);

        var left_arrow = column.find('.horizontal-page-roll.left');
        var right_arrow = column.find('.horizontal-page-roll.right');

        var category = slide_container.getAttribute('data-category');
        var subcategory = slide_container.getAttribute('data-subcategory');
        var order = slide_container.getAttribute('data-order');
        var cursor = slide_container.getAttribute('data-cursor');
        
        var url = '/category_videos';
        var params = {category: category, subcategory: subcategory, order: order};
        dt.setCursor(url, params, cursor);
        if (!cursor) {
            load_over = true;
        }

        function load_video_column() {
            dt.loadNextPage(url, {key: params, more: {page_size: lines*page_columns}}, function() {
            }, function(result, isOver) {
                load_over = isOver;
                video_columns += Math.ceil(result.videos.length/lines);
                for (var i = 0; i < result.videos.length; i++) {
                    var video = result.videos[i];
                    var div = '<a class="next-top-videos" target="_blank" href="'+video.url+'" data-id="'+video.id+'">\
                                    <div class="hover-cover">\
                                        <div class="cover-title">'+dt.escapeHTML(video.title)+'</div>\
                                        <div class="cover-uploader">Uper:'+video.uploader.nickname+'</div>\
                                        <div class="cover-hits">Views:'+dt.numberWithCommas(video.hits)+'</div>\
                                    </div>\
                                    <img src="'+video.thumbnail_url+'">\
                                </a>'
                    $(slide_container).find('.video-list-line:eq('+i%lines+')').append(div);
                }

                var x = parseInt(slide_container.getAttribute('data-offset'));
                if (x >= (video_columns/page_columns - 1)*page_width && load_over) right_arrow.addClass('hidden');
                else right_arrow.removeClass('hidden');
            }, function() {
            });
        }

        function check_arrow_display() {
            var x = parseInt(slide_container.getAttribute('data-offset'));
            if (x <= 0) left_arrow.addClass('hidden');
            else left_arrow.removeClass('hidden');
            
            if (load_over) {
                if (x >= (video_columns/page_columns - 1)*page_width) right_arrow.addClass('hidden');
                else right_arrow.removeClass('hidden');
            } else {
                if (x > (video_columns/page_columns - 1)*page_width) {
                    load_video_column();
                    right_arrow.addClass('hidden');
                } else right_arrow.removeClass('hidden');
            }
        }

        right_arrow.add(left_arrow).click(function() {
            var x = parseInt(slide_container.getAttribute('data-offset'));
            if ($(this).hasClass('left')) {
                x = Math.max(0, x - page_width);
            } else {// right
                if (load_over) {
                    x = Math.min((video_columns/page_columns - 1)*page_width, x + page_width);
                } else {
                    x = Math.min(video_columns/page_columns*page_width, x + page_width);
                }
            }
            slide_container.setAttribute('data-offset', x);
            slide_container.style.WebkitTransform = "translateX(-"+x+"px)";
            slide_container.style.msTransform = "translateX(-"+x+"px)";
            slide_container.style.transform = "translateX(-"+x+"px)";

            check_arrow_display();
        });

        $(window).resize(check_arrow_display);
        check_arrow_display();
    });
});
//end of the file
} (dt, jQuery));
