var player;
var isPlaying;
var danmakuVar = null;
var progressVar = null;
var progressHold = false;
var isLoop = false;
var danmaku = [];
var danmaku_pointer = 0;
var danmaku_list = [];
var danmkau_elements = [];
var danmaku_check_interval = 1/4;
var lastTime = 0;
var occupation = new Array(10000);
var accumulate = new Array(10000);

function onPlayerReady(event) {
    // console.log(player.getDuration());
    var progress_number = document.getElementById("progress-number");
    progress_number.lastChild.nodeValue = "00:00"+"/"+secondsToTime(player.getDuration());
    // console.log(progress_number.lastChild+" "+"00:00/"+player.getDuration());
    setInterval(buffer_update, 500);
    player.setVolume(50);

    buffer_update();
    progress_update();
}

function onPlayerStateChange(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        isPlaying = true;
        if (danmakuVar == null) {
            danmakuVar = setInterval(danmaku_update, danmaku_check_interval*1000);
        }
        if (progressVar == null) {
            progressVar = setInterval(progress_update, 500);
        }
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "pause");
    } else if (event.data == YT.PlayerState.PAUSED || event.data == YT.PlayerState.BUFFERING) {
        isPlaying = false;
        clearInterval(danmakuVar);
        clearInterval(progressVar);
        danmakuVar = null;
        progressVar = null;
        var button = document.getElementById("play-pause-button");
        button.setAttribute("class", "play");
    } else if (event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
        clearInterval(danmakuVar);
        clearInterval(progressVar);
        danmakuVar == null;
        progressVar == null;
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
    var volume_controller = document.getElementById("volume-controller");
    if (volume_controller.className === "on") {
        volume_controller.className = "off";
        player.setVolume(0);
    } else {//off
        volume_controller.className = "on";
        var volume = document.getElementById("volume-bar");
        var volume_magnitude = document.getElementById("volume-magnitude");
        player.setVolume(volume_magnitude.offsetHeight/volume.offsetHeight*100);
    }
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
        var player_canvas = document.getElementById("player-canvas");
        player_canvas.style.width = "640px";
        player_canvas.style.height = "360px";
        progress_update();

        var list = document.querySelectorAll("div.danmaku");
        for (var i = 0; i < list.length; ++i) {
           list[i].style.left = "650px";
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
        var player_canvas = document.getElementById("player-canvas");
        player_canvas.style.width = "1024px";
        player_canvas.style.height = "576px";
        progress_update();

        var list = document.querySelectorAll("div.danmaku");
        for (var i = 0; i < list.length; ++i) {
           list[i].style.left = "1034px";
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
    tip.lastChild.nodeValue = secondsToTime(curTime);
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
        var progress_number = document.getElementById("progress-number");
        progress_number.lastChild.nodeValue = secondsToTime(num)+"/"+progress_number.lastChild.nodeValue.split('/')[1];
        progress_resize();

        player.seekTo(num, true);
        document.onmousemove = null;
        document.onmouseup = null;
        // document.onfocusout = null;
        document.onmouseout = null;
    }
}

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
    // console.log('buffer_update:'+player.getVideoLoadedFraction());
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
    progress_number.lastChild.nodeValue = secondsToTime(player.getCurrentTime())+"/"+splits[1];
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

function Danmaku_Animation(index) {
    var player_canvas = document.getElementById("player-canvas");
    var lTime = 0;
    var ele = danmkau_elements[index];
    var speed = (500 + ele['element'].offsetWidth)/10;

    this.startAnimation = function() {
        lTime = Date.now();
        requestAnimationFrame(update);
        // console.log(index+' '+startTime)
    }
    function update() {
        var curTime = Date.now();
        var deltaTime = curTime - lTime;
        lTime = curTime; 
        if (isPlaying) {
            ele['posX'] += speed*deltaTime/1000;
            ele['element'].style.WebkitTransform = "translate(-"+ele['posX']+"px, "+ele['posY']+"px)";
            ele['element'].style.msTransform = "translate(-"+ele['posX']+"px, "+ele['posY']+"px)";
            ele['element'].style.transform = "translate(-"+ele['posX']+"px, "+ele['posY']+"px)";
        }
        
        // console.log(index+' '+percent)
        if (ele['generating'] && ele['posX'] > ele['element'].offsetWidth + 5) {
            ele['generating'] = false;
            for (var j = ele['posY']; j < ele['element'].offsetHeight + ele['posY']; j++) {
                occupation[j] -= 1;
            }
        }

        if (ele['posX'] < ele['element'].offsetWidth + player_canvas.offsetWidth + 10) {
            requestAnimationFrame(update);
        } else {
            ele['element'].style.WebkitTransform = "translate(-"+0+"px, "+ele['posY']+"px)";
            ele['element'].style.msTransform = "translate(-"+0+"px, "+ele['posY']+"px)";
            ele['element'].style.transform = "translate(-"+0+"px, "+ele['posY']+"px)";
            danmkau_elements[index]['idle'] = true;
            ele['posX'] = 0;
        }
    }
}

function danmaku_update() {
    // console.log('danmaku_update:'+player.getCurrentTime());
    if (danmaku.length == 0) return;

    var player_canvas = document.getElementById("player-canvas");
    var curTime = player.getCurrentTime();
    // console.log('before:'+danmaku_pointer);
    if (danmaku[danmaku_pointer].timestamp <= curTime) {
        // console.log('out:'+danmaku[danmaku_pointer].timestamp);
        while (danmaku[danmaku_pointer].timestamp < curTime - 1 || danmaku[danmaku_pointer].timestamp < lastTime) {
            danmaku_pointer += 1;
            // console.log(danmaku[danmaku_pointer].timestamp);
        }
    } else {
        while(danmaku_pointer > 0 && danmaku[danmaku_pointer - 1].timestamp > curTime) {
            danmaku_pointer -= 1;
        }
    }
    
    for (var i = 0; i < danmkau_elements.length; i++) {
        if (danmaku[danmaku_pointer].timestamp > curTime) break;

        var ele = danmkau_elements[i];
        if (ele['idle']) {
            ele['element'].lastChild.nodeValue = danmaku[danmaku_pointer].content
            // ele['element'].lastChild.nodeValue = secondsToTime(danmaku[danmaku_pointer].timestamp);
            ele['generating'] = true;
            ele['idle'] = false;

            accumulate[0] = 0;
            for (var z = 0; z < ele['element'].offsetHeight && z < player_canvas.offsetHeight; z++) {
                accumulate[0] += occupation[z];
            }
            for (var j = 1; j < player_canvas.offsetHeight - ele['element'].offsetHeight + 1; j++) {
                accumulate[j] = accumulate[j-1];
                accumulate[j] -= occupation[j-1];
                accumulate[j] += occupation[j+ele['element'].offsetHeight-1];
            }

            var min_value = 2000000;
            var min_line = 0;
            for (var j = 0; j < player_canvas.offsetHeight - ele['element'].offsetHeight + 1; j++) {
                if (accumulate[j] < min_value) {
                    min_value = accumulate[j];
                    min_line = j;
                }
            }

            ele['posY'] = min_line;
            for (var j = ele['posY']; j < ele['element'].offsetHeight + ele['posY']; j++) {
                occupation[j] += 1;
            }
            
            var danmaku_Animation = new Danmaku_Animation(i);
            danmaku_Animation.startAnimation();
            danmaku_pointer += 1;
        }
    }
    lastTime = curTime;
}

$(document).ready(function() {
    var max = 60;
    var player_canvas = document.getElementById("player-canvas");
    for (var i = 0; i < max; i++) {
        var bul = document.createElement('div');
        bul.setAttribute('class', 'danmaku');
        var text = document.createTextNode('sdfsdfs');
        bul.appendChild(text);
        player_canvas.appendChild(bul);
        danmkau_elements.push({'idle':true, 'generating':false, 'posX': 0, 'posY': 0, 'element':bul});
    }
    for (var i = 0; i < 10000; i++) {
        occupation[i] = 0;
        accumulate[i] = 0;
    }

    var play_button = document.getElementById("play-pause-button");
    play_button.addEventListener("click", video_toggle);
    isPlaying = false;

    var volume_button = document.getElementById("volume-switch");
    volume_button.addEventListener("click", volume_switch);
    var volume = document.getElementById("volume-background");
    volume.addEventListener("mousedown", volume_start);
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

    var time_title = document.getElementById("time");
    time_title.addEventListener("click", time_order_change);
    var content_title = document.getElementById("content");
    content_title.addEventListener("click", content_order_change);
    var date_title = document.getElementById("date");
    date_title.addEventListener("click", date_order_change);
});

function time_order_change(evt) {
    var time_title = document.getElementById("time");
    if (time_title.className === "danmaku-order-title") {
        time_title.className = "danmaku-order-title up";
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_timestamp_lower_compare);
    } else if (time_title.className === "danmaku-order-title up") {
        time_title.className = "danmaku-order-title down"
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_timestamp_upper_compare);
    } else {//equal "danmaku-order-title down"
        time_title.className = "danmaku-order-title up"
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_timestamp_lower_compare);
    }
    generate_danmaku_pool_list();
    var content_title = document.getElementById("content");
    content_title.className = "danmaku-order-title";
    var date_title = document.getElementById("date");
    date_title.className = "danmaku-order-title";
}

function content_order_change(evt) {
    var content_title = document.getElementById("content");
    if (content_title.className === "danmaku-order-title") {
        content_title.className = "danmaku-order-title up";
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_content_lower_compare);
    } else if (content_title.className === "danmaku-order-title up") {
        content_title.className = "danmaku-order-title down"
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_content_upper_compare);
    } else {//equal "danmaku-order-title down"
        content_title.className = "danmaku-order-title up"
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_content_lower_compare);
    }
    generate_danmaku_pool_list();
    var time_title = document.getElementById("time");
    time_title.className = "danmaku-order-title";
    var date_title = document.getElementById("date");
    date_title.className = "danmaku-order-title";
}

function date_order_change(evt) {
    var date_title = document.getElementById("date");
    if (date_title.className === "danmaku-order-title") {
        date_title.className = "danmaku-order-title up";
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_date_lower_compare);
    } else if (date_title.className === "danmaku-order-title up") {
        date_title.className = "danmaku-order-title down"
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_date_upper_compare);
    } else {//equal "danmaku-order-title down"
        date_title.className = "danmaku-order-title up"
        quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_date_lower_compare);
    }
    generate_danmaku_pool_list();
    var content_title = document.getElementById("content");
    content_title.className = "danmaku-order-title";
    var time_title = document.getElementById("time");
    time_title.className = "danmaku-order-title";
}

function getTextWidth(text) {
    // re-use canvas object for better performance
    var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
    var context = canvas.getContext("2d");
    context.font = "16px Times New Roman";
    var metrics = context.measureText(text);
    return metrics.width;
}

function secondsToTime(secs)
{
    var curTime;
    if (Math.floor(secs/60) < 10) {
        curTime = "0"+Math.floor(secs/60);
    } else {
        curTime = ""+Math.floor(secs/60);
    }
    if (Math.floor(secs%60) < 10) {
        curTime += ":0"+Math.floor(secs%60);
    } else {
        curTime += ":"+Math.floor(secs%60);
    }
    return curTime;
}

function danmaku_timestamp_lower_compare(x, y) {
    return x.timestamp < y.timestamp;
}

function danmaku_timestamp_upper_compare(x, y) {
    return x.timestamp > y.timestamp;   
}

function danmaku_content_lower_compare(x, y) {
    return x.content < y.content;
}

function danmaku_content_upper_compare(x, y) {
    return x.content > y.content;
}

function danmaku_date_lower_compare(x, y) {
    if (parseInt(x.created.substr(0, 2)) < parseInt(y.created.substr(0, 2)) ) {
        return true;
    } else if (parseInt(x.created.substr(3, 2)) < parseInt(y.created.substr(3, 2)) ) {
        return true;
    } else if (parseInt(x.created.substr(6, 2)) < parseInt(y.created.substr(6, 2)) ) {
        return true;
    } else if (parseInt(x.created.substr(9, 2)) < parseInt(y.created.substr(9, 2)) ) {
        return true;
    } else {
        return false;
    }
}

function danmaku_date_upper_compare(x, y) {
    if (parseInt(x.created.substr(0, 2)) > parseInt(y.created.substr(0, 2)) ) {
        return true;
    } else if (parseInt(x.created.substr(3, 2)) > parseInt(y.created.substr(3, 2)) ) {
        return true;
    } else if (parseInt(x.created.substr(6, 2)) > parseInt(y.created.substr(6, 2)) ) {
        return true;
    } else if (parseInt(x.created.substr(9, 2)) > parseInt(y.created.substr(9, 2)) ) {
        return true;
    } else {
        return false;
    }
}

function generate_danmaku_pool_list() {
    var listNode = document.getElementById("danmaku-list");
    while (listNode.lastChild) {
        listNode.removeChild(listNode.lastChild);
    }

    for (var i = 0; i < danmaku_list.length; i++) {
        var per_container = document.createElement('div');
        per_container.className = "per-bullet container";

        var time_value = document.createElement('div');
        time_value.className = "bullet-time-value";
        time_value.appendChild(document.createTextNode(secondsToTime(danmaku_list[i].timestamp)));
        var padding1 = document.createElement('div');
        padding1.className = "space-padding";
        var content_value = document.createElement('div');
        content_value.className = "bullet-content-value";
        content_value.appendChild(document.createTextNode(danmaku_list[i].content));
        var padding2 = document.createElement('div');
        padding2.className = "space-padding";
        var date_value = document.createElement('div');
        date_value.className = "bullet-date-value";
        date_value.appendChild(document.createTextNode(danmaku_list[i].created));
        
        per_container.appendChild(time_value);
        per_container.appendChild(padding1);
        per_container.appendChild(content_value);
        per_container.appendChild(padding2);
        per_container.appendChild(date_value);
        listNode.appendChild(per_container);
    }
}

$(document).ready(function() {
    var url = document.URL;
    var video_id = url.substr(url.lastIndexOf('/dt') + 3);

    // Retrieve Danmaku
    $.ajax({
        type: "GET",
        url: url + "/danmaku",
        success: function(result) {
            if(!result.error) {
                console.log(result.length);
                for(var i = 0; i < result.length; i++) {
                    danmaku_list.push(result[i]);
                }
                // quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_timestamp_lower_compare);
                quick_sort(danmaku_list, 0, danmaku_list.length - 1, danmaku_date_lower_compare);
                generate_danmaku_pool_list();

                danmaku = result;
                quick_sort(danmaku, 0, danmaku.length-1, danmaku_timestamp_lower_compare);
            } else {
                console.log(result);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });

    // Post Danmaku
    $('#fire-button').click(function(e){
        e.preventDefault();
        var content = $('#danmaku-input')[0].value.trim();
        if(content.length > 0) {
            var pdata = [{name: 'content', value: content}];
            pdata.push({name: 'video_id', value: video_id});
            pdata.push({name: 'timestamp', value: player.getCurrentTime()});
            $.ajax({
                type: "POST",
                url: url + "/danmaku",
                data: pdata,
                success: function(result) {
                    if(!result.error) {
                        alert('success!');
                        $('#danmaku-list').append('<div class="per-bullet container">' + 
                            '<div class="bullet-time-value">' + secondsToTime(result.timestamp) + '</div>' + 
                            '<div class="space-padding"></div>' + 
                            '<div class="bullet-content-value">' + result.content + '</div>' + 
                            '<div class="space-padding"></div>' + 
                            '<div class="bullet-date-value">' + result.created + '</div></div>');
                    } else {
                        alert(result.error);
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
