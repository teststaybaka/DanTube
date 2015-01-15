var player;
var isPlaying;
var refreshVar;
var bufferVar;
var progressVar;
var progressHold = false;
var isLoop = false;

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
    // console.log(player.getDuration());
    var progress_number = document.getElementById("progress-number");
    var curTime;
    var duration;
    if (Math.floor(player.getDuration()/60) < 10) {
        duration = "0"+Math.floor(player.getDuration()/60);
    } else {
        duration = ""+Math.floor(player.getDuration()/60);
    }
    if (Math.floor(player.getDuration()%60) < 10) {
        duration += ":0"+Math.floor(player.getDuration()%60);
    } else {
        duration += ":"+Math.floor(player.getDuration()%60);
    }
    if (Math.floor(player.getDuration()/60) > 99) {
        var digits = Math.floor(player.getDuration()/60).toString().length;
        curTime = "";
        for (var i = 0; i < digits; i++) {
            curTime += "0";
        }
    } else {
        curTime = "00";
    }
    curTime += ":00";
    progress_number.lastChild.nodeValue = curTime+"/"+duration;
    // console.log(progress_number.lastChild+" "+"00:00/"+player.getDuration());
    reposition();
    bufferVar = setInterval(buffer_update, 300);
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        isPlaying = true;
        // refreshVar = setInterval(update, 50);
        progressVar = setInterval(progress_update, 300);
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "pause");
    } else if (event.data == YT.PlayerState.PAUSED) {
        isPlaying = false;
        // clearInterval(refreshVar);
        clearInterval(progressVar);
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "play");
    } else if (event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
        // clearInterval(refreshVar);
        clearInterval(progressVar);
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "play");

        if (isLoop) {
            player.playVideo();
        }
    }
}

function video_toggle(evt) {
    if (isPlaying) {
        player.pauseVideo();
    } else {
        player.playVideo();
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
        isLoop = false;
    } else {//off
        evt.target.className = "on";
        isLoop = true;
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

function progress_bar_down(evt) {
    progressHold = true;
    var progress_bar = document.getElementById("progress-bar");
    var progress_played = document.getElementById("progress-bar-played");
    progress_played.style.backgroundPosition = -1000 + evt.clientX - progress_bar.offsetLeft + "px 0";
    var progress_pointer = document.getElementById("progress-pointer");
    progress_pointer.style.WebkitTransform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
    progress_pointer.style.msTransform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
    progress_pointer.style.transform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
}

function progress_bar_move(evt) {
    if (progressHold) {
        var progress_bar = document.getElementById("progress-bar");
        var progress_played = document.getElementById("progress-bar-played");
        progress_played.style.backgroundPosition = -1000 + evt.clientX - progress_bar.offsetLeft + "px 0";
        var progress_pointer = document.getElementById("progress-pointer");
        progress_pointer.style.WebkitTransform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
        progress_pointer.style.msTransform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
        progress_pointer.style.transform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";

        // var num = (evt.clientX - progress_bar.offsetLeft)/progress_bar.offsetWidth*player.getDuration();
        // player.seekTo(num, false);
    }
}

function progress_bar_up_out(evt) {
    if (progressHold) {
        progressHold = false;
        var progress_bar = document.getElementById("progress-bar");
        var progress_played = document.getElementById("progress-bar-played");
        progress_played.style.backgroundPosition = -1000 + evt.clientX - progress_bar.offsetLeft + "px 0";
        var progress_pointer = document.getElementById("progress-pointer");
        progress_pointer.style.WebkitTransform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
        progress_pointer.style.msTransform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";
        progress_pointer.style.transform = "translateX("+(evt.clientX - progress_bar.offsetLeft)+"px)";

        var num = (evt.clientX - progress_bar.offsetLeft)/progress_bar.offsetWidth*player.getDuration();
        player.seekTo(num, true);
    }
}

var bullets = [];
var positions = [];

window.onload = function() {
    var move_speed = 1;
    var max = 60;
    var nav_bar = document.getElementById("navigation-bar-background");
    for (var i = 0; i < max; i++) {
        var bul = document.createElement('div');
        
        bul.setAttribute('class', 'danmaku');
        bul.style.left = 500+'px';
        bul.style.top = i*20+'px';
        var text = document.createTextNode('sdfsdfs');
        bul.appendChild(text);

        positions.push(i*20);
        document.body.appendChild(bul);
        bullets.push(bul);
    }
    var block_div = document.createElement('div');
    block_div.setAttribute('class', 'danmaku-mask');
    document.body.appendChild(block_div);

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

    var progress_bar = document.getElementById("progress-bar");
    progress_bar.style.backgroundPosition = "-1000px 0";

    var progress_bar_played = document.getElementById("progress-bar-played");
    progress_bar_played.addEventListener("mousedown", progress_bar_down);
    progress_bar_played.addEventListener("mousemove", progress_bar_move);
    progress_bar_played.addEventListener("mouseup", progress_bar_up_out);
    progress_bar_played.addEventListener("mouseout", progress_bar_up_out);

    reposition();
};

window.onresize = reposition;
window.onscroll = reposition;

function danmaku_update() {
    // for (var i = 0; i < bullets.length; i++) {
    //     var bul = bullets[i];
    //     positions[i] -= 1;
    //     if (positions[i]  == 300) {
    //         var text = document.createTextNode('sdfsdfs');
    //         bul.appendChild(text);
    //     }
    //     bul.style.left = positions[i] + 'px';
    // }
    // console.log(player.getDuration());
    // console.log(player.getVideoLoadedFraction());
    // console.log(player.getCurrentTime());
    
}

function reposition() {
    var play_button = document.getElementById("play-pause-button");
    var rect = play_button.getBoundingClientRect();
    var progress_bar = document.getElementById("progress-bar");
    progress_bar.style.left = rect.left+9+play_button.offsetWidth+"px";
    progress_bar.style.top = rect.top+9+"px";
    var progress_number = document.getElementById("progress-number");
    var rectNum = progress_number.getBoundingClientRect();
    progress_bar.style.width = (rectNum.left - progress_bar.offsetLeft - 9)+"px";
    // console.log("?"+progress_bar.offsetLeft+" "+rectNum.left+" "+(rectNum.left - progress_bar.offsetLeft));

    var progress_played = document.getElementById("progress-bar-played");
    progress_played.style.left = progress_bar.style.left;
    progress_played.style.top = progress_bar.style.top;
    progress_played.style.width = progress_bar.style.width;
    // progress_buffered.style.backgroundPosition = "50% 100%";

    var progress_pointer = document.getElementById("progress-pointer");
    progress_pointer.style.left = progress_bar.offsetLeft - 5 + "px";
    progress_pointer.style.top = progress_bar.offsetTop - 2.5 + "px";
    // console.log(rect.top, rect.right, rect.bottom, rect.left);
    progress_update();
    buffer_update();
    // console.log('reposition');
}

function buffer_update() {
    var buffered = player.getVideoLoadedFraction();
    var progress_bar = document.getElementById("progress-bar");
    progress_bar.style.backgroundPosition = -1000 + progress_bar.offsetWidth*buffered + "px 0";
    // console.log(buffered+" "+(-1000 + progress_bar.offsetWidth*buffered));
    if (buffered === 1.0) {
        clearInterval(bufferVar);
    }
}

function progress_update() {
    // console.log('progress_update');
    var progress_bar = document.getElementById("progress-bar");
    var progress_played = document.getElementById("progress-bar-played");
    progress_played.style.backgroundPosition = -1000 + player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth + "px 0";

    var progress_number = document.getElementById("progress-number");
    var splits = progress_number.lastChild.nodeValue.split('/');
    var curTime;
    if (Math.floor(player.getCurrentTime()/60) < 10) {
        curTime = "0"+Math.floor(player.getCurrentTime()/60);
    } else {
        curTime = Math.floor(player.getCurrentTime()/60);
    }
    var extraDigits = splits[1].length - 5;
    for (var i = 0; i < extraDigits; i++) {
        curTime = "0"+curTime;
    }
    if (Math.floor(player.getCurrentTime()%60) < 10) {
        curTime += ":0"+Math.floor(player.getCurrentTime()%60);
    } else {
        curTime += ":"+Math.floor(player.getCurrentTime()%60);
    }
    progress_number.lastChild.nodeValue = curTime+"/"+splits[1];

    var progress_pointer = document.getElementById("progress-pointer");
    progress_pointer.style.WebkitTransform = "translateX("+player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth+"px)";
    progress_pointer.style.msTransform = "translateX("+player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth+"px)";
    progress_pointer.style.transform = "translateX("+player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth+"px)";
}
