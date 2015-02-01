$(document).ready(function() {
    
    var crop_width, crop_height;
    var orig_width, orig_height;
    var crop_coords = {};

    function cropImage(src) {
        $('#image-upload-hint').remove();
        $('#avatar-crop').remove();
        $('div.jcrop-holder').remove();

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
        if (file) {
            if (file.size <= 0) {
                $('#file-error').addClass('show');
                $('#file-error').text('Invalid file.')
                $('#upload-file-text').addClass('error');
            } else if (file.size > 50*1024*1024) {
                $('#file-error').addClass('show');
                $('#file-error').text('Please select an image smaller than 50MB.');
                $('#upload-file-text').addClass('error');
            } else {
                var types = file.type.split('/');
                // console.log
                if (types[0] != 'image') {
                    $('#file-error').addClass('show');
                    $('#file-error').text('Please select an image file.');
                    $('#upload-file-text').addClass('error');
                } else {
                    $('#file-error').removeClass('show');
                    $('#upload-file-text').removeClass('error');
                    
                    $('#file-input-line input[type=text]').val(file.name);
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
                    $('input.save_change-button').after('<div id="save-change-message" class="success show">Change applied successfully!</div>');
                    setTimeout(function(){
                        window.location.replace('/account'); 
                    }, 1500);
                } else {
                    $('input.save_change-button').after('<div id="save-change-message" class="fail show">'+result.message+'</div>');
                    button.disabled = false;
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
            }
        });
        // $('#avatar-upload-form').submit();

    }
    document.getElementById('upload-avatar').addEventListener("change", readImage);
    
    $('#avatar-upload-form').submit(function(evt) {
        $('#save-change-message').remove();
        if ($('#avatar-crop').length) {
            var button = document.querySelector('input.save_change-button');
            button.disabled = true;

            $('#file-error').removeClass('show');
            $('#upload-file-text').removeClass('error');

            var canvas = document.getElementById("crop-canvas");
            var ctx = canvas.getContext("2d");
            var img=document.getElementById("avatar-crop");
            var width_ratio = orig_width / crop_width;
            var height_ratio = orig_height / crop_height;
            ctx.drawImage(img, crop_coords.x * width_ratio,crop_coords.y * height_ratio, 
                crop_coords.w * width_ratio, crop_coords.h * height_ratio, 0, 0, 256, 256);
            var dataURL = canvas.toDataURL('image/png');
            console.log(dataURL);
            $.ajax({
                type: "GET",
                url: "/account/avatar/upload",
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        uploadImage(result.url, dataURL);
                    } else {
                        $('input.save_change-button').after('<div id="save-change-message" class="fail show">'+result.message+'</div>');
                        button.disabled = false;
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                    button.disabled = false;
                }
            });
        } else {
            $('#file-error').addClass('show');
            $('#file-error').text('Please select an image.')
            $('#upload-file-text').addClass('error');
        }
        return false;
    });

    function showPreview(coords)
    {
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
});