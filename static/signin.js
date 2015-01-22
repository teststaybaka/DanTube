$(document).ready(function() {
    $('#signinform').submit(function() {
        $.ajax({
            type: "POST",
            url: "/signin",
            data: $('#signinform').serialize(),
            success: function(result) {
                console.log(result);
                if(result === 'success') {
                    $('#signin-success').addClass('show');
                    $('#signin-fail').removeClass('show');
                    setTimeout(function(){
                        window.location.replace('/'); 
                    }, 3000);
                } else {
                    $('#signin-success').removeClass('show');
                    $('#signin-fail').addClass('show');
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
            }
        });
        return false;
    });
});
