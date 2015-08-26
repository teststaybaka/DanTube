(function(dt, $) {
function subject_check() {
    var subject = $('#feedback-subject').val().trim();
    if (!subject) {
        $('#feedback-subject-error').addClass('show')
                                    .text('Please enter a subject');
        $('#feedback-subject').addClass('error');
        return false;
    } else if (subject.length > 400) {
        $('#feedback-subject-error').addClass('show')
                                    .text('Subject can\'t exceed 400 characters.');
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
        $('#feedback-description-error').addClass('show')
                                        .text('Please write something for your feedback.');
        $('#feedback-description').addClass('error');
        return false;
    } else if (descrip.length > 2000) {
        $('#feedback-description-error').addClass('show')
                                        .text('Description can\'t exceed 2000 characters.');
        $('#feedback-description').addClass('error');
        return false;
    } else {
        $('#feedback-description-error').removeClass('show');
        $('#feedback-description').removeClass('error');
        return true;
    }
}

$(document).ready(function() {
    $('#feedback-subject').focusout(subject_check);
    $('#feedback-description').focusout(descript_check);

    $('#feedback-submission-form').submit(function(evt) {
        var button = document.querySelector('input.save_change-button');
        button.disabled = true;

        if (!subject_check() | !descript_check()) {
            button.disabled = false;
            return false;
        }

        $('#change-applying').removeClass('hidden');
        $.ajax({
            type: "POST",
            url: "/contact",
            data: $(this).serialize(),
            success: function(result) {
                if(result.error) {
                    dt.pop_ajax_message(result.message, 'error');
                    button.disabled = false;
                } else {
                    dt.pop_ajax_message('We\'ve received your feedback. Thank you!', 'success');
                    setTimeout(function(){
                        window.location.reload(); 
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
