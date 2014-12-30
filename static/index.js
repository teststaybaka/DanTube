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

// 4. The API will call this function when the video player is ready.
function onPlayerReady(event) {
event.target.playVideo();
}

// 5. The API calls this function when the player's state changes.
//    The function indicates that when playing a video (state=1),
//    the player should play for six seconds and then stop.
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
