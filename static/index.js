var isAnimating = false;
function Slide_Animation(ele, fromIndex, toIndex) {
    var startTime = Date.now();
    var duration = 200;
    var fromX = fromIndex*document.getElementById('ranking-slides').offsetWidth;
    var toX = toIndex*document.getElementById('ranking-slides').offsetWidth;

    this.startAnimation = function() {
        requestAnimationFrame(update);
    }
    function update() {
        var percent = (Date.now() - startTime)/duration;
        var posX = fromX*(1 - percent) + toX*percent;

        ele.style.WebkitTransform = "translateX(-"+posX+"px)";
        ele.style.msTransform = "translateX(-"+posX+"px)";
        ele.style.transform = "translateX(-"+posX+"px)";


        if (percent < 1) {
            requestAnimationFrame(update);
        } else {
            ele.style.WebkitTransform = "translateX(-"+toX+"px)";
            ele.style.msTransform = "translateX(-"+toX+"px)";
            ele.style.transform = "translateX(-"+toX+"px)";
            isAnimating = false;
        }
    }
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

    $('div.slide-dot').click(function(evt) {
        if (isAnimating) return;

        if ($(evt.target).hasClass('active')) {
            return;
        }
        var preIndex = 4 - $('div.slide-dot').index($('div.slide-dot.active'));
        $('div.slide-dot').removeClass('active');
        $(evt.target).addClass('active');
        var index = 4 - $('div.slide-dot').index(evt.target);
        isAnimating = true;
        var slide_Animation = new Slide_Animation(document.getElementById('slide-container'), preIndex, index);
        slide_Animation.startAnimation();

        $('div.slide-title').remove();
        $('div.slide-bottom').append('<div class="slide-title show">WHY!? WHY DID YOU HAVE TO DO THAT!? | Exoptable Money (Prequel to Presentable Liberty)</div>');
    });
});