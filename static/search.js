$(document).ready(function() {
    $('.option-entry').click(function() {
        var order = $(this).attr('data-order');
        var order_param = "order=" + order;
        var url = document.URL;
        var parts = url.split('&');
        var found = false;
        for(var i = 0; i < parts.length; i++) {
            if(parts[i].substring(0, 6) == "order=") { 
                parts[i] = order_param;
                found = true;
            }
        }
        if(!found) {
            parts.push(order_param);
        }
        url = parts.join('&');
        window.location.href = url;
    })
});