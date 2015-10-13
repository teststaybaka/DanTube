(function(dt, $) {
var danmaku_list;
var advanced_danmaku_list;
var code_danmaku_list;
var subtitles_list;

$(document).ready(function() {
    danmaku_list = JSON.parse($('.danmaku-list.normal').val());
    advanced_danmaku_list = JSON.parse($('.danmaku-list.advanced').val());
    code_danmaku_list = JSON.parse($('.danmaku-list.code').val());
    subtitles_list = JSON.parse($('.danmaku-list.subtitles').val());
    
    $('#account-right-section').on('click', '.single-checkbox', function() {
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

    if ($('.list-option.active').length != 0)
        load_danmaku_list($('.list-option.active'));
    $('.list-option').click(function() {
        load_danmaku_list($(this));
    });
    $('.inline-button.delete').click(delete_danmaku);
    $('.pools-block').on('click', '.detail-label.confirm', confirm_danmaku);
    $('.pools-block').on('click', '.detail-label.expand', expand_danmaku);
});

function load_danmaku_list(option) {
    $('.inline-button.delete').addClass('disabled');
    var list_block = $('.pools-block');
    list_block.empty();
    
    if (option.attr('data-type') === 'danmaku') {
        list_block.append('<div class="pool-detail-entry label-line">\
                                <div class="detail-label timestamp">Timestamp</div>\
                                <div class="detail-label">Type</div>\
                                <div class="detail-label color">Color</div>\
                                <div class="detail-label font-size">Font size</div>\
                                <div class="detail-label content">Content</div>\
                                <div class="detail-label created">Created</div>\
                                <div class="single-checkbox inline all"></div>\
                            </div>');
        for (var i = 0; i < danmaku_list.length; i++) {
            list_block.append(render_danmaku_entry(danmaku_list[i]));
        }
        $('.danmaku-num-label').text(danmaku_list.length);
    } else if (option.attr('data-type') === 'advanced') {
        list_block.append('<div class="pool-detail-entry label-line">\
                                <div class="detail-label timestamp">Timestamp</div>\
                                <div class="detail-label">Type</div>\
                                <div class="detail-label content long">Content</div>\
                                <div class="detail-label created">Created</div>\
                                <div class="single-checkbox inline all"></div>\
                            </div>');
        for (var i = 0; i < advanced_danmaku_list.length; i++) {
            list_block.append(render_advanced_entry(advanced_danmaku_list[i]));
        }
        $('.danmaku-num-label').text(advanced_danmaku_list.length);
    } else if (option.attr('data-type') === 'code') {
        list_block.append('<div class="pool-detail-entry label-line">\
                                <div class="detail-label timestamp">Timestamp</div>\
                                <div class="detail-label">Type</div>\
                                <div class="detail-label content long">Content</div>\
                                <div class="detail-label created">Created</div>\
                                <div class="single-checkbox inline all"></div>\
                            </div>');
        for (var i = 0; i < code_danmaku_list.length; i++) {
            list_block.append(render_code_entry(code_danmaku_list[i]));
        }
        $('.danmaku-num-label').text(code_danmaku_list.length);
    } else {
        list_block.append('<div class="pool-detail-entry label-line">\
                                <div class="detail-label name">Title</div>\
                                <div class="detail-label">Type</div>\
                                <div class="detail-label content long-long">Content</div>\
                                <div class="detail-label created">Created</div>\
                                <div class="single-checkbox inline all"></div>\
                            </div>');
        for (var i = 0; i < subtitles_list.length; i++) {
            list_block.append(render_subtitles_entry(subtitles_list[i]));
        }
        $('.danmaku-num-label').text(subtitles_list.length);
    }
}

function render_danmaku_entry(entry) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label timestamp">'+dt.millisecondsToTime(entry.timestamp)+'</div>\
                <div class="detail-label">'+entry.type+'</div>\
                <div class="detail-label color"><div class="color-box" style="background-color: '+dt.dec2hexColor(entry.color)+';"></div></div>\
                <div class="detail-label font-size">'+entry.size+'</div>\
                <div class="detail-label content" title="'+entry.content+'">'+entry.content+'</div>\
                <div class="detail-label created">'+entry.created_year+'</div>\
                <div class="single-checkbox inline"></div>\
            </div>'
    return div;
}

function render_advanced_entry(entry) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label timestamp">'+dt.millisecondsToTime(entry.timestamp)+'</div>\
                <div class="detail-label">Advanced</div>\
                <div class="detail-label content long'
                if (!entry.approved) {
                    div += ' pending'
                }
                div += '" title="'+entry.content+'">'+entry.content+'</div>'
                if (!entry.approved) {
                    div += '<div class="detail-label confirm blue-link">Confirm</div>'
                }
                div += '<div class="detail-label created">'+entry.created_year+'</div>\
                <div class="single-checkbox inline"></div>\
            </div>'
    return div;
}

function render_subtitles_entry(entry) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label name" title="'+entry.name+'">'+entry.name+'</div>\
                <div class="detail-label">Subtitles</div>\
                <div class="detail-label content subtitles'
                if (!entry.approved) {
                    div += ' pending'
                }
                div += '" title="'+entry.subtitles+'">'+entry.subtitles+'</div>\
                <div class="detail-label expand blue-link">Expand</div>'
                if (!entry.approved) {
                    div += '<div class="detail-label confirm blue-link">Confirm</div>'
                }
                div += '<div class="detail-label created">'+entry.created_year+'</div>\
                <div class="single-checkbox inline"></div>\
            </div>'
    return div;
}

function render_code_entry(entry) {
    div = '<div class="pool-detail-entry">\
                <div class="detail-label timestamp">'+dt.millisecondsToTime(entry.timestamp)+'</div>\
                <div class="detail-label">Code</div>\
                <div class="detail-label content code'
                if (!entry.approved) {
                    div += ' pending'
                }
                div += '" title="'+entry.content+'">'+entry.content+'</div>\
                <div class="detail-label expand blue-link">Expand</div>'
                if (!entry.approved) {
                    div += '<div class="detail-label confirm blue-link">Confirm</div>'
                }
                div += '<div class="detail-label created">'+entry.created_year+'</div>\
                <div class="single-checkbox inline"></div>\
            </div>'
    return div;
}

function delete_danmaku() {
    if ($(this).hasClass('disabled')) return;

    var option = $('.list-option.active');
    $('.inline-button.delete').addClass('disabled');
    var checkboxes = $('.single-checkbox.checked');
    var entries = [];
    var indices = [];
    for (var i = checkboxes.length - 1; i >= 0; i--) {
        if ($(checkboxes[i]).hasClass('all')) continue;
        var entry = $(checkboxes[i]).parent();
        indices.push($('.pool-detail-entry').index(entry) - 1);
        entries.push(entry);
    }

    $.ajax({
        type: "POST",
        url: window.location.pathname+'/delete',
        data: {pool_type: option.attr('data-type'), index: indices},
        success: function(result) {
            if (!result.error) {
                dt.pop_ajax_message('Danmaku deleted!', 'success');
                for (var i = 0; i < entries.length; i++) {
                    entries[i].remove();
                }
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

function confirm_danmaku() {
    var option = $('.list-option.active');
    var entry = $(this).parent();
    var index = $('.pool-detail-entry').index(entry) - 1;
    $(this).siblings('.detail-label.content').removeClass('pending');
    $(this).remove();
    $.ajax({
        type: 'POST',
        url: window.location.pathname+'/confirm',
        data: {pool_type: option.attr('data-type'), index: index},
        success: function(result) {
            if (!result.error) {
                dt.pop_ajax_message('Danmaku confirmed!', 'success');
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

function expand_danmaku() {
    var content = $(this).siblings('.detail-label.content');
    content.addClass('expanded');
    content.height(content[0].scrollHeight);
    $(this).remove();
}
//end of file
} (dt, jQuery));
