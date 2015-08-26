(function(dt, $) {
$(document).ready(function() {
    $('.upers-block').each(function() {
        var upers_lines = 0;
        var page_lines = 5;
        var line_size = 2;
        var up_margin = 15;
        var uper_page_over = false;
        var slide_container = $('.upers-block')[0];

        function loadNextUpers() {
            dt.loadNextPage('/account/subscribed', {}, function() {
                $('.upers-block').append('<div class="quick-uper loading"></div>');
            }, function(result, isOver) {
                $('.quick-uper.loading').remove();
                uper_page_over = isOver;
                upers_lines += Math.ceil(result.upers.length/line_size);

                var div = '';
                for (var i = 0; i < result.upers.length; i++) {
                    var uper = result.upers[i];
                    div += '<div class="quick-uper">\
                                <a href="' + uper.space_url + '" class="user-img" title="' + uper.nickname + '" target="_blank">\
                                    <img src="' + uper.avatar_url_small + '">\
                                </a>\
                            </div>'
                }

                if (div === '') {
                    if ($('.quick-uper').length == 0) {
                        div = '<div class="quick-uper none">You haven\'t subscribed to anyone.</div>'
                    }
                }
                $('.upers-block').append(div);

                var height = $('.uper-page-container').height() - up_margin;
                var y = parseInt(slide_container.getAttribute('data-offset'));
                if (y >= (upers_lines/page_lines - 1)*height && uper_page_over) $('.uper-page-arrow.down').addClass('hidden');
                else $('.uper-page-arrow.down').removeClass('hidden');
            }, function() {
                $('.quick-uper.loading').remove();
            });
        }
        loadNextUpers();

        $('.uper-page-arrow').click(function() {
            var height = $('.uper-page-container').height() - up_margin;
            var y = parseInt(slide_container.getAttribute('data-offset'));
            if ($(this).hasClass('up')) {
                y = Math.max(0, y - height);
            } else {// down
                if (uper_page_over) {
                    y = Math.min((upers_lines/page_lines - 1)*height, y + height);
                } else {
                    y = Math.min(upers_lines/page_lines*height, y + height);
                }
            }

            if (y <= 0) $('.uper-page-arrow.up').addClass('hidden');
            else $('.uper-page-arrow.up').removeClass('hidden');

            if (uper_page_over) {
                if (y >= (upers_lines/page_lines - 1)*height) $('.uper-page-arrow.down').addClass('hidden');
                else $('.uper-page-arrow.down').removeClass('hidden');
            } else {
                if (y > (upers_lines/page_lines - 1)*height) {
                    loadNextUpers();
                    $('.uper-page-arrow.down').addClass('hidden');
                } else $('.uper-page-arrow.down').removeClass('hidden');
            }

            slide_container.setAttribute('data-offset', y);
            slide_container.style.WebkitTransform = "translateY(-"+y+"px)";
            slide_container.style.msTransform = "translateY(-"+y+"px)";
            slide_container.style.transform = "translateY(-"+y+"px)";
        });
    });

    var type = dt.getParameterByName('type');
    dt.scrollUpdate('/account/subscriptions', {type: type}, 'content-entry', $('.activity-container'), function(result) {
        var div = '';
        if (result.type == 'comments') {
            for (var i = 0; i < result.entries.length; i++) {
                var comment = result.entries[i];
                div += '<div class="content-entry">\
                            <a class="uploader-img" href="' + comment.creator.space_url + '" target="_blank">\
                                <img class="uploader-img" src="' + comment.creator.avatar_url_small + '">\
                            </a>\
                            <div class="activity-detail">\
                                <div class="activity-title normal-link">\
                                    <label>'
                                    if (comment.inner_floorth) {
                                        div += 'Replied a comment in'
                                    } else {
                                        div += 'Posted a comment in'
                                    }
                                    div += '</label>\
                                    <a href="' + comment.video.url + '" class="activity-title normal-link" target="_blank">' + comment.video.title + '</a>\
                                </div>\
                                <div class="uploader-name">\
                                    <label>by</label>\
                                    <a href="' + comment.creator.space_url + '" class="uploader-name blue-link" target="_blank">' + comment.creator.nickname + '</a>\
                                    <div class="activity-time">' + comment.created + '</div>\
                                </div>\
                                <div class="activity-intro">' + comment.content + '</div>\
                                <a class="comment-check blue-link" href="' + comment.video.url + '?comment=' + comment.floorth
                                if (comment.inner_floorth) {
                                    div +=  '&reply=' + comment.inner_floorth;
                                }
                                div += '" target="_blank">[Check it out]</a>\
                            </div>\
                        </div>'
            }
        } else {
            for (var i = 0; i < result.entries.length; i++) {
                var video = result.entries[i];
                div += '<div class="content-entry">\
                            <a class="uploader-img" href="' + video.uploader.space_url + '" target="_blank">\
                                <img class="uploader-img" src="' + video.uploader.avatar_url_small + '">\
                            </a>\
                            <div class="activity-detail">\
                                <div class="activity-title normal-link">\
                                    <label>Uploaded</label>\
                                    <a href="' + video.url + '" class="activity-title normal-link" target="_blank">' + video.title + '</a>\
                                </div>\
                                <div class="uploader-name">\
                                    <label>by</label>\
                                    <a href="' + video.uploader.space_url + '" class="uploader-name blue-link" target="_blank">' + video.uploader.nickname + '</a>\
                                    <div class="activity-time">' + video.created + '</div>\
                                </div>\
                                <div class="activity-intro">' + video.intro + '</div>\
                                <a class="video-img" href="' + video.url + '" target="_blank">\
                                    <img src="' + video.thumbnail_url + '">\
                                </a>\
                            </div>\
                        </div>'
            }
        }
        return div;
    });
});
//end of the file
} (dt, jQuery));
