$(document).ready(function() {
    var canvas = document.getElementById("canvas");
    var context = canvas.getContext("2d");

    function readImage() {
        if ( this.files && this.files[0] ) {
            var FR= new FileReader();
            FR.onload = function(e) {
               var img = new Image();
               img.onload = function() {
                 context.drawImage(img, 0, 0);
               };
               img.src = e.target.result;
               $('#image-preview')[0].src = e.target.result;
            };       
            // FR.onloadend = function() {
            //     alert('das');
            //     $('#image-preview')[0].src = FR.result;
            // }
            FR.readAsDataURL( this.files[0] );
        }
    }
    document.getElementById('upload-image').addEventListener("change", readImage, false);
});