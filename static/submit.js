(function(dt, $) {
video_part_line_html = '<div class="video-part-line">\
            <div class="video-part-drag-wrapper" ondragstart="return false;" ondrop="return false;">\
                <div class="video-part-error">Title too long.</div>\
                <input type="text" class="title-input normal-input" placeholder="Optional title" name="sub-title[]" tabindex="1">\
                <div class="video-part-error">Title too long.</div>\
                <textarea class="intro-input normal-input" placeholder="Optional sub-introduction" name="sub-intro[]" tabindex="1"></textarea>\
                <div class="list-select source">\
                    <div class="list-selection down hidden">\
                        <div class="list-option medium active">YouTube</div>\
                    </div>\
                    <div class="list-selected medium">YouTube</div>\
                    <input name="source[]" type="text" class="hidden" value="YouTube">\
                </div>\
                <div class="video-part-error">Title too long.</div>\
                <input type="text" class="url-input normal-input" name="video-url[]" placeholder="e.g., youtube.com/watch?v=8NNTvx5eoXE" tabindex="1">\
                <div class="video-part-delete" title="Remove"></div>\
                <input class="hidden" type="text" name="index[]" value="-1">\
            </div>\
        </div>';

function title_check() {
    var title = $('#video-total-title').val().trim();
    if (!title) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Please enter a title for your video');
        $('#video-total-title').addClass('error');
        return false;
    } else if (dt.puncts.test(title)) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Video title contains illegal characters.');
        $('#video-total-title').addClass('error');
        return false;
    } else if (title.length > 400) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Video title can\'t exceed 400 characters.');
        $('#video-total-title').addClass('error');
        return false;
    } else {
        $('#video-title-error').removeClass('show');
        $('#video-total-title').removeClass('error');
        return true;
    }
}

function sub_title_check(target) {
    var title = $(target).val().trim();
    var error = $(target).prev();
    if (dt.puncts.test(title)) {
        error.addClass('show');
        error.text('Illegal characters.');
        $(target).addClass('error');
        return false;
    } else if (title.length > 400) {
        error.addClass('show');
        error.text('No longer than 400 characters.');
        $(target).addClass('error');
        return false;
    } else {
        error.removeClass('show');
        $(target).removeClass('error');
        return true;
    }
}

function descript_check() {
    var descrip = $('#video-description').val().trim();
    if (!descrip) {
        $('#video-description-error').addClass('show');
        $('#video-description-error').text('Please write something for your video.');
        $('#video-description').addClass('error');
        return false;
    } else if (descrip.length > 2000) {
        $('#video-description-error').addClass('show');
        $('#video-description-error').text('Description can\'t exceed 2000 characters.');
        $('#video-description').addClass('error');
        return false;
    } else {
        $('#video-description-error').removeClass('show');
        $('#video-description').removeClass('error');
        return true;
    }
}

function sub_intro_check(target) {
    var intro = $(target).val().trim();
    var error = $(target).prev();
    if (intro.length > 2000) {
        error.addClass('show');
        error.text('No longer than 2000 characters.');
        $(target).addClass('error');
        return false;
    } else {
        error.removeClass('show');
        $(target).removeClass('error');
        return true;
    }
}

function video_tag_check() {
    var tags_ori = $('#video-tags').val().split(',');
    var tags = []
    for (var i = 0; i < tags_ori.length; i++) {
        tag = tags_ori[i].trim()
        if (tag != '') {
            if (tag.length > 100) {
                $('#video-tags-error').addClass('show');
                $('#video-tags-error').text('All tags must be no longer than 100 characters.');
                $('#video-tags').addClass('error');
                return false;
            } else if (dt.puncts.test(tag)) {
                $('#video-tags-error').addClass('show');
                $('#video-tags-error').text('Tags contain illegal characters.');
                $('#video-tags').addClass('error');
                return false;
            }
            tags.push(tag);
        }
    }
    
    if (tags.length === 0) {
        $('#video-tags-error').addClass('show');
        $('#video-tags-error').text('Please add at least one tag.');
        $('#video-tags').addClass('error');
        return false;
    } else if (tags.length > 10) {
        $('#video-tags-error').addClass('show');
        $('#video-tags-error').text('You can add at most 10 tags.');
        $('#video-tags').addClass('error');
        return false;
    } else {
        $('#video-tags-error').removeClass('show');
        $('#video-tags').removeClass('error');
        return true;
    }
}

function thumbnail_change() {
    var file = document.getElementById("thumbnail-input").files[0];
    $('img.thumbnail-preview-img').remove();
    if (file) {
        if (file.size <= 0) {
            $('#thumbnail-error').addClass('show');
            $('#thumbnail-error').text('Invalid file.')
            $('#thumbnail-input').val('')
        } else if (file.size > 50*1024*1024) {
            $('#thumbnail-error').addClass('show');
            $('#thumbnail-error').text('Please select an image smaller than 50MB.');
            $('#thumbnail-input').val('')
        } else {
            var types = file.type.split('/');
            // console.log
            if (types[0] != 'image') {
                $('#thumbnail-error').addClass('show');
                $('#thumbnail-error').text('Please select an image file.');
                $('#thumbnail-input').val('')
            } else {
                $('#thumbnail-error').removeClass('show');
                $('#thumbnail-preview').append('<img class="thumbnail-preview-img">');

                console.log('file size:'+file.size);
                console.log('file type:'+file.type);
                var reader = new FileReader();
                reader.onload = function(e) {
                    $('img.thumbnail-preview-img').attr('src', e.target.result);
                }
                reader.readAsDataURL(file);
            }
        }
    }
}

function url_check(target) {
    var url = $(target).val().trim();
    var error = $(target).prev();
    if (!url) {
        error.addClass('show');
        error.text('Please enter the video source.');
        $(target).addClass('error');
        return false;
    } else {
        error.removeClass('show');
        $(target).removeClass('error');
        return true;
    }
}

$(document).ready(function() {
    $('.list-option.category').click(function() {
        var subcategories = video_subcategories[$(this).text()];
        $('.list-selection.subcategory').empty();
        for (var i = 0; i < subcategories.length; i++) {
            $('.list-selection.subcategory').append('<div class="list-option medium subcategory">'+subcategories[i]+'</div>');
        }
        var first_option = $($('.list-selection.subcategory').children()[0]);
        $('.list-selection.subcategory').next().text(first_option.text())
                                        .next().val(first_option.text());
        first_option.addClass('active');

    });

    $('#video-part-content').mousedown(function(evt) {
        if ($(evt.target).hasClass('video-part-drag-wrapper') && $('div.table-label-line.stealth').length == 0) {
            var label_height = document.getElementById('table-label-line').offsetHeight;
            var link_height = document.getElementById('add-more-link').offsetHeight;
            var video_line_container = document.getElementById('video-part-content');
            var block_height = evt.target.offsetHeight + 1;

            // var targetIndex = $('div.video-part-drag-wrapper').index($(evt.target));
            var float_block = $(evt.target).clone().addClass('float');
            var textarea_content = $(evt.target).children('textarea').val();
            float_block.children('textarea').val(textarea_content);
            // console.log(textarea_content);
            var rect = evt.target.getBoundingClientRect();
            var offset_X = rect.left - evt.clientX;
            var offset_Y = rect.top - evt.clientY;

            $(evt.target).parent().addClass('stealth');
            $('#video-part-content').append(float_block);
            
            float_block[0].style.left = evt.clientX + offset_X + 'px';
            float_block[0].style.top = evt.clientY + offset_Y + 'px';

            document.onmousemove = function(evt) {
                float_block[0].style.left = evt.clientX + offset_X + 'px';
                float_block[0].style.top = evt.clientY + offset_Y + 'px';

                rect = video_line_container.getBoundingClientRect();
                if (evt.clientX < rect.left || evt.clientX > rect.left + video_line_container.offsetWidth) {
                    return;
                }

                var top_Y = rect.top + label_height;
                var y = Math.min(evt.clientY, rect.top + video_line_container.offsetHeight - 1 - link_height);
                var index = Math.floor((y - top_Y)/block_height);
                var total = $('div.video-part-line').length;
                // console.log(y+' '+top_Y+' '+index)
                for (var i = 0; i < index; i++) {
                    var cur_line = $('div.video-part-line:eq('+i+')');
                    var next_line = $('div.video-part-line:eq('+(i+1)+')');
                    if (cur_line.hasClass('stealth') && i+1 < total) {
                        cur_line.empty();
                        cur_line.append(next_line.children().clone());
                        textarea_content = next_line.children().children('textarea').val();
                        cur_line.children().children('textarea').val(textarea_content);
                        next_line.addClass('stealth');
                        cur_line.removeClass('stealth');
                    }
                }
                for (var i = total - 1; i > index; i--) {
                    var cur_line = $('div.video-part-line:eq('+i+')');
                    var next_line = $('div.video-part-line:eq('+(i-1)+')');
                    if (cur_line.hasClass('stealth') && i-1 >= 0) {
                        cur_line.empty();
                        cur_line.append(next_line.children().clone());
                        textarea_content = next_line.children().children('textarea').val();
                        cur_line.children().children('textarea').val(textarea_content);
                        next_line.addClass('stealth');
                        cur_line.removeClass('stealth');
                    }
                }
            }
            document.onmouseup = function(evt) {
                var final_line = $('div.video-part-line.stealth');
                var back_block = float_block.clone().removeClass('float');
                textarea_content = float_block.children('textarea').val();
                back_block.children('textarea').val(textarea_content);
                back_block[0].style.left = 0;
                back_block[0].style.top = 0;
                float_block.remove();
                final_line.empty();
                final_line.append(back_block);
                final_line.removeClass('stealth');

                document.onmousemove = null;
                document.onmouseup = null;
            }
        }
    });

    $('div.option-button.type').click(function(evt) {
        $('div.option-button.type').removeClass('select');
        $(evt.target).addClass('select');
        $('#video-type-option').val($(evt.target).text());
    });

    $('#video-total-title').focusout(title_check);
    $('#video-description').focusout(descript_check);
    $('#video-tags').focusout(video_tag_check);
    $('#thumbnail-input').on("change", thumbnail_change);

    $('a.add-more').click(function(evt) {
        $('#add-more-link').before(video_part_line_html);
        $('div.input-error.add-more').removeClass('show');
    });
    $('form').on('click', 'div.video-part-delete', function(evt) {
        $(evt.target).parent().parent().remove();
    });

    $('form').on('focusout', 'input.title-input', function(evt) {
        sub_title_check(evt.target);
    });
    $('form').on('focusout', 'textarea.intro-input', function(evt) {
        sub_intro_check(evt.target);
    });
    $('form').on('focusout', 'input.url-input', function(evt) {
        url_check(evt.target);
    });

    $('#video-submission-form').submit(function(evt) {
        $('#thumbnail-error').removeClass('show');

        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        var error = !title_check() | !descript_check() | !video_tag_check();
        var subtitles = $('input.title-input');
        if (subtitles.length == 0) {
            error = true;
            $('div.input-error.add-more').addClass('show');
            $('div.input-error.add-more').text('Please add at least one video.');
        }
        for (var i = 0; i < subtitles.length; i++) {
            error |= !sub_title_check(subtitles[i]);
        }
        var subintros = $('textarea.intro-input');
        for (var i = 0; i < subintros.length; i++) {
            error |= !sub_intro_check(subintros[i]);
        }
        var urls = $('input.url-input');
        for (var i = 0; i < urls.length; i++) {
            error |= !url_check(urls[i]);
        }
        if (error) {
            button.disabled = false;
            return false;
        }

        $('#change-applying').removeClass('hidden');
        var formData = new FormData(document.getElementById('video-submission-form'));
        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            timeout: 10000,
            success: function(result) {
                console.log(result);
                if(result.error) {
                    var lineNumber = result.message.match(/invalid url:(\d+)/);
                    if (lineNumber) {
                        var error = $('input.url-input:eq('+lineNumber[1]+')').prev();
                        error.addClass('show');
                        error.text('Video url invalid.');
                        $('input.url-input:eq('+lineNumber[1]+')').addClass('error');
                    } else {
                        dt.pop_ajax_message(result.message, 'error');
                    }
                    button.disabled = false;
                } else {
                    dt.pop_ajax_message('Video submitted successfully!', 'success');
                    setTimeout(function(){
                        window.location.replace('/account/video'); 
                    }, 3000);
                }
                $('#change-applying').addClass('hidden');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').addClass('hidden');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });  
});
//end of the file
} (dt, jQuery));
