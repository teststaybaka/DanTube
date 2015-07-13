(function(dt, $) {
$(document).ready(function() {
    $('.list-selected').each(function() {
        var first_option = $($(this).prev().children()[0]);
        if (first_option.length > 0) {
            load_danmaku_list(first_option);
            $('.inline-button.drop').removeClass('disabled');
        }
    });
    $('.pools-block').on('click', '.single-checkbox', function() {
        $(this).toggleClass('checked');
        if ($(this).hasClass('all')) {
            if ($(this).hasClass('checked')) {
                $('.single-checkbox').addClass('checked');
            } else {
                $('.single-checkbox').removeClass('checked');
            }
        }

        if ($('.single-checkbox.checked').length > 0) {
            $('.inline-button.delete').removeClass('disabled');
        } else {
            $('.inline-button.delete').addClass('disabled');
        }
    });

    $('.list-option').click(function() {
        load_danmaku_list($(this));
    });
    $('.inline-button.drop').click(function() {
        if ($(this).hasClass('disabled')) return;
        drop_danmaku_pool($('.list-option.active'));
    });
    $('.inline-button.delete').click(function() {
        if ($(this).hasClass('disabled')) return;
        delete_danmaku($('.list-option.active'));
    });
});

function load_danmaku_list(option) {
    $('.inline-button.delete').addClass('disabled');
    var list_block = $('.pools-block');
    list_block.empty();
    list_block.append('<div class="pool-detail-list loading"></div>');
    $.ajax({
        type: "POST",
        url: window.location.href,
        data: {pool_index: option.attr('data-index'), pool_type: option.attr('data-type')},
        success: function(result) {
            list_block.empty();
            if (!result.error) {
                if (option.attr('data-type') === 'danmaku') {
                    list_block.append('<div class="pool-detail-entry label-line">\
                        <div class="detail-label timestamp">Timestamp</div>\
                        <div class="detail-label">Type</div>\
                        <div class="detail-label color">Color</div>\
                        <div class="detail-label">Font size</div>\
                        <div class="detail-label content">Content</div>\
                        <div class="detail-label created">Created</div>\
                        <div class="single-checkbox inline all"></div>\
                    </div>');
                    for (var i = 0; i < result.danmaku_list.length; i++) {
                        list_block.append(render_danmaku_entry(result.danmaku_list[i], i));
                    }
                    $('.danmaku-num-label').text(result.danmaku_list.length+'/1000');
                } else if (option.attr('data-type') === 'advanced') {
                    list_block.append('<div class="pool-detail-entry label-line">\
                        <div class="detail-label timestamp">Timestamp</div>\
                        <div class="detail-label">Type</div>\
                        <div class="detail-label content advanced">Content</div>\
                        <div class="detail-label created">Created</div>\
                        <div class="single-checkbox inline all"></div>\
                    </div>');
                    for (var i = 0; i < result.danmaku_list.length; i++) {
                        list_block.append(render_advanced_entry(result.danmaku_list[i], i));
                    }
                    $('.danmaku-num-label').text(result.danmaku_list.length+'/1000');
                } else if (option.attr('data-type') === 'subtitles') {
                    list_block.append('<div class="pool-detail-entry label-line">\
                        <div class="detail-label timestamp">Timestamp</div>\
                        <div class="detail-label">Type</div>\
                        <div class="detail-label content subtitles">Content</div>\
                        <div class="detail-label created">Created</div>\
                    </div>');
                    var subtitles_list = [];
                    var lines = result.subtitles_list.subtitles.split('\n');
                    for (var i = 0; i < lines.length; i++) {
                        var line = lines[i].trim();
                        if (line) {
                            var matched = line.match(dt.subtitle_format);
                            if (matched[4]) {
                                subtitles_list.push({
                                    'timestamp': parseInt(matched[1])*60+parseInt(matched[2])+parseInt(matched[3])/100,
                                    'content': matched[4],
                                });
                            }
                        }
                    }
                    for (var i = 0; i < subtitles_list.length; i++) {
                        list_block.append(render_subtitles_entry(subtitles_list[i], result.subtitles_list.created_year));
                    }
                    $('.danmaku-num-label').text(subtitles_list.length);
                }
            } else {
                list_block.append('<div class="content-entry none">Load error.</div>');
                dt.pop_ajax_message(result.message, 'error');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            list_block.empty();
            list_block.append('<div class="content-entry none">Empty list.</div>');
            dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
        }
    });
}

function render_danmaku_entry(entry, index) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label timestamp">'+dt.millisecondsToTime(entry.timestamp)+'</div>\
                <div class="detail-label">'+entry.type+'</div>\
                <div class="detail-label color"><div class="color-box" style="background-color: '+dt.dec2hexColor(entry.color)+';"></div></div>\
                <div class="detail-label">'+entry.size+'</div>\
                <div class="detail-label content" title="'+entry.content+'">'+entry.content+'</div>\
                <div class="detail-label created">'+entry.created_year+'</div>\
                <div class="single-checkbox inline" data-index="'+index+'"></div>\
            </div>'
    return div;
}

function render_advanced_entry(entry, index) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label timestamp">'+dt.millisecondsToTime(entry.timestamp)+'</div>\
                <div class="detail-label">Advanced</div>\
                <div class="detail-label content advanced" title="'+entry.content+'">'+entry.content+'</div>\
                <div class="detail-label created">'+entry.created_year+'</div>\
                <div class="single-checkbox inline" data-index="'+index+'"></div>\
            </div>'
    return div;
}

function render_subtitles_entry(entry, created_year) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label timestamp">'+dt.millisecondsToTime(entry.timestamp)+'</div>\
                <div class="detail-label">Subtitles</div>\
                <div class="detail-label content subtitles" title="'+entry.content+'">'+entry.content+'</div>\
                <div class="detail-label created">'+created_year+'</div>\
            </div>'
    return div;
}

function drop_danmaku_pool(option) {
    var url_suffix = window.location.href.split('/').last();
    $.ajax({
        type: "POST",
        url: '/account/video/parts/danmaku/drop/'+url_suffix,
        data: {pool_index: option.attr('data-index'), pool_type: option.attr('data-type')},
        success: function(result) {
            if (!result.error) {
                window.location.reload();
            } else {
                dt.pop_ajax_message(result.message, 'error');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
        }
    });
}

function delete_danmaku(option) {
    $('.inline-button.delete').addClass('disabled');
    var url_suffix = window.location.href.split('/').last();
    indices = []
    var checkboxes = $('.single-checkbox.checked');
    for (var i = 0; i < checkboxes.length; i++) {
        if ($(checkboxes[i]).hasClass('all')) continue;
        indices.push($(checkboxes[i]).attr('data-index'));
    }
    $.ajax({
        type: "POST",
        url: '/account/video/parts/danmaku/delete/'+url_suffix,
        data: {pool_index: option.attr('data-index'), pool_type: option.attr('data-type'), danmaku_index: indices},
        success: function(result) {
            if (!result.error) {
                load_danmaku_list(option);
                dt.pop_ajax_message('Danmaku deleted!', 'success');
            } else {
                dt.pop_ajax_message(result.message, 'error');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
        }
    });
}
} (dt, jQuery));