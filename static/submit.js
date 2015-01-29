function title_check() {
    var title = $('#video-title').val().trim();
    if (!title) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Please enter a title for your video');
        $('#video-title').addClass('error');
        return false;
    } else if (title.length > 40) {
        $('#video-title-error').addClass('show');
        $('#video-title-error').text('Video title can\'t exceed 40 characters.');
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
    } else if (tags.length > 30) {
        $('#video-tags-error').addClass('show');
        $('#video-tags-error').text('You can add at most 30 tags.');
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

function resizeAndUpload(url, dataURL) {
    var canvas = document.getElementById("crop-canvas");
    var ctx = canvas.getContext("2d");
    var img = document.getElementById("thumbnail-preview-img");
    ctx.drawImage(img, 0, 0, 320, 180);
    var dataURL = canvas.toDataURL('image/png');
}

function thumbnail_change() {
    var file = document.getElementById("thumbnail-input").files[0];
    if (file) {
        if (file.size <= 0) {
            $('#thumbnail-error').addClass('show');
            $('#thumbnail-error').text('Invalid file.')
        } else if (file.size > 50*1024*1024) {
            $('#thumbnail-error').addClass('show');
            $('#thumbnail-error').text('Please select an image smaller than 50MB.');
        } else {
            var types = file.type.split('/');
            // console.log
            if (types[0] != 'image') {
                $('#thumbnail-error').addClass('show');
                $('#thumbnail-error').text('Please select an image file.');
            } else {
                $('#thumbnail-error').removeClass('show');

                if (!$('#thumbnail-preview-img').length) {
                    $('#thumbnail-preview').append('<img id="thumbnail-preview-img">');
                }

                console.log('file size:'+file.size);
                console.log('file type:'+file.type);
                var reader = new FileReader();
                reader.onload = function(e) {
                    $('#thumbnail-preview-img').attr('src', e.target.result);
                }
                reader.readAsDataURL(file);
            }
        }
    } else {
        $('#thumbnail-preview-img').remove();
        $('#thumbnail-error').removeClass('show');
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

    $('#video-submission-form').submit(function() {
        $('#save-change-message').remove();
        $('#thumbnail-error').removeClass('show');

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
            return false;
        }

        $.ajax({
            type: "POST",
            url: "/submit",
            data: $('#video-submission-form').serialize(),
            success: function(result) {
                console.log(result);
                if(result.error) {
                    if (result.message === 'invalid url') {
                        $('#video-url-error').addClass('show');
                        $('#video-url-error').text('Video url invalid.');
                        $('#video-url').addClass('error');
                    } else {
                        $('input.save_change-button').after('<div id="save-change-message" class="fail show">'+result.message+'</div>');
                    }
                    button.disabled = false;
                } else {
                    $('input.save_change-button').after('<div id="save-change-message" class="success show">Video submitted successfully!</div>');
                    setTimeout(function(){
                        window.location.replace('/account/video'); 
                    }, 1500);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
            }
        });
        return false;
    });  
});
