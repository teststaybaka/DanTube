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
var occupation_normal = [];
var accumulate_normal = [];
var occupation_bottom = [];
var accumulate_bottom = [];
var occupation_top = [];
var accumulate_top = [];
var floorth = 0;
var inner_floorth = 0;

function onPlayerReady(event) {
	// console.log(player.getDuration());
	var progress_number = document.getElementById("progress-number");
	progress_number.lastChild.nodeValue = "00:00"+"/"+secondsToTime(player.getDuration());
	// console.log(progress_number.lastChild+" "+"00:00/"+player.getDuration());
	setInterval(buffer_update, 500);
	player.setVolume(50);

	buffer_update();
	progress_update();

	var arguments = document.URL.split('?')[1]
	if (arguments) {
		arguments = arguments.split('&');
		for (var i = 0; i < arguments.length; i++) {
			if (arguments[i].indexOf('timestamp') > -1) {
				var timestamp = parseFloat(arguments[i].substr(10));
				player.seekTo(timestamp, true);
			}
		}
	}
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
	if ($(volume_controller).hasClass('on')) {
		$(volume_controller).removeClass('on');
		$(volume_controller).addClass('off');
		player.setVolume(0);
	} else {//off
		$(volume_controller).removeClass('off');
		$(volume_controller).addClass('on');
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
	if ($(evt.target).hasClass('on')) {
		$(evt.target).addClass('off');
		$(evt.target).removeClass('on');
	} else {//off
		$(evt.target).addClass('on');
		$(evt.target).removeClass('off');
	}
}

function loop_switch(evt) {
	if ($(evt.target).hasClass('on')) {
		$(evt.target).addClass('off');
		$(evt.target).removeClass('on');
		isLoop = false;
	} else {//off
		$(evt.target).addClass('on');
		$(evt.target).removeClass('off');
		isLoop = true;
	}
}

function widescreen_switch(evt) {
	if ($(evt.target).hasClass('on')) {
		$(evt.target).removeClass('on');
		$(evt.target).addClass('off');
		var danmaku_pool = document.getElementById("danmaku-pool");
		danmaku_pool.style.display = "inline-table";
		player.setSize(640, 360);
		var player_controller = document.getElementById("player-controller");
		player_controller.style.width = "640px";
		var danmaku_input = document.getElementById("danmaku-input");
		danmaku_input.style.width = "527px";
		var player_canvas = document.getElementById("player-canvas");
		player_canvas.style.width = "640px";
		player_canvas.style.height = "360px";
		progress_update();

		var list = document.querySelectorAll("div.danmaku");
		for (var i = 0; i < list.length; ++i) {
		   list[i].style.left = "650px";
		}
	} else {//off
		$(evt.target).removeClass('off');
		$(evt.target).addClass('on');
		var danmaku_pool = document.getElementById("danmaku-pool");
		danmaku_pool.style.display = "none";
		player.setSize(1024, 576);
		var player_controller = document.getElementById("player-controller");
		player_controller.style.width = "1024px";
		var danmaku_input = document.getElementById("danmaku-input");
		danmaku_input.style.width = "911px";
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
	if ($(evt.target).hasClass('on')) {
		$(evt.target).addClass('off');
		$(evt.target).removeClass('on');
	} else {//off
		$(evt.target).addClass('on');
		$(evt.target).removeClass('off');
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

		danmaku_clear_request();

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

function Danmaku_Animation(index, type) {
	var player_canvas = document.getElementById("player-canvas");
	var lTime = 0;
	var ele = danmkau_elements[index];
	var speed = (800 + ele['element'].offsetWidth)/10;
	var existingTime = 5000;

	this.startAnimation = function() {
		lTime = Date.now();
		if (type === 'RightToLeft') {
			requestAnimationFrame(float_update);
		} else if (type === 'Top' || type === 'Bottom') {
			ele['posX'] = (player_canvas.offsetWidth - ele['element'].offsetWidth)/2 + ele['element'].offsetWidth;
			ele['element'].style.WebkitTransform = "translate(-"+ele['posX']+"px, "+ele['posY']+"px)";
			ele['element'].style.msTransform = "translate(-"+ele['posX']+"px, "+ele['posY']+"px)";
			ele['element'].style.transform = "translate(-"+ele['posX']+"px, "+ele['posY']+"px)";
			requestAnimationFrame(staying_update);
		}
		// console.log(index+' '+startTime)
	}

	function float_update() {
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
		if (ele['generating'] && (ele['clear_request'] || ele['posX'] > ele['element'].offsetWidth + 20)) {
			ele['generating'] = false;
			for (var j = ele['posY']; j < ele['element'].offsetHeight + ele['posY']; j++) {
				occupation_normal[j] -= 1;
			}
		}

		if (!ele['clear_request'] && ele['posX'] < ele['element'].offsetWidth + player_canvas.offsetWidth + 10) {
			requestAnimationFrame(float_update);
		} else {
			ele['element'].style.WebkitTransform = "translate(-"+0+"px, "+ele['posY']+"px)";
			ele['element'].style.msTransform = "translate(-"+0+"px, "+ele['posY']+"px)";
			ele['element'].style.transform = "translate(-"+0+"px, "+ele['posY']+"px)";
			ele['idle'] = true;
			ele['posX'] = 0;
		}
	}

	function staying_update() {
		var curTime = Date.now();
		var deltaTime = curTime - lTime;
		lTime = curTime;
		if (isPlaying) {
			existingTime -= deltaTime;
		}

		if (!ele['clear_request'] && existingTime > 0) {
			requestAnimationFrame(staying_update);
		} else {
			ele['generating'] = false;
			if (type === 'Top') {
				occupation = occupation_top;
			} else if (type === 'Bottom') {
				occupation = occupation_bottom;
			}
			for (var j = ele['posY']; j < ele['element'].offsetHeight + ele['posY']; j++) {
				occupation[j] -= 1;
			}
			// console.log(type+': '+occupation)
			ele['element'].style.WebkitTransform = "translate(-"+0+"px, "+ele['posY']+"px)";
			ele['element'].style.msTransform = "translate(-"+0+"px, "+ele['posY']+"px)";
			ele['element'].style.transform = "translate(-"+0+"px, "+ele['posY']+"px)";
			ele['idle'] = true;
			ele['posX'] = 0;
		}
	}
}

function danmaku_clear_request() {
	for (var i = 0; i < danmkau_elements.length; i++) {
		var ele = danmkau_elements[i];
		ele['clear_request'] = true;
	}
}

function danmaku_update() {
	// console.log('danmaku_update:'+player.getCurrentTime());
	if (danmaku.length == 0) return;

	var player_canvas = document.getElementById("player-canvas");
	var curTime = player.getCurrentTime();
	// console.log('before:'+danmaku_pointer);
	if (danmaku_pointer < danmaku.length && danmaku[danmaku_pointer].timestamp <= curTime) {
		// console.log('out:'+danmaku[danmaku_pointer].timestamp);
		while (danmaku_pointer < danmaku.length
			&& (danmaku[danmaku_pointer].timestamp < curTime - 1 || danmaku[danmaku_pointer].timestamp < lastTime)) {
			danmaku_pointer += 1;
			// console.log(danmaku[danmaku_pointer].timestamp);
		}
	} else {
		while(danmaku_pointer > 0 && danmaku[danmaku_pointer - 1].timestamp >= curTime) {
			danmaku_pointer -= 1;
		}
	}
	
	for (var i = 0; i < danmkau_elements.length; i++) {
		if (danmaku_pointer >= danmaku.length || danmaku[danmaku_pointer].timestamp > curTime) break;

		var ele = danmkau_elements[i];
		if (ele['idle']) {
			ele['element'].lastChild.nodeValue = danmaku[danmaku_pointer].content;
			ele['element'].style.color = '#'+('000000'+danmaku[danmaku_pointer].color.toString(16)).substr(-6);
			ele['element'].style.fontSize = danmaku[danmaku_pointer].size+'px';
			// ele['element'].lastChild.nodeValue = secondsToTime(danmaku[danmaku_pointer].timestamp);
			ele['generating'] = true;
			ele['idle'] = false;
			ele['clear_request'] = false;

			if (danmaku[danmaku_pointer].type === 'RightToLeft') {
				accumulate = accumulate_normal;
				occupation = occupation_normal;
			} else if (danmaku[danmaku_pointer].type === 'Bottom') {
				accumulate = accumulate_bottom;
				occupation = occupation_bottom;
			} else if (danmaku[danmaku_pointer].type === 'Top') {
				accumulate = accumulate_top;
				occupation = occupation_top;
			} 
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
				if ((danmaku[danmaku_pointer].type === 'Bottom' && accumulate[j] <= min_value)
					|| (danmaku[danmaku_pointer].type != 'Bottom' && accumulate[j] < min_value)) {
					min_value = accumulate[j];
					min_line = j;
				}
			}

			ele['posY'] = min_line;
			for (var j = ele['posY']; j < ele['element'].offsetHeight + ele['posY']; j++) {
				occupation[j] += 1;
			}
			
			var danmaku_Animation = new Danmaku_Animation(i, danmaku[danmaku_pointer].type);
			danmaku_Animation.startAnimation();
			danmaku_pointer++;
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
		danmkau_elements.push({'idle':true, 'generating':false, 'posX': 0, 'posY': 0, 'clear_request':false, 'element':bul});
	}
	for (var i = 0; i < 10000; i++) {
		occupation_top.push(0);
		occupation_bottom.push(0);
		occupation_normal.push(0);
		accumulate_top.push(0);
		accumulate_bottom.push(0);
		accumulate_normal.push(0);
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
	if (x.timestamp != y.timestamp) {
		return x.timestamp < y.timestamp;
	} else {
		return danmaku_content_lower_compare(x, y);
	}
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
	return x.created_seconds < y.created_seconds;
}

function danmaku_date_upper_compare(x, y) {
	return x.created_seconds > y.created_seconds;
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
		content_value.title = danmaku_list[i].content;
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

function isCookieExisted(cname) {
	var cookie = getCookie(cname);
	var res = (cookie != "");
	var now = new Date().toUTCString();
	var extime = 10 * 60 *1000; // 10 mins window to block next operation
	setCookie(cname, now, extime);
	return res;
}

$(document).ready(function() {
	var url = document.URL;
	var urls = document.URL.split('/');
	var url_suffix = urls[urls.length-1];
	var video_id = url.split('?')[0].substr(url.lastIndexOf('/dt') + 3);

	$('div.more-episode').click(function() {
		$('a.episode-link.hidden').removeClass('hidden');
		$('div.more-episode').remove();
	});

	// $('#uploader-subscribe').click(function(e) {
	// 	var uploader_id = $(this).attr('uid');
	// 	$.ajax({
	// 		type: "POST",
	// 		url: "/user/" + uploader_id + "/subscribe",
	// 		success: function(result) {
	// 			if(!result.error) {
	// 				alert('success!');
	// 			} else {
	// 				alert(result.message);
	// 			}
	// 		},
	// 		error: function (xhr, ajaxOptions, thrownError) {
	// 			console.log(xhr.status);
	// 			console.log(thrownError);
	// 			pop_ajax_message(xhr.status+' '+thrownError, 'error');
	// 		}
	// 	});
	// })

	if( !isCookieExisted( video_id+'_last_hit' ) ) {
		// Send to server hit +1
		$.ajax({
			type: "POST",
			url: '/video/hit/dt' + video_id,
			success: function(result) {
				if(!result.error) {
					console.log('hit +1 success.');
				} else {
					console.log(result.error);
				}
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
			}
		});
	} else {
		console.log('Hit is not counted.');
	}

	$('#add-to-favorite').click(function() {
		$.ajax({
			type: "POST",
			url: '/account/favor/dt'+video_id,
			success: function(result) {
				if(!result.error) {
					pop_ajax_message('You have successfully added it to your favorites.', 'success');
					$('#add-to-favorite').children('span.commas_number').text(numberWithCommas(result.favors));
				} else {
					pop_ajax_message(result.message, 'error');
				}
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				pop_ajax_message(xhr.status+' '+thrownError, 'error');
			}
		});
	});

	$('#like-this').click(function(e) {
		if( !isCookieExisted( video_id+'_last_like' ) ) {
			// Send to server like + 1
			$.ajax({
				type: "POST",
				url: '/video/like/dt' + video_id,
				success: function(result) {
					if(!result.error) {
						pop_ajax_message('You liked it!', 'success');
						$('#like-this').children('span.commas_number').text(numberWithCommas(result.likes));
					} else {
						pop_ajax_message(result.message, 'error');
					}
				},
				error: function (xhr, ajaxOptions, thrownError) {
					console.log(xhr.status);
					console.log(thrownError);
					pop_ajax_message(xhr.status+' '+thrownError, 'error');
				}
			});
		} else {
			pop_ajax_message('You already liked it.', 'error');
		}
	});

	$('#danmaku-type-setting').click(function() {
		$('#danmaku-type-box').removeClass('hidden');
		var hide_type_box = function() {
			$('#danmaku-type-box').addClass('hidden');
			$(document).off('mousedown', hide_type_box);
		};
		$(document).mousedown(hide_type_box);
	});

	$('#danmaku-type-box').mousedown(function(evt) {
		evt.stopPropagation();
	});

	$('div.danmaku-size-option').click(function() {
		$('div.danmaku-size-option').removeClass('active');
		$(this).addClass('active');
		if ($(this).hasClass('small')) {
			$('#danmaku-size-input').val('12');
		} else if ($(this).hasClass('medium')) {
			$('#danmaku-size-input').val('16');
		} else if ($(this).hasClass('large')) {
			$('#danmaku-size-input').val('20');
		}
	});

	$('div.danmaku-type-option').click(function() {
		$('div.danmaku-type-option').removeClass('active');
		$(this).addClass('active');
		if ($(this).hasClass('top')) {
			$('#danmaku-type-input').val('Top');
		} else if ($(this).hasClass('normal')) {
			$('#danmaku-type-input').val('RightToLeft');
		} else if ($(this).hasClass('bottom')) {
			$('#danmaku-type-input').val('Bottom');
		}
	});

	$('#danmaku-color-setting').colpick({
		layout: 'rgbhex',
		color: 'ffffff',
		onSubmit: function(hsb,hex,rgb,el) {	
			$('#danmaku-color-setting').colpickHide();
			$('#danmaku-color-setting').css('background-color', '#'+hex);
			$('#danmaku-color-input').val(hex);
		},
	});

	// Retrieve Danmaku
	$.ajax({
		type: "GET",
		url: '/video/danmaku/' + url_suffix,
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
				pop_ajax_message(result.message, 'error');
			}
		},
		error: function (xhr, ajaxOptions, thrownError) {
			console.log(xhr.status);
			console.log(thrownError);
			pop_ajax_message(xhr.status+' '+thrownError, 'error');
		}
	});

	// Post Danmaku
	$('#shooter').submit(function(){
		var button = document.querySelector('#fire-button');
		button.disabled = true;

		var error = false;
		var content = $('#danmaku-input').val().trim();
		if (!content) {
			pop_ajax_message('You can\'t post empty comment.', 'error');
			error = true;
		} else if (content.length > 350) {
			pop_ajax_message('Comment is too long (less than 350 characters).', 'error');
			error = true;
		}

		if (error) {
			button.disabled = false;
			return false;
		}

		var danmaku_color = $('#danmaku-color-input').val();
		var danmaku_type = $('#danmaku-type-input').val();
		var danmaku_size = $('#danmaku-size-input').val();
		$.ajax({
			type: "POST",
			url: '/video/danmaku/' + url_suffix,
			data: {content: content, timestamp: (player.getCurrentTime()), color: danmaku_color, type: danmaku_type, size: danmaku_size},
			success: function(result) {
				if(!result.error) {
					$('#danmaku-input').val('');
					pop_ajax_message('Danmaku sent!', 'success');
					result.timestamp = player.getCurrentTime();
					$('#danmaku-list').append('<div class="per-bullet container">\
						<div class="bullet-time-value">' + secondsToTime(result.timestamp) + '</div>\
						<div class="space-padding"></div>\
						<div class="bullet-content-value" title="' + result.content + '">' + result.content + '</div>\
						<div class="space-padding"></div>\
						<div class="bullet-date-value">' + result.created + '</div></div>');
					danmaku_list.push(result);
					danmaku.push(result);
					quick_sort(danmaku, 0, danmaku.length-1, danmaku_timestamp_lower_compare);
				} else {
					pop_ajax_message(result.message, 'error');
				}
				button.disabled = false;
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				pop_ajax_message(xhr.status+' '+thrownError, 'error');
				button.disabled = false;
			}
		});
		return false;
	});

	$('div.add-new-tag-button').click(function() {
		$('input.add-new-tag-input').addClass('show');
		$('input.add-new-tag-input').focus();
	});

	$('input.add-new-tag-input').focusout(function() {
		$('input.add-new-tag-input').removeClass('show');
	})

	$('#add-new-tag-form').submit(function(evt) {
		var error = false;
		var new_tag = $('input.add-new-tag-input').val().trim();
		if (!new_tag) {
			pop_ajax_message('You can\'t add an empty tag.', 'error');
			error = true;
		} else if (new_tag.length > 100) {
			pop_ajax_message('Tag is too long (less than 100 characters).', 'error');
			error = true;
		} else if (new_tag.indexOf(',') > -1) {
			pop_ajax_message('Can not contain ",".', 'error');
			error = true;
		}

		if (error) {
			return false;
		}

		$.ajax({
			type: "POST",
			url: '/video/new_tag/dt'+video_id,
			data: $(evt.target).serialize(),
			success: function(result) {
				if(!result.error) {
					pop_ajax_message('A new tag has been added!', 'success');
					$('input.add-new-tag-input').val('');
					$('input.add-new-tag-input').focusout();
				} else {
					$('input.add-new-tag-input').val('');
					pop_ajax_message(result.message, 'error');
				}
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				pop_ajax_message(xhr.status+' '+thrownError, 'error');
			}
		});
		return false;
	});

	var video_intro = document.getElementById('video-intro-box');
	if (video_intro.scrollHeight > 48) {
		video_intro.style.height = "48px";
	} else {
		$('#video-intro-display-button').remove();
	}
	$('#video-intro-display-button').click(function(evt) {
		if ($('#video-intro-display-button').hasClass('less')) {
			$('#video-intro-display-button').removeClass('less');
			$('#video-intro-display-button').children('span.intro-display-text').text("SHOW MORE");
			video_intro.style.height = "48px";
		} else {
			$('#video-intro-display-button').addClass('less');
			$('#video-intro-display-button').children('span.intro-display-text').text("SHOW LESS");
			video_intro.style.height = video_intro.scrollHeight + "px";
		}
	});

	var list_intro = document.getElementById('list-intro');
	if (list_intro) {
		if (list_intro.scrollHeight > 48) {
			list_intro.style.height = "48px";
		} else {
			$('#list-intro-display-button').remove();
		}
		$('#list-intro-display-button').click(function(evt) {
			if ($('#list-intro-display-button').hasClass('less')) {
				$('#list-intro-display-button').removeClass('less');
				$('#list-intro-display-button').children('span.intro-display-text').text("SHOW MORE");
				list_intro.style.height = "48px";
			} else {
				$('#list-intro-display-button').addClass('less');
				$('#list-intro-display-button').children('span.intro-display-text').text("SHOW LESS");
				list_intro.style.height = list_intro.scrollHeight + "px";
			}
		});
	}

	$('#user-comment-form').submit(function(evt) {
		var button = document.querySelector('#user-comment-form input.inline-button.post');
		button.disabled = true;

		var error = false;
		var content = $('#comment-textarea').val().trim();
		if (!content) {
			pop_ajax_message('You can\'t post empty comment.', 'error');
			error = true;
		} else if (content.length > 2000) {
			pop_ajax_message('Your comment is too long (less than 2000 characters).', 'error');
			error = true;
		}

		if (error) {
			button.disabled = false;
			return false;
		}

		$.ajax({
			type: "POST",
			url: '/video/comment_post/dt'+video_id,
			data: $(evt.target).serialize(),
			success: function(result) {
				if(!result.error) {
					pop_ajax_message('Comment posted!', 'success');
					$('#comment-textarea').val('');
					update_comments(1, video_id);
				} else {
					pop_ajax_message(result.message, 'error');
				}
				button.disabled = false;
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				pop_ajax_message(xhr.status+' '+thrownError, 'error');
				button.disabled = false;
			}
		});
		return false;
	});

	$('#user-reply-form').submit(function(evt) {
		var button = document.querySelector('#user-reply-form input.inline-button.post');
		button.disabled = true;

		var error = false;
		var content = $('#reply-textarea').val().trim();
		if (!content) {
			pop_ajax_message('You can\'t post empty comment.', 'error');
			error = true;
		} else if (content.length > 2000) {
			pop_ajax_message('Your comment is too long (less than 2000 characters).', 'error');
			error = true;
		}
		var comment_id = $(evt.target).parent().parent().attr('data-id');
		if (!comment_id) {
			error = true;
		}

		if (error) {
			button.disabled = false;
			return false;
		}

		$.ajax({
			type: "POST",
			url: '/video/reply_post/dt'+video_id,
			data: {content: content, comment_id: comment_id},
			success: function(result) {
				if(!result.error) {
					pop_ajax_message('Reply posted!', 'success');
					$('#reply-textarea').val('');
					update_inner_comments(result.total_pages, video_id, $(evt.target).parent());
				} else {
					pop_ajax_message(result.message, 'error');
				}
				button.disabled = false;
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				pop_ajax_message(xhr.status+' '+thrownError, 'error');
				button.disabled = false;
			}
		});
		return false;
	});

	$('div.pagination-line.all').on('click', 'a', function() {
		var page = $(this).attr('data-page');
		update_comments(page, video_id);
	});
	$('#comments-list-container').on('click', 'div.comment-entry.error', function() {
		var page = $(this).attr('data-page');
		if ($(this).hasClass('inner')) {
			update_inner_comments(page, video_id, $(this).parent());
		} else {
			update_comments(page, video_id);
		}
	});
	$('#comments-list-container').on('click', 'a.page-num, a.page-change', function() {
		var page = $(this).attr('data-page');
		update_inner_comments(page, video_id, $(this).parent().parent());
	});

	$(window).scroll(function() {
		if ($('#comments-list-container').children().length > 0
			|| $(window).scrollTop() < $('#comments-list-container').offset().top - 30  - $(window).height()) return;

		update_comments(1, video_id);
	});
	$('#comments-list-container').on('click', 'div.display-button.comment', function() {
		if ($(this).hasClass('less')) {
			var comment_div = $(this).prev();
			comment_div[0].style.height = '48px';
			$(this).removeClass('less');
			$(this).children('span.reply-display-text').text('Read more');
		} else {
			var comment_div = $(this).prev();
			comment_div[0].style.height = comment_div[0].scrollHeight + 'px';
			$(this).addClass('less');
			$(this).children('span.reply-display-text').text('Read less');
		}
	});
	$('#comments-list-container').on('click', 'div.display-button.replies', function() {
		update_inner_comments(1, video_id, $(this).parent());
	});
	$('#comments-list-container').on('click', 'div.comment-operation.reply', function() {
		var comment_box = $(this).parent().parent();
		var comment_entry = comment_box.parent();
		if (comment_entry.hasClass('inner')) {
			var inner_comment_container = comment_entry.parent();
		} else {
			var inner_comment_container = comment_box.next();
		}
		inner_comment_container.append($('#user-reply-form'));
		$('#user-reply-form').removeClass('hidden');
	});

	var arguments = url.split('?')[1]
	if (arguments) {
		arguments = arguments.split('&');
		for (var i = 0; i < arguments.length; i++) {
			if (arguments[i].indexOf('comment') > -1) {
				floorth = parseInt(arguments[i].substr(8));
			}
			if (arguments[i].indexOf('reply') > -1) {
				inner_floorth = parseInt(arguments[i].substr(6));
			}
		}
		if (floorth != 0) {
			var total = parseInt($('#comments-block-title span').text());
			var rev = total - floorth + 1;
			update_comments(Math.ceil(rev/20), video_id);
		}
	}
});

function update_comments(page, video_id) {
	var comment_container = $('#comments-list-container');
	var pagination_container = $('div.pagination-line.all');
	$('#user-comment-form').after($('#user-reply-form'));
	$('#user-reply-form').addClass('hidden')
	comment_container.empty();
	pagination_container.empty();
	comment_container.append('<div class="comment-entry loading"></div>');
	$.ajax({
		type: "GET",
		url: '/video/comment/dt'+video_id,
		data: {page: page},
		success: function(result) {
			comment_container.empty();
			if(!result.error) {
				$('#comments-block-title').children('span.commas_number').text(numberWithCommas(result.total_comments));
				if (result.total_pages == 0) {
					comment_container.append('<div class="comment-entry no-comment">Be the first one to comment!</div>');
				} else {
					for(var i = 0; i < result.comments.length; i++) {
	                    var comment_div = render_comment_div(result.comments[i]);
	                    comment_container.append(comment_div);
	                }
	                var content_div = comment_container.find('div.comment-content');
                    for (var j = 0; j < content_div.length; j++) {
                    	if (content_div[j].scrollHeight > 48) {
                    		$(content_div[j]).addClass('collapse');
                    	} else {
                    		$(content_div[j]).next().remove();
                    	}
                    }

                    var pagination = render_pagination(page, result.total_pages);
                    pagination_container.append(pagination);

                    for(var i = 0; i < result.comments.length; i++) {
                    	if (result.comments[i].floorth == floorth) {
	                    	var cur_div = $(comment_container.children()[i]);
	                    	$(window).scrollTop(cur_div.offset().top);
	                    	console.log(cur_div.offset().top)
	                    	floorth = 0;
	                    	if (inner_floorth != 0) {
		                    	update_inner_comments(Math.ceil(inner_floorth/10), video_id, cur_div.children('div.inner-comment-container'))
		                    }
	                    }
                    }
				}
			} else {
				pop_ajax_message(result.message, 'error');
				comment_container.append('<div class="comment-entry no-comment error">Load error.</div>');
			}
		},
		error: function (xhr, ajaxOptions, thrownError) {
			console.log(xhr.status);
			console.log(thrownError);
			comment_container.empty();
			pop_ajax_message(xhr.status+' '+thrownError, 'error');
			comment_container.append('<div class="comment-entry no-comment error" data-page="'+page+'">Load error.</div>');
		}
	});
}

function update_inner_comments(page, video_id, inner_comment_container) {
	var comment_id = inner_comment_container.parent().attr('data-id');
	inner_comment_container.children('div.comment-entry').remove();
	inner_comment_container.children('div.display-button.replies').remove();
	var pagination_container = inner_comment_container.children('div.pagination-line.replies');
	if (pagination_container.length == 0) {
		inner_comment_container.prepend('<div class="pagination-line replies"></div>');
		pagination_container = inner_comment_container.children('div.pagination-line.replies');
	}
	pagination_container.empty();

	inner_comment_container.prepend('<div class="comment-entry loading"></div>');
	$.ajax({
		type: "GET",
		url: '/video/inner_comment/dt'+video_id,
		data: {page: page, comment_id: comment_id},
		success: function(result) {
			inner_comment_container.children('div.comment-entry').remove();
			if(!result.error) {
				if (result.total_pages != 0) {
					// inner_comment_container.append('<div class="comment-entry no-comment">Be the first one to comment!</div>');
				// } else {
					for(var i = 0; i < result.inner_comments.length; i++) {
	                    var comment_div = render_inner_comment_div(result.inner_comments[i]);
	                    pagination_container.before(comment_div);
	                }
	                var content_div = inner_comment_container.find('div.comment-content');
                    for (var j = 0; j < content_div.length; j++) {
                    	if (content_div[j].scrollHeight > 48) {
                    		$(content_div[j]).addClass('collapse');
                    	} else {
                    		$(content_div[j]).next().remove();
                    	}
                    }

                    if (result.total_pages > 1) {
		                var pagination = render_pagination(page, result.total_pages);
	                    pagination_container.append(pagination);
	                }

	                for(var i = 0; i < result.inner_comments.length; i++) {
                    	if (result.inner_comments[i].inner_floorth == inner_floorth) {
	                    	var cur_div = $(inner_comment_container.children('div.comment-entry')[i]);
	                    	$(window).scrollTop(cur_div.offset().top);
	                    	inner_floorth = 0;
	                    }
                    }
				}
			} else {
				pop_ajax_message(result.message, 'error');
				inner_comment_container.prepend('<div class="comment-entry no-comment inner error">Load error.</div>');
			}
		},
		error: function (xhr, ajaxOptions, thrownError) {
			console.log(xhr.status);
			console.log(thrownError);
			inner_comment_container.children('div.comment-entry').remove();
			pop_ajax_message(xhr.status+' '+thrownError, 'error');
			inner_comment_container.prepend('<div class="comment-entry no-comment inner error" data-page="'+page+'">Load error.</div>');
		}
	});
}

function render_comment_div(comment) {
	var div = '<div class="comment-entry" data-id="' + comment.id + '">\
      <a href="' + comment.creator.space_url + '" target="_blank">\
        <img class="comment-img" src="' + comment.creator.avatar_url_small + '">\
      </a>\
      <div class="comment-detail-box">\
        <div class="user-title-line">\
          <label class="floorth">#'+ comment.floorth +'</label>\
          <a class="blue-link user-name" href="' + comment.creator.space_url + '" target="_blank">' + comment.creator.nickname + '</a>\
          <label class="comment-time">' + comment.created + '</label>\
        </div>\
        <div class="comment-content">' + mention_link(comment.content) + '</div>\
        <div class="display-button comment"><span class="reply-display-text">Read more</span><span class="display-arrow"></span></div>\
        <div class="comment-operation-line">\
          <div class="comment-operation reply">Reply</div>\
          <div class="comment-operation report">Report</div>\
        </div>\
      </div>\
      <div class="inner-comment-container">'
    if (comment.inner_comments.length != 0) {
    	if (comment.inner_comment_counter > 3) {
    		div += '<div class="display-button replies"><span class="reply-display-text">View more replies (' + (comment.inner_comment_counter-3) + ')</span><span class="display-arrow"></span></div>'
    	}
    	for (var i = 0; i < comment.inner_comments.length; i++) {
	        div += render_inner_comment_div(comment.inner_comments[i])
        }
        div += '<div class="pagination-line replies"></div>'
    }
    div += '</div>'
    return div;
}

function render_inner_comment_div(inner_comment) {
	var div = '<div class="comment-entry inner">\
					<a href="' + inner_comment.creator.space_url + '" target="_blank">\
			          <img class="comment-img" src="' + inner_comment.creator.avatar_url_small + '">\
			        </a>\
			        <div class="comment-detail-box inner">\
			        	<div class="user-title-line">\
			              <a class="blue-link user-name" href="' + inner_comment.creator.space_url + '" target="_blank">' + inner_comment.creator.nickname + '</a>\
			              <label class="comment-time">' + inner_comment.created + '</label>\
			            </div>\
			            <div class="comment-content">' + inner_comment.content + '</div>\
			            <div class="display-button comment"><span class="reply-display-text">Read more</span><span class="display-arrow"></span></div>\
						<div class="comment-operation-line">\
				          <div class="comment-operation reply">Reply</div>\
				          <div class="comment-operation report">Report</div>\
				        </div>\
			        </div>\
		        </div>'
	return div;
}

function mention_link(content) {
	var state = 0;
	var new_content = '';
	var part_content = '';
	var puncts = /[@.,?!;:/\\"']/;
	for (var i = 0; i < content.length; i++) {
		if (content[i] === '@' && state == 0) {
			state = 1;
			part_content += content[i];
		} else if (puncts.test(content[i]) && state == 1) {
			state = 0;
		} else if (state == 1) {
			part_content += content[i]
		} else if (state == 0) {
			new_content += content[i]
		}
	}
	return content;
}
