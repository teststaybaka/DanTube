$(document).ready(function() {
    var urls = window.location.href.split('/');
    if (urls[urls.length-1] === "account") {
        $("#sub-overview").addClass("active");
        $("#account-top-title").text("Overview");
    } else if (urls[urls.length-1] === "change_password") {
        $("#sub-change-password").addClass("active");
        $("#account-top-title").text("Change Password");
    }
});