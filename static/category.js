function slideChange() {
    var preIndex = 3 - $('div.slide-dot').index($('div.slide-dot.active'));
    var index = (preIndex + 1)%4;
    $('div.slide-dot.active').removeClass('active');
    $('div.slide-dot:eq('+(3-index)+')').addClass('active');
    $('div.slide-title.active').removeClass('active');
    $('div.slide-title:eq('+(3-index)+')').addClass('active');
    document.getElementById('slide-container').style.left = -index*document.getElementById('ranking-slides').offsetWidth+'px';
    window.slideTimeout = setTimeout(slideChange, 5000);
}

$(document).ready(function() {
    window.slideTimeout = setTimeout(slideChange, 5000);
    $('div.slide-dot').click(function(evt) {
        if ($(evt.target).hasClass('active')) return;
        
        clearTimeout(window.slideTimeout);
        window.slideTimeout = setTimeout(slideChange, 5000);
        var preIndex = 3 - $('div.slide-dot').index($('div.slide-dot.active'));
        $('div.slide-dot.active').removeClass('active');
        $(evt.target).addClass('active');
        var index = 3 - $('div.slide-dot').index(evt.target);
        $('div.slide-title.active').removeClass('active');
        $('div.slide-title:eq('+(3-index)+')').addClass('active');
        document.getElementById('slide-container').style.left = -index*document.getElementById('ranking-slides').offsetWidth+'px';
    });

    // Retrieve Videos
    var category = window.location.pathname.split('/')[1];
    $('.subcategory').each(function() {
        var subcategory = $(this).attr('id');
        var current_div = $(this);
        var query = {'category': category, 'subcategory': subcategory, 'limit': 10};
        get_video_list(query, function(err, videos) {
            if(err) console.log(err);
            else {
                if(videos.length == 0)
                    current_div.append('<p>No video</p>');
                else {
                    for(var i = 0; i < videos.length; i++) {
                        var div = render_video_div(videos[i]);
                        current_div.append(div);
                    }
                }
            }
        });
    });
});