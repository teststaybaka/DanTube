var player;
var isPlaying;
var danmakuVar;
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
    curTime = "00:00";
    progress_number.lastChild.nodeValue = curTime+"/"+duration;
    // console.log(progress_number.lastChild+" "+"00:00/"+player.getDuration());
    bufferVar = setInterval(buffer_update, 300);
    player.setVolume(50);

    buffer_update();
    progress_update();
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        isPlaying = true;
        danmakuVar = setInterval(danmaku_update, 50);
        progressVar = setInterval(progress_update, 300);
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "pause");
    } else if (event.data == YT.PlayerState.PAUSED) {
        isPlaying = false;
        clearInterval(danmakuVar);
        clearInterval(progressVar);
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "play");
    } else if (event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
        clearInterval(danmakuVar);
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
        player.setVolume(0);
    } else {//off
        evt.target.className = "on";
        var volume = document.getElementById("volume-bar");
        var volume_magnitude = document.getElementById("volume-magnitude");
        player.setVolume(volume_magnitude.offsetHeight/volume.offsetHeight*100);
    }
}

function volume_stop_propagation(evt) {
    evt.stopPropagation();
}

function volume_start(evt) {
    volume_move(evt);

    document.onmousemove = volume_move;
    document.onmouseup = volume_end;
    document.onmouseout = volume_end;
}

function volume_move(evt) {
    var volume = document.getElementById("volume-bar");
    var rect = volume.getBoundingClientRect();
    var len = volume.offsetHeight - (evt.clientY - rect.top);
    if (len > volume.offsetHeight) {
        len = volume.offsetHeight;
    }
    if (len < 0) {
        len = 0;
    }
    var volume_magnitude = document.getElementById("volume-magnitude");
    volume_magnitude.style.height = len + "px";
    
    var volume_pointer = document.getElementById("volume-pointer");
    volume_pointer.style.WebkitTransform = "translateY(-"+len+"px)";
    volume_pointer.style.msTransform = "translateY(-"+len+"px)";
    volume_pointer.style.transform = "translateY(-"+len+"px)";

    var volume_tip = document.getElementById("volume-tip");
    volume_tip.style.WebkitTransform = "translateY(-"+len+"px)";
    volume_tip.style.msTransform = "translateY(-"+len+"px)";
    volume_tip.style.transform = "translateY(-"+len+"px)";
    var text;
    if (Math.floor(len/volume.offsetHeight*100) < 10) {
        text = "0"+Math.floor(len/volume.offsetHeight*100);
    } else {
        text = Math.floor(len/volume.offsetHeight*100);
    }
    volume_tip.lastChild.nodeValue = text;

    player.setVolume(len/volume.offsetHeight*100);
}

function volume_end(evt) {
    // console.log(evt.target.id);
    if (evt.target.id === "volume-background") {
        document.onmousemove = null;
        document.onmouseup = null;
        document.onmouseout = null;
        // console.log("volume end")
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
        var danmaku_pool = document.getElementById("danmaku-pool");
        danmaku_pool.style.display = "inline-table";
        player.setSize(640, 360);
        var player_controller = document.getElementById("player-controller");
        player_controller.style.width = "640px";
        var danmaku_input = document.getElementById("danmaku-input");
        danmaku_input.style.width = "555px";
        var danmaku_right_mask = document.getElementById("danmaku-right-mask");
        danmaku_right_mask.style.left = "640px";
        danmaku_right_mask.style.height = "360px";
        var danmaku_left_mask = document.getElementById("danmaku-left-mask");
        danmaku_left_mask.style.height = "360px";
        progress_update();

        var list = document.querySelectorAll("div.danmaku");
        for (var i = 0; i < list.length; ++i) {
           list[i].style.left = "640px";
        }
    } else {//off
        evt.target.className = "on";
        var danmaku_pool = document.getElementById("danmaku-pool");
        danmaku_pool.style.display = "none";
        player.setSize(1024, 576);
        var player_controller = document.getElementById("player-controller");
        player_controller.style.width = "1024px";
        var danmaku_input = document.getElementById("danmaku-input");
        danmaku_input.style.width = "939px";
        var danmaku_right_mask = document.getElementById("danmaku-right-mask");
        danmaku_right_mask.style.left = "1024px";
        danmaku_right_mask.style.height = "576px";
        var danmaku_left_mask = document.getElementById("danmaku-left-mask");
        danmaku_left_mask.style.height = "576px";
        progress_update();

        var list = document.querySelectorAll("div.danmaku");
        for (var i = 0; i < list.length; ++i) {
           list[i].style.left = "1024px";
        }
    }
}

function fullscreen_switch(evt) {
    if (evt.target.className === "on") {
        evt.target.className = "off";
    } else {//off
        evt.target.className = "on";
    }
}

function progress_tip_show(evt) {
    var tip = document.getElementById("progress-tip");
    tip.style.display = "inline-block";

    var progress_bar = document.getElementById("progress-bar");
    var rect = progress_bar.getBoundingClientRect();
    var offset = evt.clientX - rect.left;
    if (offset < 0) {
        offset = 0;
    }
    if (offset > progress_bar.offsetWidth) {
        offset = progress_bar.offsetWidth;
    }
    tip.style.WebkitTransform = "translateX("+offset+"px)";
    tip.style.msTransform = "translateX("+offset+"px)";
    tip.style.transform = "translateX("+offset+"px)";

    var curTime = offset/progress_bar.offsetWidth*player.getDuration();
    var text;
    if (Math.floor(curTime/60) < 10) {
        text = "0"+Math.floor(curTime/60);
    } else {
        text = "" + Math.floor(curTime/60);
    }
    if (Math.floor(curTime%60) < 10) {
        text += ":0"+Math.floor(curTime%60);
    } else {
        text += ":"+Math.floor(curTime%60);
    }
    tip.lastChild.nodeValue = text;
}

function progress_tip_hide(evt) {
    var tip = document.getElementById("progress-tip");
    tip.style.display = "none";
}

function progress_bar_down(evt) {
    progressHold = true;
    
    progress_bar_move(evt);

    document.onmousemove = progress_bar_move;
    document.onmouseup = progress_bar_up_out;
    // document.onfocusout = progress_bar_up_out;
    document.onmouseout = progress_bar_up_out;
}

function progress_bar_move(evt) {
    // if (progressHold) {
        var progress_bar = document.getElementById("progress-bar");
        var rect = progress_bar.getBoundingClientRect();
        var progress_played = document.getElementById("progress-bar-played");
        var offset = evt.clientX - rect.left;
        if (offset < 0) {
            offset = 0;
        }
        if (offset > progress_bar.offsetWidth) {
            offset = progress_bar.offsetWidth;
        }
        progress_played.style.width = offset + "px";
        var progress_pointer = document.getElementById("progress-pointer");
        progress_pointer.style.WebkitTransform = "translateX("+offset+"px)";
        progress_pointer.style.msTransform = "translateX("+offset+"px)";
        progress_pointer.style.transform = "translateX("+offset+"px)";

        // var num = (evt.clientX - progress_bar.offsetLeft)/progress_bar.offsetWidth*player.getDuration();
        // player.seekTo(num, false);
    // }
}

function progress_bar_up_out(evt) {
    if (evt.target.id === "progress-bar") {
        progressHold = false;

        progress_bar_move(evt);

        var progress_bar = document.getElementById("progress-bar");
        var rect = progress_bar.getBoundingClientRect();
        var offset = evt.clientX - rect.left;
        if (offset < 0) {
            offset = 0;
        }
        if (offset > progress_bar.offsetWidth) {
            offset = progress_bar.offsetWidth;
        }
        var num = offset/progress_bar.offsetWidth*player.getDuration();
        var text;
        if (Math.floor(num/60) < 10) {
            text = "0"+Math.floor(num/60);
        } else {
            text = "" + Math.floor(num/60);
        }
        if (Math.floor(num%60) < 10) {
            text += ":0"+Math.floor(num%60);
        } else {
            text += ":"+Math.floor(num%60);
        }
        var progress_number = document.getElementById("progress-number");
        progress_number.lastChild.nodeValue = text+"/"+progress_number.lastChild.nodeValue.split('/')[1];
        progress_resize();

        player.seekTo(num, true);
        document.onmousemove = null;
        document.onmouseup = null;
        // document.onfocusout = null;
        document.onmouseout = null;
    }
}

var bullets = [];
var positions = [];

window.onload = function() {
    var max = 60;
    var player_container = document.getElementById("player-container");
    for (var i = 0; i < max; i++) {
        var bul = document.createElement('div');
        bul.setAttribute('class', 'danmaku');
        var text = document.createTextNode('sdfsdfs');
        bul.appendChild(text);
        player_container.appendChild(bul);
        bullets.push(bul);
    }

    var play_button = document.getElementById("play-pause-button");
    play_button.addEventListener("click", video_toggle);
    isPlaying = false;

    var volume_button = document.getElementById("volume-switch");
    volume_button.addEventListener("click", volume_switch);
    var volume = document.getElementById("volume-background");
    volume.addEventListener("mousedown", volume_start);
    volume.addEventListener("click", volume_stop_propagation);
    var volume_magnitude = document.getElementById("volume-magnitude");
    volume_magnitude.style.height = "25px";
    var volume_pointer = document.getElementById("volume-pointer");
    volume_pointer.style.WebkitTransform = "translateY(-"+25+"px)";
    volume_pointer.style.msTransform = "translateY(-"+25+"px)";
    volume_pointer.style.transform = "translateY(-"+25+"px)";
    var volume_tip = document.getElementById("volume-tip");
    volume_tip.style.WebkitTransform = "translateY(-"+25+"px)";
    volume_tip.style.msTransform = "translateY(-"+25+"px)";
    volume_tip.style.transform = "translateY(-"+25+"px)";
    volume_tip.lastChild.nodeValue = 50;

    var danmaku_button = document.getElementById("danmaku-switch");
    danmaku_button.addEventListener("click", danmaku_switch);

    var loop_button = document.getElementById("loop-switch");
    loop_button.addEventListener("click", loop_switch);

    var wide_button = document.getElementById("wide-screen");
    wide_button.addEventListener("click", widescreen_switch);

    var full_button = document.getElementById("full-screen");
    full_button.addEventListener("click", fullscreen_switch);

    var progress_bar = document.getElementById("progress-bar");
    progress_bar.addEventListener("mousedown", progress_bar_down);
    progress_bar.addEventListener("mouseover", progress_tip_show);
    progress_bar.addEventListener("mousemove", progress_tip_show);
    progress_bar.addEventListener("mouseout", progress_tip_hide);
    // progress_bar.addEventListener("mouseout", progress_bar_up_out);

    var progress_bar_played = document.getElementById("progress-bar-played");
    progress_bar_played.style.width = "0";

    var progress_buffered = document.getElementById("progress-bar-buffered");
    progress_buffered.style.width = "0";

    progress_resize();
    danmaku_mask_resize();
    console.log(getTextWidth("sdfsdfs"));
};
window.onresize = danmaku_mask_resize;
window.onscroll = danmaku_mask_resize;

function danmaku_mask_resize() {
    var left_mask = document.getElementById("danmaku-left-mask");
    var player_controller = document.getElementById("player-controller");
    var rect = player_controller.getBoundingClientRect();
    left_mask.style.width = rect.left + "px";
}

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

function getTextWidth(text) {
    // re-use canvas object for better performance
    var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
    var context = canvas.getContext("2d");
    context.font = "16px Times New Roman";
    var metrics = context.measureText(text);
    return metrics.width;
};

function progress_resize() {
    var progress_bar = document.getElementById("progress-bar");
    var rect = progress_bar.getBoundingClientRect();
    var progress_number = document.getElementById("progress-number");
    var rectNum = progress_number.getBoundingClientRect();
    progress_bar.style.width = (rectNum.left - rect.left - 9)+"px";

    var progress_bar_background = document.getElementById("progress-bar-background");
    progress_bar_background.style.width = progress_bar.style.width;
    // console.log('progress_resize');
}

function buffer_update() {
    var buffered = player.getVideoLoadedFraction();
    var progress_bar = document.getElementById("progress-bar");
    var progress_buffered = document.getElementById("progress-bar-buffered");
    progress_buffered.style.width = progress_bar.offsetWidth*buffered + "px";
    // console.log(buffered+" "+(-1000 + progress_bar.offsetWidth*buffered));
}

function progress_update() {
    // console.log('progress_update');
    var progress_number = document.getElementById("progress-number");
    var splits = progress_number.lastChild.nodeValue.split('/');
    var curTime;
    if (Math.floor(player.getCurrentTime()/60) < 10) {
        curTime = "0"+Math.floor(player.getCurrentTime()/60);
    } else {
        curTime = Math.floor(player.getCurrentTime()/60);
    }
    if (Math.floor(player.getCurrentTime()%60) < 10) {
        curTime += ":0"+Math.floor(player.getCurrentTime()%60);
    } else {
        curTime += ":"+Math.floor(player.getCurrentTime()%60);
    }
    progress_number.lastChild.nodeValue = curTime+"/"+splits[1];
    progress_resize();

    if (!progressHold) {
        var progress_bar = document.getElementById("progress-bar");
        var progress_played = document.getElementById("progress-bar-played");
        progress_played.style.width = player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth + "px";
        
        var progress_pointer = document.getElementById("progress-pointer");
        progress_pointer.style.WebkitTransform = "translateX("+player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth+"px)";
        progress_pointer.style.msTransform = "translateX("+player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth+"px)";
        progress_pointer.style.transform = "translateX("+player.getCurrentTime()/player.getDuration()*progress_bar.offsetWidth+"px)";
    }
}