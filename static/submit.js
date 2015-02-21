video_part_line_html = '<div class="video-part-line">\
            <div class="video-part-error">Title too long.</div>\
            <input type="text" class="title-input" placeholder="Optional" name="sub-title[]">\
            <div class="video-part-error">Title too long.</div>\
            <textarea class="intro-input" placeholder="Optional" name="sub-intro[]"></textarea>\
            <select class="source-select">\
                <option>YouTube</option>\
            </select>\
            <div class="video-part-error">Title too long.</div>\
            <input type="text" class="url-input" name="video-url[]" placeholder="e,g., youtube.com/watch?v=8NNTvx5eoXE">\
            <div class="video-part-delete"></div>\
        </div>'

function title_check() {
    var title = $('#video-total-title').val().trim();
    if (!title) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Please enter a title for your video');
        $('#video-total-title').addClass('error');
        return false;
    } else if (title.length > 100) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Video title can\'t exceed 100 characters.');
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
    if (title.length > 100) {
        error.addClass('show');
        error.text('No longer than 100 characters.');
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
        if (tags_ori[i].trim() != '') {
            tags.push(tags_ori[i].trim());
        }
    }
    
    if (tags.length === 0) {
        $('#video-tags-error').addClass('show');
        $('#video-tags-error').text('Please add at least one tag.');
        $('#video-tags').addClass('error');
        return false;
    } else if (tags.length > 20) {
        $('#video-tags-error').addClass('show');
        $('#video-tags-error').text('You can add at most 20 tags.');
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
    $('#select-category').change(function() {
        var subcategory = video_subcategories[$(this).val()];
        $('#select-subcategory').empty();
        for(var i = 0; i < subcategory.length; i++) {
            $('#select-subcategory').append('<option value="' + subcategory[i] + '">' + subcategory[i] + '</option>');
        }
    });

    $('div.option-button.type').click(function(evt) {
        $('div.option-button.type').removeClass('select');
        $(evt.target).addClass('select');
        if (evt.target.id === 'self-made-option') {
            $('#video-type-option').val('self-made');
        } else {//republish
            $('#video-type-option').val('republish');
        }
    });

    $('#video-total-title').focusout(title_check);
    $('#video-description').focusout(descript_check);
    $('#video-tags').focusout(video_tag_check);
    document.getElementById('thumbnail-input').addEventListener("change", thumbnail_change);

    $('a.add-more').click(function(evt) {
        $('div.add-more-link').before(video_part_line_html);
        $('div.input-error.add-more').removeClass('show');
    });
    $('form').on('click', 'div.video-part-delete', function(evt) {
        $(evt.target).parent().remove();
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
        $('#change-applying').addClass('show');

        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        var error = false;
        if (!title_check()) {
            error = true;
        }
        if (!descript_check()) {
            error = true;
        }
        if (!video_tag_check()) {
            error = true;
        }
        var subtitles = document.querySelectorAll('input.title-input');
        if (subtitles.length == 0) {
            error = true;
            $('div.input-error.add-more').addClass('show');
            $('div.input-error.add-more').text('Please add at least one video.');
        }
        for (var i = 0; i < subtitles.length; i++) {
            if (!sub_title_check(subtitles[i])) {
                error = true;
            }
        }
        var subintros = document.querySelectorAll('textarea.intro-input');
        for (var i = 0; i < subintros.length; i++) {
            if (!sub_intro_check(subintros[i])) {
                error = true;
            }
        }
        var urls = document.querySelectorAll('input.url-input');
        for (var i = 0; i < urls.length; i++) {
            if (!url_check(urls[i])) {
                error = true;
            }
        }
        if (error) {
            button.disabled = false;
            $('#change-applying').removeClass('show');
            return false;
        }

        var formData = new FormData(document.getElementById('video-submission-form'));
        $.ajax({
            type: "POST",
            url: evt.target.action,
            // data: $('#video-submission-form').serialize(),
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            success: function(result) {
                console.log(result);
                if(result.error) {
                    if (result.message === 'invalid url') {
                        var error = $('input.url-input:eq('+result.index+')').prev();
                        error.addClass('show');
                        error.text('Video url invalid.');
                        $('input.url-input:eq('+result.index+')').addClass('error');
                    } else {
                        pop_ajax_message(result.message, 'error');
                    }
                    button.disabled = false;
                } else {
                    pop_ajax_message(result.message, 'success');
                    setTimeout(function(){
                        window.location.replace('/account/video'); 
                    }, 3000);
                }
                $('#change-applying').removeClass('show');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').removeClass('show');
            }
        });
        return false;
    });  
});
