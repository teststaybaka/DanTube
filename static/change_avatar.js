(function(dt, $) {
var crop_width, crop_height;
var orig_width, orig_height;
var crop_coords = {};

function cropImage(src) {
    $('#image-upload-hint').addClass('hidden')
    $('#avatar-crop-canvas').append('<img id="avatar-crop" src="' + src + '">');
    crop_width = $('#avatar-crop').width();
    crop_height = $('#avatar-crop').height();
    crop_coords.x = 0;
    crop_coords.y = 0;
    var l = (crop_width > crop_height) ? crop_height : crop_width;
    crop_coords.w = l;
    crop_coords.h = l;
    showPreview(crop_coords);
        
    $('#avatar-crop').Jcrop({
        onChange: showPreview,
        onSelect: showPreview,
        setSelect: [crop_coords.x, crop_coords.y, crop_coords.x + crop_coords.w, crop_coords.y + crop_coords.h],
        aspectRatio: 1
    });
    $('div.jcrop-holder').css({
        'left': '50%',
        'top': '50%',
        'margin-left': -crop_width/2 + 'px',
        'margin-top': -crop_height/2 + 'px',
        'position': 'absolute'
    });

    $('#avatar-preview-medium, #avatar-preview-medium-round').attr('src', src);
    $('#avatar-preview-small, #avatar-preview-small-round').attr('src', src);   
}

function readImage() {
    var file = document.getElementById("upload-avatar").files[0];
    $('#image-upload-hint').removeClass('hidden');
    $('#avatar-crop').remove();
    $('div.jcrop-holder').remove();
    $('#upload-file-text').val('');
    if (file) {
        if (file.size <= 0) {
            $('#file-error').addClass('show');
            $('#file-error').text('Invalid file.')
            $('#upload-file-text').addClass('error');
            $('#upload-avatar').val('')
        } else if (file.size > 50*1024*1024) {
            $('#file-error').addClass('show');
            $('#file-error').text('Please select an image smaller than 50MB.');
            $('#upload-file-text').addClass('error');
            $('#upload-avatar').val('')
        } else {
            var types = file.type.split('/');
            // console.log
            if (types[0] != 'image') {
                $('#file-error').addClass('show');
                $('#file-error').text('Please select an image file.');
                $('#upload-file-text').addClass('error');
                $('#upload-avatar').val('')
            } else {
                $('#file-error').removeClass('show');
                $('#upload-file-text').removeClass('error');
                
                $('#upload-file-text').val(file.name);
                console.log('file size:'+file.size);
                console.log('file type:'+file.type);
                var reader = new FileReader();
                reader.onload = function(e) {
                    var image = new Image();
                    image.src = e.target.result;

                    image.onload = function() {
                        orig_width = this.width;
                        orig_height = this.height;
                        cropImage(this.src);
                    }
                }
                reader.readAsDataURL(file);
            }
        }
    }
}

function uploadImage(upload_url, image_url) {
    var button = document.querySelector('input.save_change-button');

    var form = document.getElementById('avatar-upload-form');
    var sBoundary = "---------------------------" + Date.now().toString(16);
    var base64Data = image_url.split(',')[1];
    // var binaryData = window.atob(base64Data);
    // var binaryData = decodeBase64(base64Data);
    // var filename = document.getElementById('upload-avatar').files[0].name;
    // var data = '--' + sBoundary + '\r\n' + 
    //     'Content-Disposition: form-data; name="upload-avatar"; filename="' + filename + '"\n' + 
    //     'Content-Type: image/jpeg' + '\r\n\n' + binaryData + '\n' + '--' + sBoundary + '--\r\n';

    // http://stackoverflow.com/questions/6566240/saving-canvas-image-via-javascript-from-safari-5-0-x-to-appengine-blobstore-w
    var arr = ['--' + sBoundary, 'Content-Disposition: form-data; name="upload-avatar"; filename="avatar.png"',
        'Content-Transfer-Encoding: base64', 'Content-Type:  image/png', '', base64Data, '--' + sBoundary + '--'];
    var data = arr.join('\r\n');
    $.ajax({
        type: 'POST',
        url: upload_url,
        headers: {"Content-Type": "multipart\/form-data; boundary=" + sBoundary},
        data: data,
        success: function(result){
            console.log(result);
            if(!result.error) {
                dt.pop_ajax_message('Change applied successfully.', 'success')
                setTimeout(function(){
                    window.location.replace('/account'); 
                }, 3000);
            } else {
                button.disabled = false;
                dt.pop_ajax_message(result.message, 'error');
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            button.disabled = false;
            dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
        }
    });
    // $('#avatar-upload-form').submit();

}

function showPreview(coords) {
    if(coords.w > 0) crop_coords = coords;
    var medium_len = $('#medium-container').width();
    var rx = medium_len / coords.w;
    var ry = medium_len / coords.h;
    $('#avatar-preview-medium, #avatar-preview-medium-round').css({
        width: Math.round(rx * crop_width) + 'px',
        height: Math.round(ry * crop_height) + 'px',
        marginLeft: '-' + Math.round(rx * coords.x) + 'px',
        marginTop: '-' + Math.round(ry * coords.y) + 'px'
    });
    
    var small_len = $('#small-container').width();
    rx = small_len / coords.w;
    ry = small_len / coords.h;
    $('#avatar-preview-small, #avatar-preview-small-round').css({
        width: Math.round(rx * crop_width) + 'px',
        height: Math.round(ry * crop_height) + 'px',
        marginLeft: '-' + Math.round(rx * coords.x) + 'px',
        marginTop: '-' + Math.round(ry * coords.y) + 'px'
    });
}

$(document).ready(function() {
    document.getElementById('upload-avatar').addEventListener("change", readImage);
    $('#avatar-upload-form').submit(function(evt) {
        var file = document.getElementById("upload-avatar").files[0];
        if (file) {
        // if ($('#avatar-crop').length) {
            var button = document.querySelector('input.save_change-button');
            button.disabled = true;
            $('#file-error').removeClass('show');
            $('#upload-file-text').removeClass('error');
            $('#change-applying').removeClass('hidden');

            // var canvas = document.getElementById("crop-canvas");
            // var ctx = canvas.getContext("2d");
            // var img=document.getElementById("avatar-crop");
            var width_ratio = orig_width / crop_width;
            var height_ratio = orig_height / crop_height;
            // ctx.drawImage(img, crop_coords.x * width_ratio,crop_coords.y * height_ratio, 
            //     crop_coords.w * width_ratio, crop_coords.h * height_ratio, 0, 0, 256, 256);
            // var dataURL = canvas.toDataURL('image/png');
            // console.log(dataURL);
            var formData = new FormData(document.getElementById('avatar-upload-form'));
            formData.append('x0', crop_coords.x * width_ratio);
            formData.append('y0', crop_coords.y * height_ratio);
            formData.append('width', crop_coords.w * width_ratio);
            formData.append('height', crop_coords.h * height_ratio);

            $.ajax({
                type: "POST",
                url: "/account/avatar",
                data: formData,
                cache: false,
                contentType: false,
                processData: false,
                success: function(result) {
                    $('#change-applying').addClass('hidden');
                    if (!result.error) {
                        // uploadImage(result.url, dataURL);
                        dt.pop_ajax_message('Change applied successfully!', 'success');
                        setTimeout(function() {
                            window.location.replace('/account'); 
                        }, 1500);
                    } else {
                        dt.pop_ajax_message(result.message, 'error');
                        button.disabled = false;
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    button.disabled = false;
                    $('#change-applying').addClass('hidden');
                    dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                }
            });
        } else {
            $('#file-error').addClass('show');
            // $('#file-error').text('Please select an image.')
            $('#upload-file-text').addClass('error');
        }
        return false;
    });
});
//end of the file
} (dt, jQuery));
