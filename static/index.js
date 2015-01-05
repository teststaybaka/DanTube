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
        'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange,
      }
    });
}


function onPlayerReady(event) {
    console.log(player.getDuration());
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        isPlaying = true;
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "pause");
    } else if (event.data == YT.PlayerState.PAUSED || event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "play");
    }
}

function video_toggle(evt) {
    if (isPlaying) {
        isPlaying = false;
        player.pauseVideo();
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "play");
    } else {
        isPlaying = true;
        player.playVideo();
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "pause");
    }
}

function volume_switch(evt) {
    if (evt.target.className === "on") {
        evt.target.className = "off";
    } else {//off
        evt.target.className = "on";
    }
}

function danmaku_switch(evt) {
    if (evt.target.className === "on") {
        evt.target.className = "off";
    } else {//off
        evt.target.className = "on";
    }
}

function loop_switch(evt) {
    if (evt.target.className === "on") {
        evt.target.className = "off";
    } else {//off
        evt.target.className = "on";
    }
}

function widescreen_switch(evt) {
    if (evt.target.className === "on") {
        evt.target.className = "off";
    } else {//off
        evt.target.className = "on";
    }
}

function fullscreen_switch(evt) {
    if (evt.target.className === "on") {
        evt.target.className = "off";
    } else {//off
        evt.target.className = "on";
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

    var play_button = document.getElementById("play-pause-button");
    play_button.addEventListener("click", video_toggle);
    isPlaying = false;

    var volume_button = document.getElementById("volume-switch");
    volume_button.addEventListener("click", volume_switch);

    var danmaku_button = document.getElementById("danmaku-switch");
    danmaku_button.addEventListener("click", danmaku_switch);

    var loop_button = document.getElementById("loop-switch");
    loop_button.addEventListener("click", loop_switch);

    var wide_button = document.getElementById("wide-screen");
    wide_button.addEventListener("click", widescreen_switch);

    var full_button = document.getElementById("full-screen");
    full_button.addEventListener("click", fullscreen_switch);
};

function update() {
    // for (var i = 0; i < bullets.length; i++) {
    //     var bul = bullets[i];
    //     positions[i] -= 1;
    //     if (positions[i]  == 300) {
    //         var text = document.createTextNode('sdfsdfs');
    //         bul.appendChild(text);
    //     }
    //     bul.style.left = positions[i] + 'px';
    // }
    console.log(player.getDuration());
    console.log(player.getVideoLoadedFraction());
    console.log(player.getCurrentTime());
}
