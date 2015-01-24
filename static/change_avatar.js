$(document).ready(function() {
    
    var crop_width, crop_height;
    var orig_width, orig_height;
    var crop_coords = {};

    function cropImage(src) {
        var old_image = $('#avatar-crop')[0];
        if(old_image) old_image.remove();
        var old_crop_holder = $('.jcrop-holder')[0];
        if(old_crop_holder) old_crop_holder.remove();

        $('#avatar-crop-container').append('<img id="avatar-crop" src="' + src + '">');
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
        $('.jcrop-holder').css({
            'left': '50%',
            'top': '50%',
            'margin-left': -crop_width/2 + 'px',
            'margin-top': -crop_height/2 + 'px',
            'position': 'absolute'
        });

        $('#avatar-preview-medium').removeAttr('width');
        $('#avatar-preview-medium').removeAttr('height');
        $('#avatar-preview-small').removeAttr('width');
        $('#avatar-preview-small').removeAttr('height');
        $('#avatar-preview-medium').attr('src', src);
        $('#avatar-preview-small').attr('src', src);   
    }

    function readImage() {
        if ( this.files && this.files[0] ) {
            file = this.files[0];
            if (file.size <= 0) {
                alert('File is invalid!');
            } else if (file.size > 50*1000000) {
                alert('File is not supposed to be larger than 50MB!!');
            } else {
                console.log('file size:'+file.size);
                console.log('file type:'+file.type);
                var types = file.type.split('/');
                if (types[0] != 'image') {
                    alert('Please select an image.');
                } else {
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
        } else {
            console.log('Please select a file to upload.');
        }
    }

    function uploadImage(upload_url, image_url) {
        var form = document.getElementById('avatar-upload-form');
        form.action = upload_url;
        var sBoundary = "---------------------------" + Date.now().toString(16);
        var base64Data = image_url.split(',')[1];
        // var binaryData = window.atob(base64Data);
        // var binaryData = decodeBase64(base64Data);
        var filename = document.getElementById('upload-avatar').files[0].name;
        // var data = '--' + sBoundary + '\r\n' + 
        //     'Content-Disposition: form-data; name="upload-avatar"; filename="' + filename + '"\n' + 
        //     'Content-Type: image/jpeg' + '\r\n\n' + binaryData + '\n' + '--' + sBoundary + '--\r\n';

        // http://stackoverflow.com/questions/6566240/saving-canvas-image-via-javascript-from-safari-5-0-x-to-appengine-blobstore-w
        var arr = ['--' + sBoundary, 'Content-Disposition: form-data; name="upload-avatar"; filename="' + filename + '"',
            'Content-Transfer-Encoding: base64', 'Content-Type:  image/jpeg', '', base64Data, '--' + sBoundary + '--'];
        var data = arr.join('\r\n');
        $.ajax({
            type: 'POST',
            url: form.action,
            headers: {"Content-Type": "multipart\/form-data; boundary=" + sBoundary},
            data: data,
            success: function(result){
                alert(result.message);
                if(!result.error) {
                    // success
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
        // $('#avatar-upload-form').submit();

    }
    document.getElementById('upload-avatar').addEventListener("change", readImage, false);
    
    $('#avatar-upload-button').click(function() {
        var canvas = document.getElementById("crop-canvas");
        var ctx = canvas.getContext("2d");
        var img=document.getElementById("avatar-crop");
        var width_ratio = orig_width / crop_width;
        var height_ratio = orig_height / crop_height;
        ctx.drawImage(img,crop_coords.x * width_ratio,crop_coords.y * height_ratio, 
            crop_coords.w * width_ratio, crop_coords.h * height_ratio, 0, 0, 100, 100);
        var dataURL = canvas.toDataURL('image/jpeg');
        console.log(dataURL);
        $.ajax({
            type: "GET",
            url: "/account/avatar/upload",
            success: function(result) {
                if(!result.error) {
                    console.log(result);
                    uploadImage(result.url, dataURL);
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
    });

    function showPreview(coords)
    {
        if(coords.w > 0) crop_coords = coords;
        var rx = 100 / coords.w;
        var ry = 100 / coords.h;
        $('#avatar-preview-medium').css({
            width: Math.round(rx * crop_width) + 'px',
            height: Math.round(ry * crop_height) + 'px',
            marginLeft: '-' + Math.round(rx * coords.x) + 'px',
            marginTop: '-' + Math.round(ry * coords.y) + 'px'
        });
        
        rx = 50 / coords.w;
        ry = 50 / coords.h;
        $('#avatar-preview-small').css({
            width: Math.round(rx * crop_width) + 'px',
            height: Math.round(ry * crop_height) + 'px',
            marginLeft: '-' + Math.round(rx * coords.x) + 'px',
            marginTop: '-' + Math.round(ry * coords.y) + 'px'
        });
    }
});