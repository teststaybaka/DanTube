var player;
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
      height: '390',
      width: '640',
      videoId: 'M7lc1UVf-VE',
      events: {
        'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange
      }
    });
}


function onPlayerReady(event) {
    event.target.playVideo();
}

var done = false;
function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING && !done) {
      setTimeout(stopVideo, 6000);
      done = true;
    }
}
function stopVideo() {
    player.stopVideo();
}


var bullets = [];
var positions = [];

window.onload = function() {
    var move_speed = 1;
    var max = 60;
    for (var i = 0; i < max; i++) {
        var bul = document.createElement('div');
        
        bul.setAttribute('class', 'danmaku');
        bul.style.left = 200+'px';
        bul.style.top = i*20+'px';

        positions.push(i*20);
        document.body.appendChild(bul);
        bullets.push(bul);
    }
    var block_div = document.createElement('div');
    block_div.setAttribute('class', 'danmaku-mask');
    document.body.appendChild(block_div);
    setInterval(update, 50)
};

function update() {
    for (var i = 0; i < bullets.length; i++) {
        var bul = bullets[i];
        positions[i] -= 1;
        if (positions[i]  == 300) {
            var text = document.createTextNode('sdfsdfs');
            bul.appendChild(text);
        }
        bul.style.left = positions[i] + 'px';
    }
}

$(document).ready(function() {
    // Post Danmaku
    $('#post-danmaku-form .button').click(function(e){
        e.preventDefault();
        var content = $.trim($('#post-danmaku-form input[name="content"]')[0].value);
        if(content.length > 0) {
            var pdata = [{name: 'content', value: content}];
            pdata.push({name: 'video_id', value: '123'});
            pdata.push({name: 'timestamp', value: player.getCurrentTime()});
            $.ajax({
                type: "POST",
                url: "/danmaku",
                data: pdata,
                success: function(result) {
                    console.log(result);
                    if(!result.error) {
                        $('#danmaku-list').append('<tr><td>' + result.content + '</td><td>' + 'test' + '</td><td>' +  result.timestamp + '</td></tr>');
                    }
                },
                error: function (xhr, ajaxOptions, thrownError) {
                    console.log(xhr.status);
                    console.log(thrownError);
                }
            });
        }
    });
});
