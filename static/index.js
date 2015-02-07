function slideChange() {
    var preIndex = 4 - $('div.slide-dot').index($('div.slide-dot.active'));
    var index = (preIndex + 1)%5;
    $('div.slide-dot.active').removeClass('active');
    $('div.slide-dot:eq('+(4-index)+')').addClass('active');
    $('a.slide-title').remove();
    $('div.slide-bottom').append('<a class="slide-title show">WHY!? WHY DID YOU HAVE TO DO THAT!? | Exoptable Money (Prequel to Presentable Liberty)</a>');
    document.getElementById('slide-container').style.left = -index*document.getElementById('ranking-slides').offsetWidth+'px';
}

$(document).ready(function() {
    var query = {'limit': 10};
    get_video_list(query, function(err, videos) {
        if(err) console.log(err);
        else {
            for(var i = 0; i < videos.length; i++) {
                var div = render_video_div(videos[i]);
                $('#video-list').append(div);
            }
        }
    });

    window.slideTimeout = setTimeout(slideChange, 5000);
    $('div.slide-dot').click(function(evt) {
        if ($(evt.target).hasClass('active')) return;
        
        clearTimeout(window.slideTimeout);
        window.slideTimeout = setTimeout(slideChange, 5000);
        var preIndex = 4 - $('div.slide-dot').index($('div.slide-dot.active'));
        $('div.slide-dot.active').removeClass('active');
        $(evt.target).addClass('active');
        var index = 4 - $('div.slide-dot').index(evt.target);
        $('a.slide-title').remove();
        $('div.slide-bottom').append('<a class="slide-title show">WHY!? WHY DID YOU HAVE TO DO THAT!? | Exoptable Money (Prequel to Presentable Liberty)</a>');
        document.getElementById('slide-container').style.left = -index*document.getElementById('ranking-slides').offsetWidth+'px';
    });
});