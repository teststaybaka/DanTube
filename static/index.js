var player;
var isPlaying;
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
      height: '360',
      width: '100%',
      videoId: 'M7lc1UVf-VE',
      playerVars: {
        autoplay: 0,
        controls: 0,
        showinfo: 0,
        modestbranding: 1,
        enablejsapi: 1,
        rel: 0,
      },
      events: {
        // 'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange,
      }
    });
}


// function onPlayerReady(event) {
//     event.target.playVideo();
// }

function playVideo() {
    isPlaying = true;
    player.playVideo();
    var button = document.getElementById("play-pause-button");
    button.style.backgroundImage = 'url(/static/img/pause-icon.png)'
}

function pauseVideo() {
    isPlaying = false;
    player.pauseVideo();
    var button = document.getElementById("play-pause-button");
    button.style.backgroundImage = 'url(/static/img/play-icon.png)';
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        playVideo();
    } else if (event.data == YT.PlayerState.PAUSED) {
        pauseVideo();
    }
}

function video_toggle(evt) {
    if (isPlaying) {
        pauseVideo();
    } else {
        playVideo();
    }
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
    // setInterval(update, 50)

    var button = document.getElementById("play-pause-button");
    button.addEventListener("click", video_toggle);
    isPlaying = false;
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
