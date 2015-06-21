(function(dt, $) {
function subject_check() {
    var subject = $('#feedback-subject').val().trim();
    if (!subject) {
        $('#feedback-subject-error').addClass('show');
        $('#feedback-subject-error').text('Please enter a subject');
        $('#feedback-subject').addClass('error');
        return false;
    } else if (subject.length > 400) {
        $('#feedback-subject-error').addClass('show');
        $('#feedback-subject-error').text('Subject can\'t exceed 400 characters.');
        $('#feedback-subject').addClass('error');
        return false;
    } else {
        $('#feedback-subject-error').removeClass('show');
        $('#feedback-subject').removeClass('error');
        return true;
    }
}

function descript_check() {
    var descrip = $('#feedback-description').val().trim();
    if (!descrip) {
        $('#feedback-description-error').addClass('show');
        $('#feedback-description-error').text('Please write something for your feedback.');
        $('#feedback-description').addClass('error');
        return false;
    } else if (descrip.length > 2000) {
        $('#feedback-description-error').addClass('show');
        $('#feedback-description-error').text('Description can\'t exceed 2000 characters.');
        $('#feedback-description').addClass('error');
        return false;
    } else {
        $('#feedback-description-error').removeClass('show');
        $('#feedback-description').removeClass('error');
        return true;
    }
}

$(document).ready(function() {
    $('#feedback-submission-form').submit(function(evt) {
        evt.preventDefault();
        $('#change-applying').addClass('show');

        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        var error = false;
        if (!subject_check()) {
            error = true;
        }
        if (!descript_check()) {
            error = true;
        }
        console.log(error)
        if (error) {
            button.disabled = false;
            $('#change-applying').removeClass('show');
            return false;
        }

        $.ajax({
            type: "POST",
            url: evt.target.action,
            data: $('#feedback-submission-form').serialize(),
            success: function(result) {
                console.log(result);
                if(result.error) {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                } else {
                    dt.pop_ajax_message(result.message, 'success');
                    setTimeout(function(){
                        window.location.reload(); 
                    }, 3000);
                }
                $('#change-applying').removeClass('show');
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                button.disabled = false;
                $('#change-applying').removeClass('show');
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        return false;
    });  
});
//end of the file
} (dt, jQuery));
