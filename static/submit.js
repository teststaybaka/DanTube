function title_check() {
    var title = $('#video-title').val().trim();
    if (!title) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Please enter a title for your video');
        $('#video-title').addClass('error');
        return false;
    } else if (title.length > 100) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Video title can\'t exceed 100 characters.');
        $('#video-title').addClass('error');
        return false;
    } else {
        $('#video-title-error').removeClass('show');
        $('#video-title').removeClass('error');
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
    } else if (tags.length > 15) {
        $('#video-tags-error').addClass('show');
        $('#video-tags-error').text('You can add at most 15 tags.');
        $('#video-tags').addClass('error');
        return false;
    } else {
        $('#video-tags-error').removeClass('show');
        $('#video-tags').removeClass('error');
        return true;
    }
}

function url_check() {
    var url = $('#video-url').val().trim();
    if (!url) {
        $('#video-url-error').addClass('show');
        $('#video-url-error').text('Please enter the url of your video.');
        $('#video-url').addClass('error');
        return false;
    } else {
        $('#video-url-error').removeClass('show');
        $('#video-url').removeClass('error');
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
    })

    $('div.option-button.playlist').click(function(evt) {
        $('div.option-button.playlist').removeClass('select');
        $(evt.target).addClass('select');
        $('div.input-line.hide').removeClass('show');
        if (evt.target.id === "add-to-playlist-option") {
            $('#add-to-playlist-input').addClass('show');
            $('#playlist-option').val('add-to-playlist');
        } else if (evt.target.id === "new-playlist-option") {
            $('#new-playlist-input').addClass('show');
            $('#playlist-option').val('new-playlist');
        } else {//no playlist
            $('#playlist-option').val('no-playlist');
        }
    });

    $('#video-title').focusout(title_check);

    $('#video-description').focusout(descript_check);

    $('#video-tags').focusout(video_tag_check);

    $('#video-url').focusout(url_check);

    document.getElementById('thumbnail-input').addEventListener("change", thumbnail_change);

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
        if (!url_check()) {
            error = true;
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
                        $('#video-url-error').addClass('show');
                        $('#video-url-error').text('Video url invalid.');
                        $('#video-url').addClass('error');
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
