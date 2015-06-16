var player;
var isPlaying = false;
var player_width = 640;
var player_height = 446;
var danmakuVar = null;
var progressVar = null;
var progressHold = false;
var autoSwitch = false;
var isLoop = false;
var danmaku = [];
var danmaku_pointer = 0;
var danmaku_list = [];
var danmaku_elements = [];
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
var danmaku_opacity = 1;
var show_top = true;
var show_bottom = true;
var show_colored = true;
var show_danmaku = true;
var switch_count_down;
var ori_danmaku_speed = 4;
var danmaku_speed = 4;
var ori_existing_time = 5;
var existing_time = 5;
var ori_max_danmaku = 60;
var max_danmaku = 60;
var ori_danmaku_scale = 3;
var danmaku_scale = 3;
var has_text_outline = 1;
var hide_controls = 1;
var ori_danmaku_font = 'Times New Roman';
var danmaku_font = 'Times New Roman';
var block_rules = [];
var url_suffix = window.location.href.split('/').last();
var video_id = window.location.pathname.substr(window.location.pathname.lastIndexOf('/dt') + 3);

function onPlayerStateChange(event) {
	if (event.data == YT.PlayerState.PLAYING) {
		isPlaying = true;
		if (danmakuVar == null) {
			danmakuVar = setInterval(danmaku_update, danmaku_check_interval*1000);
		}
		if (progressVar == null) {
			progressVar = setInterval(progress_update, 500);
		}
		if (switch_count_down != null) {
			stop_switch_count_down();
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
		var button = document.getElementById("play-pause-button");
		button.setAttribute("class", "play");

		if (isLoop) {
			player.playVideo();
		} else if (autoSwitch && $('a.episode-link.active').length != 0 && $('a.episode-link.active').next().length != 0) {
			auto_switch_count_down();
		} else {
			clearInterval(danmakuVar);
			clearInterval(progressVar);
			danmakuVar == null;
			progressVar == null;
		}
	}
}

function auto_switch_count_down() {
	var count_down = 5;
	var one_down = function() {
		console.log('one down '+count_down)
		if (count_down > 0) {
			$('#switch-count-span').text('Switch to the next part in '+count_down+' seconds.');
	        count_down -= 1;
	        switch_count_down = setTimeout(one_down, 1000);
    	} else {
    		window.location.href = $('a.episode-link.active').next().attr('href')+"&autoplay=1";
    	}
	}

	$('#switch-count-down').removeClass('hidden');
	$('#switch-count-span').text('Switch to the next part in '+count_down+' seconds.');
	count_down -= 1;
	switch_count_down = setTimeout(one_down, 1000);
}

function stop_switch_count_down() {
	clearTimeout(switch_count_down);
	switch_count_down = null;
	$('#switch-count-down').addClass('hidden');
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
	setCookie('player_volume', len/volume.offsetHeight*100);
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
	var danmaku_controller = document.getElementById("danmaku-controller");
	if ($(danmaku_controller).hasClass('on')) {
		$(danmaku_controller).addClass('off');
		$(danmaku_controller).removeClass('on');
		show_danmaku = false;
		danmaku_all_clear();
	} else {//off
		$(danmaku_controller).addClass('on');
		$(danmaku_controller).removeClass('off');
		show_danmaku = true;
	}
}

function widescreen_switch(evt) {
	if($('#full-screen').hasClass('on') || $('#page-wide').hasClass('on')) return;

	if ($(evt.target).hasClass('on')) {
		$(evt.target).removeClass('on');
		$(evt.target).addClass('off');
		
	} else {//off
		$(evt.target).removeClass('off');
		$(evt.target).addClass('on');
	}
	widescreen_change();
}

function widescreen_change() {
	if ($('#wide-screen').hasClass('on')) {
		$("#danmaku-pool").addClass('hidden');
		player_width = 1024;
		player_height = 576;
		player.setSize(player_width, player_height);
		$('.player-vertical-padding')[0].style.height = player_height+"px";
		var player_controller = document.getElementById("player-controller");
		player_controller.style.width = player_width+"px";
		var danmaku_input = document.getElementById("danmaku-input");
		if ($('.input-layon-block').hasClass('hidden')) {
			danmaku_input.style.width = "920px";
		} else {
			danmaku_input.style.width = "888px";
		}
		var player_canvas = document.getElementById("player-canvas");
		player_canvas.style.width = player_width+"px";
		player_canvas.style.height = player_height+"px";

		var list = document.querySelectorAll("div.danmaku");
		for (var i = 0; i < list.length; ++i) {
		   list[i].style.left = player_width+10+"px";
		}
	} else {
		$("#danmaku-pool").removeClass('hidden');
		player_width = 640;
		player_height = 446;
		var player_inner_width = player_width;
		var player_inner_height = 360;
		player.setSize(player_inner_width, player_inner_height);
		$('.player-vertical-padding')[0].style.height = player_height+"px";
		var player_controller = document.getElementById("player-controller");
		player_controller.style.width = player_width+"px";
		var danmaku_input = document.getElementById("danmaku-input");
		if ($('.input-layon-block').hasClass('hidden')) {
			danmaku_input.style.width = "536px";
		} else {
			danmaku_input.style.width = "504px";
		}
		var player_canvas = document.getElementById("player-canvas");
		player_canvas.style.width = player_inner_width+"px";
		player_canvas.style.height = player_inner_height+"px";

		var list = document.querySelectorAll("div.danmaku");
		for (var i = 0; i < list.length; ++i) {
		   list[i].style.left = player_width+10+"px";
		}
	}
}

function fullscreen_change(evt) {
	if ($('#full-screen').hasClass('on')) {
		$('#full-screen').addClass('off');
		$('#full-screen').removeClass('on');

		$('#page-wide').removeClass('on');
		$('#page-wide').addClass('off');
		var player_container = document.getElementById('player-container');
		player_container.style.position = 'relative';
		$('#progress-controller-wrap')[0].style.position = 'static';
		$('#progress-controller-wrap').off('mouseenter mouseleave');
		$(window).off('resize', page_wide_player);
		
		widescreen_change();
	} else {//off
		$('#full-screen').addClass('on');
		$('#full-screen').removeClass('off');
		player_width = screen.width;
		if (!hide_controls) {
			player_height = screen.height - $('#progress-controller-wrap').height();
		} else {
			player_height = screen.height - $('#progress-bar-background').outerHeight();
			var wrap = document.getElementById('progress-controller-wrap');
			wrap.style.position = 'absolute';
			$(wrap).hover(function() {
				wrap.style.bottom = - $('#progress-bar-background').height()+'px';
			}, function() {
				wrap.style.bottom = - wrap.offsetHeight + 'px';
			});
			wrap.style.bottom = - wrap.offsetHeight + 'px';
		}
		$("#danmaku-pool").addClass('hidden');
		var player_inner_width = player_width;
		var player_inner_height = player_height;
		if (player_inner_height/9*16 < player_inner_width) {
			player_inner_width = Math.round(player_inner_height/9*16);
		} else {
			player_inner_height = Math.round(player_inner_width/16*9);
		}
		player.setSize(player_inner_width, player_inner_height);
		$('.player-vertical-padding')[0].style.height = player_height+"px";
		var player_controller = document.getElementById("player-controller");
		player_controller.style.width = player_width+'px';
		var danmaku_input = document.getElementById("danmaku-input");
		if ($('.input-layon-block').hasClass('hidden')) {
			danmaku_input.style.width = (player_width - 26*2 - 50 - 2) + 'px';
		} else {
			danmaku_input.style.width = (player_width - 26*2 - 50 - 2 - 32) + 'px';
		}
		var player_canvas = document.getElementById("player-canvas");
		player_canvas.style.width = player_inner_width+"px";
		player_canvas.style.height = player_inner_height+"px";

		var list = document.querySelectorAll("div.danmaku");
		for (var i = 0; i < list.length; ++i) {
		   list[i].style.left = player_width+10+"px";
		}
	}
}

function fullscreen_switch(evt) {
	// var isInFullScreen = document.fullScreenElement ||  document.mozFullScreen || document.webkitIsFullScreen || document.msIsFullScreen;
	if($('#full-screen').hasClass('on')) {
    	// browser is almost certainly fullscreen
		var requestMethod = document.msExitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen || document.exitFullscreen || document.cancelFullScreen;
        if (requestMethod) { // cancel full screen.
            requestMethod.call(document);
        } else if (typeof window.ActiveXObject !== "undefined") { // Older IE.
            var wscript = new ActiveXObject("WScript.Shell");
            if (wscript !== null) {
                wscript.SendKeys("{F11}");
            }
        }
	} else {
		var player_container = document.getElementById('player-container');
		var requestMethod = player_container.requestFullScreen || player_container.webkitRequestFullscreen || player_container.mozRequestFullScreen || player_container.msRequestFullscreen;
	    if (requestMethod) { // Native full screen.
	        requestMethod.call(player_container);
	    } else if (typeof window.ActiveXObject !== "undefined") { // Older IE.
	        var wscript = new ActiveXObject("WScript.Shell");
	        if (wscript !== null) {
	            wscript.SendKeys("{F11}");
	        }
	    }
	}
}

function page_wide_player() {
	player_width = $('body').innerWidth();
	player_height = window.innerHeight - $('#progress-controller-wrap').height();
	$("#danmaku-pool").addClass('hidden');
	var player_inner_width = player_width;
	var player_inner_height = player_height;
	if (player_inner_height/9*16 < player_inner_width) {
		player_inner_width = Math.round(player_inner_height/9*16);
	} else {
		player_inner_height = Math.round(player_inner_width/16*9);
	}
	player.setSize(player_inner_width, player_inner_height);
	$('.player-vertical-padding')[0].style.height = player_height+"px";
	var player_controller = document.getElementById("player-controller");
	player_controller.style.width = player_width+'px';
	var danmaku_input = document.getElementById("danmaku-input");
	if ($('.input-layon-block').hasClass('hidden')) {
		danmaku_input.style.width = (player_width - 26*2 - 50 - 2) + 'px';
	} else {
		danmaku_input.style.width = (player_width - 26*2 - 50 - 2 - 32) + 'px';
	}
	var player_canvas = document.getElementById("player-canvas");
	player_canvas.style.width = player_inner_width+"px";
	player_canvas.style.height = player_inner_height+"px";

	var list = document.querySelectorAll("div.danmaku");
	for (var i = 0; i < list.length; ++i) {
	   list[i].style.left = player_width+10+"px";
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
	document.onmouseup = progress_bar_stop;
	document.onmouseout = progress_bar_stop;
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
}

function progress_bar_stop(evt) {
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

	danmaku_all_clear();

	player.seekTo(num, true);
	document.onmousemove = null;
	document.onmouseup = null;
	document.onmouseout = null;

	progressHold = false;
}

function buffer_update() {
	// console.log('buffer_update:'+player.getVideoLoadedFraction());
	var buffered = player.getVideoLoadedFraction();
	var progress_buffered = document.getElementById("progress-bar-buffered");
	progress_buffered.style.width = buffered*100+'%';
}

function progress_update() {
	// console.log('progress_update');
	var progress_number = document.getElementById("progress-number");
	var splits = progress_number.lastChild.nodeValue.split('/');
	progress_number.lastChild.nodeValue = secondsToTime(player.getCurrentTime())+"/"+splits[1];
	if (!progressHold) {
		var progress_played = document.getElementById("progress-bar-played");
		progress_played.style.width = player.getCurrentTime()/player.getDuration()*100+'%';
	}

	var cur_quality = quality_youtube2local(player.getPlaybackQuality());
	if (typeof cur_quality !== 'undefined') {
		var quality = $('.list-selected.quality').text().replace(/ \(.*\)/g, '');
		$('.list-selected.quality').text(quality+' ('+cur_quality+')');
	}
}

function Danmaku_Animation(ele) {
	var lTime = 0;
	var existingTime = existing_time*1000;
	var type = ele.ref_danmaku.type;
	var offsetWidth = ele.element.offsetWidth;
	var offsetHeight = ele.element.offsetHeight;
	var direct_x, direct_y;

	function get_positionX(x) {
		if (x < 0) return offsetWidth + player_width + x;
		else return x;
	}

	function get_positionY(y) {
		if (y < 0) return offsetHeight + player_width + y;
		else return y;
	}

	this.startAnimation = function() {
		lTime = Date.now();
		if (type === 'RightToLeft') {
			requestAnimationFrame(float_update);
		} else if (type === 'Top' || type === 'Bottom') {
			ele.posX = (player_width + offsetWidth)/2;
			ele.element.style.WebkitTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			ele.element.style.msTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			ele.element.style.transform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			requestAnimationFrame(staying_update);
		} else if (type === 'Advanced') {
			ele.posX = get_positionX(ele.ref_danmaku.birth_x);
			ele.posY = get_positionY(ele.ref_danmaku.birth_y);
			var death_x = get_positionX(ele.ref_danmaku.death_x);
			var death_y = get_positionY(ele.ref_danmaku.death_y);

			if (death_x > ele.posX) direct_x = 1;
			else if (death_x < ele.posX) direct_x = -1;
			else direct_x = 0;

			if (death_y > ele.posY) direct_y = 1;
			else if (death_y < ele.posY) direct_y = -1;
			else direct_y = 0;

			if (ele.ref_danmaku.longevity != 0) {
				existingTime = ele.ref_danmaku.longevity*1000;
			}
			requestAnimationFrame(advanced_update);
		}
	}

	function float_update() {
		var curTime = Date.now();
		var deltaTime = curTime - lTime;
		var speed = (100*danmaku_speed + 400 + offsetWidth)/10;
		lTime = curTime;
		if (isPlaying) {
			ele.posX += speed*deltaTime/1000;
			ele.element.style.WebkitTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			ele.element.style.msTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			ele.element.style.transform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
		}
		
		// console.log(index+' '+percent)
		if (ele.generating && (ele.clear_request || ele.posX > offsetWidth + 20)) {
			ele.generating = false;
			for (var j = ele.posY; j < ele.element.offsetHeight + ele.posY; j++) {
				occupation_normal[j] -= 1;
			}
		}

		if (!ele.clear_request && ele.posX < offsetWidth + player_width + 10) {
			requestAnimationFrame(float_update);
		} else {
			ele.element.style.WebkitTransform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.element.style.msTransform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.element.style.transform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.idle = true;
			ele.posX = 0;
		}
	}

	function staying_update() {
		var curTime = Date.now();
		var deltaTime = curTime - lTime;
		lTime = curTime;
		if (isPlaying) {
			existingTime -= deltaTime;
		}

		if (!ele.clear_request && existingTime > 0) {
			requestAnimationFrame(staying_update);
		} else {
			ele.generating = false;
			if (type === 'Top') {
				occupation = occupation_top;
			} else if (type === 'Bottom') {
				occupation = occupation_bottom;
			}
			for (var j = ele.posY; j < ele.element.offsetHeight + ele.posY; j++) {
				occupation[j] -= 1;
			}
			// console.log(type+': '+occupation)
			ele.element.style.WebkitTransform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.element.style.msTransform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.element.style.transform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.idle = true;
			ele.posX = 0;
		}
	}

	function advanced_update() {
		var curTime = Date.now();
		var deltaTime = curTime - lTime;
		var speed = ele.ref_danmaku.speed;
		lTime = curTime;

		var death_x = get_positionX(ele.ref_danmaku.death_x);
		var death_y = get_positionY(ele.ref_danmaku.death_y);
		if (isPlaying) {
			existingTime -= deltaTime;
			ele.posX += direct_x*ele.ref_danmaku.speed_x*deltaTime/1000;
			ele.posY += direct_y*ele.ref_danmaku.speed_y*deltaTime/1000;
			ele.element.style.WebkitTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			ele.element.style.msTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
			ele.element.style.transform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
		}

		if (!ele.clear_request 
			&& (ele.ref_danmaku.longevity == 0 || (ele.ref_danmaku.longevity != 0 && existingTime > 0))
			&& ele.posX*direct_x <= death_x*direct_x 
			&& ele.posY*direct_y <= death_y*direct_y) {
			requestAnimationFrame(advanced_update);
		} else {
			// console.log(type+': '+occupation)
			ele.element.style.WebkitTransform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.element.style.msTransform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.element.style.transform = "translate(-"+0+"px, "+ele.posY+"px)";
			ele.idle = true;
			ele.posX = 0;
		}
	}
}

function danmaku_all_clear() {
	for (var i = 0; i < danmaku_elements.length; i++) {
		var ele = danmaku_elements[i];
		if (!ele.idle) {
			ele.clear_request = true;
		}
	}
}

function change_show_top_danmaku(show) {
	show_top = show;
	if (!show_top) {
		for (var i = 0; i < danmaku_elements.length; i++) {
			var ele = danmaku_elements[i];
			if (!ele.idle && ele.ref_danmaku.type === 'Top') {
				ele.clear_request = true;
			}
		}
		for (var i = 0; i < danmaku.length; i++) {
			if (danmaku[i].type === 'Top') {
				danmaku[i].blocked = true;
			}
		}
	} else {
		for (var i = 0; i < danmaku.length; i++) {
			if (danmaku[i].type === 'Top' && !danmaku_filter(i)) {
				danmaku[i].blocked = false;
			}
		}
	}
	refresh_danmaku_pool();
}

function change_show_bottom_danmaku(show) {
	show_bottom = show;
	if (!show_bottom) {
		for (var i = 0; i < danmaku_elements.length; i++) {
			var ele = danmaku_elements[i];
			if (!ele.idle && ele.ref_danmaku.type === 'Bottom') {
				ele.clear_request = true;
			}
		}
		for (var i = 0; i < danmaku.length; i++) {
			if (danmaku[i].type === 'Bottom') {
				danmaku[i].blocked = true;
			}
		}
	} else {
		for (var i = 0; i < danmaku.length; i++) {
			if (danmaku[i].type === 'Bottom' && !danmaku_filter(i)) {
				danmaku[i].blocked = false;
			}
		}
	}
	refresh_danmaku_pool();
}

function change_show_colored_danmaku(show) {
	show_colored = show;
	if (!show_colored) {
		for (var i = 0; i < danmaku_elements.length; i++) {
			var ele = danmaku_elements[i];
			if (!ele.idle && ele.ref_danmaku.type !== 'Advanced' && ele.ref_danmaku.color.toString(16) !== 'ffffff') {
				ele.clear_request = true;
			}
		}
		for (var i = 0; i < danmaku.length; i++) {
			if (danmaku[i].type !== 'Advanced' && danmaku[i].color.toString(16) !== 'ffffff') {
				danmaku[i].blocked = true;
			}
		}
	} else {
		for (var i = 0; i < danmaku.length; i++) {
			if (danmaku[i].type !== 'Advanced' && danmaku[i].color.toString(16) !== 'ffffff' && !danmaku_filter(i)) {
				danmaku[i].blocked = false;
			}
		}
	}
	refresh_danmaku_pool();
}

function add_block_rule(block_type, block_content) {
	if (!block_content) return false;
	// console.log(block_content);
	$('.block-condition-input').val('');
	for (var i = 0; i < block_rules.length; i++) {
		if (block_type === block_rules[i].type && block_content === block_rules[i].content) {
			if (!block_rules[i].isOn) {
				block_rules[i].isOn = true;
				change_block_rule(i);
				setCookie('block-rules', JSON.stringify(block_rules), 0);
				$('.block-rule-entry:nth-child('+(i+1)+') .rule-status').removeClass('off').text('On');
			}
			return false;
		}
	}

	$('.block-list').append('<div class="block-rule-entry">\
      <div class="block-rule rule-type">' + block_type + '</div>\
      <div class="block-rule rule-content" title="' + block_content + '">' + block_content + '</div>\
      <div class="block-rule rule-status">On</div>\
      <div class="block-rule rule-delete"></div>\
    </div>');
    block_rules.push({type: block_type, content: block_content, isOn: true});
	change_block_rule(block_rules.length-1);
    setCookie('block-rules', JSON.stringify(block_rules), 0);
	return false;
}

function change_block_rule(index) {
	if (block_rules[index].isOn) {
		for (var i = 0; i < danmaku_elements.length; i++) {
			var ele = danmaku_elements[i];
			if (ele.idle) continue;

			if (block_rules[index].type === 'Keywords') {
				if (ele.element.lastChild.nodeValue.indexOf(block_rules[index].content) > -1) {
					ele.clear_request = true;
				}
			} else if (block_rules[index].type === 'RegExp') {
				var regex = new RegExp(block_rules[index].content);
				if (regex.test(ele.element.lastChild.nodeValue)) {
					ele.clear_request = true;
				}
			} else if (block_rules[index].type === 'User') {
				if (ele.ref_danmaku.creator.toString() === block_rules[index].content) {
					ele.clear_request = true;
				}
			}
		}
		for (var j = 0; j < danmaku.length; j++) {
			if (single_rule_filter(j, index)) {
				danmaku[j].blocked = true;
			}
		}
	} else {
		for (var j = 0; j < danmaku.length; j++) {
			if (single_rule_filter(j, index) && !danmaku_filter(j)) {
				danmaku[j].blocked = false;
			}
		}
	}
	refresh_danmaku_pool();
}

function danmaku_filter(danmaku_pointer) {// return true to filter.
	if ((danmaku[danmaku_pointer].type === 'Top' && !show_top) || 
		(danmaku[danmaku_pointer].type === 'Bottom' && !show_bottom) ||
		(danmaku[danmaku_pointer].type !== 'Advanced' && !show_colored && danmaku[danmaku_pointer].color.toString(16) != 'ffffff' )) {
		return true;
	} else {
		for (var i = 0; i < block_rules.length; i++) {
			if (!block_rules[i].isOn) continue;
			if (single_rule_filter(danmaku_pointer, i)) {
				return true;
			}
		}
		return false;
	}
}

function single_rule_filter(danmaku_pointer, i) {
	if (block_rules[i].type === 'Keywords') {
		if (danmaku[danmaku_pointer].content.indexOf(block_rules[i].content) > -1) {
			return true;
		}
	} else if (block_rules[i].type === 'RegExp') {
		var regex = new RegExp(block_rules[i].content);
		if (regex.test(danmaku[danmaku_pointer].content)) {
			return true;
		}
	} else if (block_rules[i].type === 'User') {
		if (danmaku[danmaku_pointer].creator.toString() === block_rules[i].content) {
			return true;
		}
	}
	return false;
}

function change_danmaku_outline() {
	if (has_text_outline) {
		for (var i = 0; i < danmaku_elements.length; i++) {
			var ele = danmaku_elements[i];
			if (!ele.idle) {
				var outline_color = reverse_color(ele.ref_danmaku.color);
				ele.element.style.textShadow = '1px 0 1px '+outline_color+', -1px 0 1px '+outline_color+', 0 1px 1px '+outline_color+', 0 -1px 1px '+outline_color;
			}
		}
	} else {
		for (var i = 0; i < danmaku_elements.length; i++) {
			var ele = danmaku_elements[i];
			if (!ele.idle) {
				ele.element.style.textShadow = '0 0 0';
			}
		}
	}
}

function reverse_color(color) {
	var b = color%256;
	var g = Math.floor(color/256)%256;
	var r = Math.floor(color/256/256)%256;
	var grey = Math.floor((r+g+b)/3);
	var reverse;
	if (grey < 50) {
		reverse = 'rgb(255, 255, 255)';
	} else {
		reverse = 'rgb(0, 0, 0)';
	}
	return reverse;
}

function danmaku_update() {
	// console.log('danmaku_update:'+player.getCurrentTime());
	if (danmaku.length == 0 || !show_danmaku) return;

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
	
	for (var i = 0; i < max_danmaku; i++) {
		var ele = danmaku_elements[i];
		if (!ele.idle) continue;

		while (danmaku_pointer < danmaku.length && danmaku[danmaku_pointer].timestamp <= curTime && danmaku[danmaku_pointer].blocked) {
			danmaku_pointer++;
		}
		if (danmaku_pointer >= danmaku.length || danmaku[danmaku_pointer].timestamp > curTime) break;

		ele.ref_danmaku = danmaku[danmaku_pointer];
		danmaku_pointer++;

		ele.idle = false;
		ele.clear_request = false;
		if (ele.ref_danmaku.type === 'Advanced') {
			ele.element.setAttribute('data-index', i);
			ele.element.lastChild.nodeValue = ele.ref_danmaku.content;
			ele.element.setAttribute('style', ele.ref_danmaku.css);
		} else {
			ele.element.setAttribute('data-index', i);
			ele.element.lastChild.nodeValue = ele.ref_danmaku.content;
			ele.element.setAttribute('style', '');
			ele.element.style.opacity = danmaku_opacity;
			ele.element.style.color = '#'+('000000'+ele.ref_danmaku.color.toString(16)).substr(-6);
			if (has_text_outline) {
				var outline_color = reverse_color(ele.ref_danmaku.color);
				ele.element.style.textShadow = '1px 0 1px '+outline_color+', -1px 0 1px '+outline_color+', 0 1px 1px '+outline_color+', 0 -1px 1px '+outline_color;
			}
			ele.element.style.fontSize = ele.ref_danmaku.size*danmaku_scale/3+'px';
			ele.element.style.fontFamily = danmaku_font;
			// ele.element.lastChild.nodeValue = secondsToTime(ele.ref_danmaku.timestamp);
			ele.generating = true;

			if (ele.ref_danmaku.type === 'RightToLeft') {
				accumulate = accumulate_normal;
				occupation = occupation_normal;
			} else if (ele.ref_danmaku.type === 'Bottom') {
				accumulate = accumulate_bottom;
				occupation = occupation_bottom;
			} else if (ele.ref_danmaku.type === 'Top') {
				accumulate = accumulate_top;
				occupation = occupation_top;
			}
			accumulate[0] = 0;
			for (var z = 0; z < ele.element.offsetHeight && z < player_height; z++) {
				accumulate[0] += occupation[z];
			}
			for (var j = 1; j < player_height - ele.element.offsetHeight + 1; j++) {
				accumulate[j] = accumulate[j-1];
				accumulate[j] -= occupation[j-1];
				accumulate[j] += occupation[j+ele.element.offsetHeight-1];
			}

			var min_value = 2000000;
			var min_line = 0;
			for (var j = 0; j < player_height - ele.element.offsetHeight + 1; j++) {
				if ((ele.ref_danmaku.type === 'Bottom' && accumulate[j] <= min_value)
					|| (ele.ref_danmaku.type != 'Bottom' && accumulate[j] < min_value)) {
					min_value = accumulate[j];
					min_line = j;
				}
			}

			ele.posY = min_line;
			for (var j = ele.posY; j < ele.element.offsetHeight + ele.posY; j++) {
				occupation[j] += 1;
			}
		}
		var danmaku_Animation = new Danmaku_Animation(ele);
		danmaku_Animation.startAnimation();
	}
	lastTime = curTime;
}

function onPlayerReady(event) {
	var progress_number = document.getElementById("progress-number");
	progress_number.lastChild.nodeValue = "00:00"+"/"+secondsToTime(player.getDuration());
	setInterval(buffer_update, 500);
	buffer_update();
	progress_update();

	var volume = getCookie('player_volume');
	if (!volume) {
		player.setVolume(50);
		setCookie('player_volume', 50);
		var volume_magnitude = document.getElementById("volume-magnitude");
		volume_magnitude.style.height = 25 + "px";
		var volume_pointer = document.getElementById("volume-pointer");
		volume_pointer.style.WebkitTransform = "translateY(-"+25+"px)";
		volume_pointer.style.msTransform = "translateY(-"+25+"px)";
		volume_pointer.style.transform = "translateY(-"+25+"px)";
		var volume_tip = document.getElementById("volume-tip");
		volume_tip.style.WebkitTransform = "translateY(-"+25+"px)";
		volume_tip.style.msTransform = "translateY(-"+25+"px)";
		volume_tip.style.transform = "translateY(-"+25+"px)";
		volume_tip.lastChild.nodeValue = 50;
	} else {
		volume = parseInt(volume);
		player.setVolume(volume);
		// var volume_bar = document.getElementById("volume-bar");
		var volume_magnitude = document.getElementById("volume-magnitude");
		var len = 50*volume/100;
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
		if (Math.floor(len/50*100) < 10) {
			text = "0"+Math.floor(len/50*100);
		} else {
			text = Math.floor(len/50*100);
		}
		volume_tip.lastChild.nodeValue = text;
	}

	var player_background = document.getElementById("player-background");
	for (var i = 0; i < 120; i++) {
		var bul = document.createElement('div');
		bul.setAttribute('class', 'danmaku');
		var text = document.createTextNode('sdfsdfs');
		bul.appendChild(text);
		player_background.appendChild(bul);
		danmaku_elements.push({idle: true, generating: false, posX: 0, posY: 0, clear_request: false, element: bul, ref_danmaku: null});
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
	player_background.addEventListener("click", video_toggle);
	$('div.danmaku').click(video_toggle);

	$('#backward-button').click(function() {
		var time = Math.max(player.getCurrentTime() - 3, 0);
		player.seekTo(time, true);
	});
	$('#forward-button').click(function() {
		var time = Math.min(player.getCurrentTime() + 3, player.getDuration());
		player.seekTo(time, true);
	});

	var volume_button = document.getElementById("volume-switch");
	volume_button.addEventListener("click", volume_switch);
	var volume = document.getElementById("volume-background");
	volume.addEventListener("mousedown", volume_start);

	var danmaku_button = document.getElementById("danmaku-switch");
	danmaku_button.addEventListener("click", danmaku_switch);

	var wide_button = document.getElementById("wide-screen");
	wide_button.addEventListener("click", widescreen_switch);

	var full_button = document.getElementById("full-screen");
	full_button.addEventListener("click", fullscreen_switch);
	player_background.addEventListener("dblclick", fullscreen_switch);
	document.addEventListener("fullscreenchange", fullscreen_change, false);      
	document.addEventListener("webkitfullscreenchange", fullscreen_change, false);
	document.addEventListener("mozfullscreenchange", fullscreen_change, false);
	document.addEventListener("MSFullscreenChange", fullscreen_change, false);

	$('#page-wide').click(function() {
		if ($('#full-screen').hasClass('on')) return;

		if ($(this).hasClass('on')) {
			$(this).removeClass('on');
			$(this).addClass('off');
			var player_container = document.getElementById('player-container');
			player_container.style.position = 'relative';
			$(window).off('resize', page_wide_player);

			widescreen_change();
		} else {
			$(this).removeClass('off');
			$(this).addClass('on');
			var player_container = document.getElementById('player-container');
			player_container.style.position = 'fixed';

			$(window).resize(page_wide_player);
			page_wide_player();
		}
	});

	var progress_bar = document.getElementById("progress-bar");
	progress_bar.addEventListener("mousedown", progress_bar_down);
	progress_bar.addEventListener("mouseover", progress_tip_show);
	progress_bar.addEventListener("mousemove", progress_tip_show);
	progress_bar.addEventListener("mouseout", progress_tip_hide);

	var progress_bar_played = document.getElementById("progress-bar-played");
	progress_bar_played.style.width = "0";
	var progress_buffered = document.getElementById("progress-bar-buffered");
	progress_buffered.style.width = "0";

	var time_title = document.getElementById("time");
	time_title.addEventListener("click", time_order_change);
	var content_title = document.getElementById("content");
	content_title.addEventListener("click", content_order_change);
	var date_title = document.getElementById("date");
	date_title.addEventListener("click", date_order_change);

	$('#switch-cancel').click(stop_switch_count_down);

	{
		var opacity = getCookie('danmaku_opacity');
		if (opacity) {
			opacity = parseFloat(opacity);
			// var indicator = document.getElementById("opacity-indicator");
			var pointer = document.getElementById('opacity-pointer');
			var offset = (1 - opacity)*155;
			pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
			pointer.style.msTransform = "translateX(-"+offset+"px)";
			pointer.style.transform = "translateX(-"+offset+"px)";
			$('div.danmaku').css('opacity', opacity);
			danmaku_opacity = opacity;
		}
	}
	$('#opacity-indicator').mousedown(function(evt) {
		var move_pointer = function(evt) {
			var indicator = document.getElementById("opacity-indicator");
			var rect = indicator.getBoundingClientRect();
			var offset = rect.right - evt.clientX;
			if (offset < 0) {
				offset = 0;
			}
			if (offset > indicator.offsetWidth) {
				offset = indicator.offsetWidth;
			}
			var pointer = document.getElementById('opacity-pointer');
			pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
			pointer.style.msTransform = "translateX(-"+offset+"px)";
			pointer.style.transform = "translateX(-"+offset+"px)";
			var opacity = 1 - offset/indicator.offsetWidth;
			if (danmaku_opacity != opacity) {
				$('div.danmaku').css('opacity', opacity);
			}
			setCookie('danmaku_opacity', opacity, 0);
		}
		var stop_move = function() {
			$(document).off('mousemove', move_pointer);
			$(document).off('mouseup', stop_move);
			$(document).off('mouseout', stop_move);
		}
		$(document).mousemove(move_pointer);
		$(document).mouseup(stop_move);
		$(document).mouseout(stop_move);
	});

	$('#show-top-checkbox').click(function() {
		if ($('#show-top-checkbox').is(':checked')) {
			change_show_top_danmaku(true);
		} else {
			change_show_top_danmaku(false);
		}
	});
	$('#show-bottom-checkbox').click(function() {
		if ($('#show-bottom-checkbox').is(':checked')) {
			change_show_bottom_danmaku(true);
		} else {
			change_show_bottom_danmaku(false);
		}
	});
	$('#show-colored-checkbox').click(function() {
		if ($('#show-colored-checkbox').is(':checked')) {
			change_show_colored_danmaku(true);
		} else {
			change_show_colored_danmaku(false);
		}
	});

	$('#loop-switch').click(function() {
		if (isLoop == false) {
			isLoop = true;
		} else {
			isLoop = false;
		}
	});

	{
		var cookie_str = getCookie('autoSwitch');
		if (cookie_str && cookie_str === 'true') {
			autoSwitch = true;
		}
		if (autoSwitch) {
			$('#auto-switch').removeClass('off');
			$('#auto-switch').addClass('on');
		}
	}
	$('#auto-switch').click(function() {
		if (autoSwitch == false) {
			autoSwitch = true;
		} else {
			autoSwitch = false;
		}
		setCookie('autoSwitch', autoSwitch, 0);
	});

	{
		var cookie_str = getCookie('danmaku_font');
		if (cookie_str) danmaku_font = cookie_str;
		$('.list-option.font.active').removeClass('active');
		var font_list = $('.list-option.font');
		for (var i = 0; i < font_list.length; i++) {
			if ($(font_list[i]).text() === danmaku_font) {
				$(font_list[i]).addClass('active');
				break;
			}
		}
		$('.list-selected.font').text(danmaku_font);
	}
	$('.setting-reset-button.font').click(function() {
		danmaku_font = ori_danmaku_font;
		setCookie('danmaku_font', danmaku_font, 0);
		$('.list-option.font.active').removeClass('active');
		var font_list = $('.list-option.font');
		for (var i = 0; i < font_list.length; i++) {
			if ($(font_list[i]).text() === danmaku_font) {
				$(font_list[i]).addClass('active');
				break;
			}
		}
		$('.list-selected.font').text(danmaku_font);
	});

	$(document).click(function() {
		$('.list-selection').addClass('hidden');
	});
	$('.list-selected').click(function(evt) {
		evt.stopPropagation();
        var list = $(this).siblings('.list-selection');
        if (list.hasClass('hidden')) {
        	$('.list-selection').addClass('hidden');
            list.removeClass('hidden');
        } else {
            list.addClass('hidden');
        }
    });
    $('.list-option').click(function(evt) {
    	evt.stopPropagation();
    	if ($(this).hasClass('quality')) {
    		player.setPlaybackQuality(quality_local2youtube($(this).text()));
    	} else if ($(this).hasClass('speed')) {
    		player.setPlaybackRate(parseFloat($(this).text()));
    	} else if ($(this).hasClass('font')) {
    		danmaku_font = $(this).text();
    		setCookie('danmaku_font', danmaku_font, 0);
    	}

        var selection = $(this).parent();
        selection.siblings('.list-selected').text($(this).text());
        $(this).siblings().removeClass('active');
        $(this).addClass('active');
        selection.addClass('hidden');
    });

    $('.danmaku-pool-setting').click(function() {
    	if ($(this).hasClass('player')) {
    		$('.player-full-setting.player').removeClass('hidden');
    	} else if ($(this).hasClass('block')) {
    		$('.player-full-setting.block').removeClass('hidden');
    	} else if ($(this).hasClass('special')) {
    		$('.player-full-setting.special').removeClass('hidden');
    	} else if ($(this).hasClass('tab')) {
    		$('.danmaku-pool-setting.tab.selected').addClass('unselected').removeClass('selected');
    		$(this).addClass('selected').removeClass('unselected');
    		$('.special-danmaku-setting').addClass('hidden');
    		if ($(this).hasClass('advanced')) {
    			$('.special-danmaku-setting.advanced').removeClass('hidden')
    		} else if ($(this).hasClass('subtitle')) {
    			$('.special-danmaku-setting.subtitle').removeClass('hidden')
    		} else if ($(this).hasClass('code')) {
    			$('.special-danmaku-setting.code').removeClass('hidden')
    		}
    	}
    });
    $('.player-setting-go-back').click(function() {
    	$(this).parent().parent().addClass('hidden');
    });

    $('.number-adjust-bar').each(function() {
    	var bar = $(this)[0];
    	var offset = 0;
    	if ($(bar).hasClass('speed')) {
    		var cookie_str = getCookie('danmaku_speed');
    		if (cookie_str) danmaku_speed = parseInt(cookie_str);
			$(bar).prev().text(danmaku_speed);
			offset = (1 - (danmaku_speed - 1)/7)*300;
		} else if ($(bar).hasClass('danmaku-num')) {
			var cookie_str = getCookie('max_danmaku');
    		if (cookie_str) max_danmaku = parseInt(cookie_str);
			$(bar).prev().text(max_danmaku);
			offset = (1 - (max_danmaku - 10)/110)*300;
		} else if ($(bar).hasClass('scale')) {
			var cookie_str = getCookie('danmaku_scale');
    		if (cookie_str) danmaku_scale = parseInt(cookie_str);
			$(bar).prev().text(danmaku_scale);
			offset = (1 - (danmaku_scale - 1)/4)*300;
		} else if ($(bar).hasClass('time')) {
			var cookie_str = getCookie('existing_time');
    		if (cookie_str) existing_time = parseInt(cookie_str);
			$(bar).prev().text(existing_time);
			offset = (1 - (existing_time - 3)/5)*300;
		}
		var pointer = $(bar).children('.number-adjust-pointer')[0];
		pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
		pointer.style.msTransform = "translateX(-"+offset+"px)";
		pointer.style.transform = "translateX(-"+offset+"px)";
    });
    $('.number-adjust-bar').mousedown(function(evt) {
    	var bar = $(this)[0];
    	var move_pointer = function(evt) {
			var rect = bar.getBoundingClientRect();
			var offset = rect.right - evt.clientX;
			if (offset < 0) {
				offset = 0;
			}
			if (offset > bar.offsetWidth) {
				offset = bar.offsetWidth;
			}
			var pointer = $(bar).children('.number-adjust-pointer')[0];
			pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
			pointer.style.msTransform = "translateX(-"+offset+"px)";
			pointer.style.transform = "translateX(-"+offset+"px)";
			if ($(bar).hasClass('speed')) {
				danmaku_speed = Math.round((1 - offset/bar.offsetWidth)*7 + 1);
				$(bar).prev().text(danmaku_speed);
				setCookie('danmaku_speed', danmaku_speed, 0);
			} else if ($(bar).hasClass('danmaku-num')) {
				max_danmaku = Math.round((1 - offset/bar.offsetWidth)*110 + 10);
				$(bar).prev().text(max_danmaku);
				setCookie('max_danmaku', max_danmaku, 0);
			} else if ($(bar).hasClass('scale')) {
				danmaku_scale = Math.round((1 - offset/bar.offsetWidth)*4 + 1);
				$(bar).prev().text(danmaku_scale);
				setCookie('danmaku_scale', danmaku_scale, 0);
			} else if ($(bar).hasClass('time')) {
				existing_time = Math.round((1 - offset/bar.offsetWidth)*5 + 3);
				$(bar).prev().text(existing_time);
				setCookie('existing_time', existing_time, 0);
			}
		}
		move_pointer(evt);
    	var stop_move = function() {
			$(document).off('mousemove', move_pointer);
			$(document).off('mouseup', stop_move);
			// $(document).off('mouseout', stop_move);
		}
		$(document).mousemove(move_pointer);
		$(document).mouseup(stop_move);
		// $(document).mouseout(stop_move);
    });
	$('.setting-reset-button.number').click(function() {
		var bar = $(this).prev()[0];
    	var offset = 0;
    	if ($(bar).hasClass('speed')) {
    		danmaku_speed = ori_danmaku_speed;
			$(bar).prev().text(danmaku_speed);
			offset = (1 - (danmaku_speed - 1)/7)*bar.offsetWidth;
			setCookie('danmaku_speed', danmaku_speed, 0);
		} else if ($(bar).hasClass('danmaku-num')) {
			max_danmaku = ori_max_danmaku;
			$(bar).prev().text(max_danmaku);
			offset = (1 - (max_danmaku - 10)/110)*bar.offsetWidth;
			setCookie('max_danmaku', max_danmaku, 0);
		} else if ($(bar).hasClass('scale')) {
			danmaku_scale = ori_danmaku_scale;
			$(bar).prev().text(danmaku_scale);
			offset = (1 - (danmaku_scale - 1)/4)*bar.offsetWidth;
			setCookie('danmaku_scale', danmaku_scale, 0);
		} else if ($(bar).hasClass('time')) {
			existing_time = ori_existing_time;
			$(bar).prev().text(existing_time);
			offset = (1 - (existing_time - 3)/5)*bar.offsetWidth;
			setCookie('existing_time', existing_time, 0);
		}
		var pointer = $(bar).children('.number-adjust-pointer')[0];
		pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
		pointer.style.msTransform = "translateX(-"+offset+"px)";
		pointer.style.transform = "translateX(-"+offset+"px)";
	});

	$('.checkbox-selection').each(function() {
		if ($(this).hasClass('text-outline')) {
			var cookie_str = getCookie('text_outline');
    		if (cookie_str) has_text_outline = parseInt(cookie_str);
    		if (!has_text_outline) {
    			$(this).removeClass('on');
    			$(this).addClass('off');
    		}
		} else if ($(this).hasClass('hide-controls')) {
			var cookie_str = getCookie('hide_controls');
    		if (cookie_str) hide_controls = parseInt(cookie_str);
    		if (hide_controls) {
    			$(this).removeClass('off');
    			$(this).addClass('on');
    		}
		}
	});
	$('.checkbox-selection').click(function() {
		if ($(this).hasClass('text-outline')) {
			if ($(this).hasClass('off')) {
				has_text_outline = 0;
			} else {
				has_text_outline = 1;
			}
			setCookie('text_outline', has_text_outline, 0);
			change_danmaku_outline();
		} else if ($(this).hasClass('hide-controls')) {
			if ($(this).hasClass('off')) {
				hide_controls = 0;
			} else {
				hide_controls = 1;
			}
			setCookie('hide_controls', hide_controls, 0);
		}
	});
	
	{
		var cookie_str = getCookie('block-rules');
		if (cookie_str) {
			block_rules = JSON.parse(cookie_str);
		}
		for (var i = 0; i < block_rules.length; i++) {
			var div = '<div class="block-rule-entry">\
	          <div class="block-rule rule-type">' + block_rules[i].type + '</div>\
	          <div class="block-rule rule-content" title="' + block_rules[i].content + '">' + block_rules[i].content + '</div>'
	          if (block_rules[i].isOn) {
	          	div += '<div class="block-rule rule-status">On</div>'
	          } else {
	          	div += '<div class="block-rule rule-status off">Off</div>'
	          }
	          div += '<div class="block-rule rule-delete"></div>\
	        </div>'
			$('.block-list').append(div);
		}
		for (var j = 0; j < danmaku.length; j++) {
        	if (danmaku_filter(j)) {
        		danmaku[j].blocked = true;
        	}
        }
        refresh_danmaku_pool();
	}
	$('#add-rule-form').submit(function(evt) {
		var block_type = $('.list-selected.block').text();
		var block_content = $('.block-condition-input').val();
		return add_block_rule(block_type, block_content);
	});
	$('.block-list').on('click', '.block-rule.rule-status', function() {
		var entry = $(this).parent();
		var block_type = entry.children('.block-rule.rule-type').text();
		var block_content = entry.children('.block-rule.rule-content').text();
		if ($(this).hasClass('off')) {
			$(this).removeClass('off');
			$(this).text('On');
			for (var i = 0; i < block_rules.length; i++) {
				if (block_type === block_rules[i].type && block_content === block_rules[i].content) {
					block_rules[i].isOn = true;
					change_block_rule(i);
					setCookie('block-rules', JSON.stringify(block_rules), 0);
					break;
				}
			}
		} else {
			$(this).addClass('off');
			$(this).text('Off');
			for (var i = 0; i < block_rules.length; i++) {
				if (block_type === block_rules[i].type && block_content === block_rules[i].content) {
					block_rules[i].isOn = false;
					change_block_rule(i);
					setCookie('block-rules', JSON.stringify(block_rules), 0);
					break;
				}
			}
		}
	});
	$('.block-list').on('click', '.block-rule.rule-delete', function() {
		var entry = $(this).parent();
		var block_type = entry.children('.block-rule.rule-type').text();
		var block_content = entry.children('.block-rule.rule-content').text();
		for (var i = 0; i < block_rules.length; i++) {
			if (block_type === block_rules[i].type && block_content === block_rules[i].content) {
				if (block_rules[i].isOn) {
					block_rules[i].isOn = false;
					change_block_rule(i);
				}
				block_rules.splice(i, 1);
				setCookie('block-rules', JSON.stringify(block_rules), 0);
				break;
			}
		}
		entry.remove();
	});
	
	$('.number-input').on('input propertychange paste', function (e) {
		if (($(this).hasClass('negative') && /^[-]?\d*[.]?\d*$/.test($(this).val()))
			|| (!$(this).hasClass('negative') && /^\d*[.]?\d*$/.test($(this).val()))) { // is a number
			$(this).attr('data-old', $(this).val());
		} else { // not a number, preserve original value
			$(this).val($(this).attr('data-old'));
		}
    });
	$('.number-input-arrow').click(function() {
		var number_input = $(this).siblings('.number-input');
		var num = parseFloat(number_input.val());
		if (isNaN(num)) num = 0;

		num = Math.round(num*100);
		if ($(this).hasClass('up')) {
			num += 10;
		}
		if ($(this).hasClass('down') && (number_input.hasClass('negative') || num >= 10)) {
			num -= 10;
		}
		num /= 100;
		number_input.val(num);
	});
	
	$('div.danmaku').bind('contextmenu', function(evt) {
		evt.preventDefault();

		var ele = danmaku_elements[$(this).attr('data-index')];
		$('.danmaku-menu').attr('data-creator', ele.ref_danmaku.creator)
						.attr('data-index', $(this).attr('data-index'));

		var rect = $('#player-container').offset();
		$('.danmaku-menu').removeClass('hidden');
		$('.danmaku-menu')[0].style.left = evt.pageX - rect.left+'px';
		$('.danmaku-menu')[0].style.top = evt.pageY - rect.top+'px';
		var hide_menu = function() {
			$('.danmaku-menu').addClass('hidden');
			$(document).off('click', hide_menu);
		}
		$(document).click(hide_menu);
	});
	$('#danmaku-block-sender').click(function(e) {
		var block_type = 'User';
		var block_content = $('.danmaku-menu').attr('data-creator');
		add_block_rule(block_type, block_content);
	});
	$('#danmaku-locate-it').click(function(e) {
		var ele = danmaku_elements[$('.danmaku-menu').attr('data-index')];
		var danmaku_pool_index = danmaku_list.indexOf(ele.ref_danmaku);
		$('.per-bullet.selected').removeClass('selected');
		var target = $('.per-bullet')[danmaku_pool_index];
		target.classList.add('selected');
		$('#danmaku-list').scrollTop(target.offsetHeight*danmaku_pool_index);
	});
	$('#danmaku-reply').click(function(e) {
		if ($('.input-layon-block').hasClass('hidden')) {
			$('.input-layon-block').removeClass('hidden');
			var danmaku_input = document.getElementById('danmaku-input');
			danmaku_input.style.width = (danmaku_input.offsetWidth - 32) + 'px';
		}
		var reply_to = $('.danmaku-menu').attr('data-creator');
		$('#danmaku-reply-input').val(reply_to);
		$('#danmaku-input').focus();
	});
	$('.layon-close').click(function(e) {
		if (!$('.input-layon-block').hasClass('hidden')) {
			$('.input-layon-block').addClass('hidden');
			var danmaku_input = document.getElementById('danmaku-input');
			danmaku_input.style.width = (danmaku_input.offsetWidth + 32) + 'px';
		}
		$('#danmaku-reply-input').val('');
	});

	$('#advanced-danmaku-form input[type="button"]').click(function() {
		var error = advanced_danmaku_form_check();
		if (error) return;

		var preview_danmaku = {
			content: $('#advanced-danmaku-content').val().trim(),
			birth_x: parseFloat($('input[name="birth-position-X"]').val()),
			birth_y: parseFloat($('input[name="birth-position-Y"]').val()),
			death_x: parseFloat($('input[name="death-position-X"]').val()),
			death_y: parseFloat($('input[name="death-position-Y"]').val()),
			speed_x: parseFloat($('input[name="speed-X"]').val()),
			speed_y: parseFloat($('input[name="speed-Y"]').val()),
			longevity: parseFloat($('input[name="longevity"]').val()),
			css: $('textarea[name="danmaku-css"]').val().trim(),
			type: 'Advanced',
		}
		var bul = document.createElement('div');
		bul.setAttribute('class', 'danmaku');
		bul.setAttribute('style', preview_danmaku.css);
		var text = document.createTextNode(preview_danmaku.content);
		bul.appendChild(text);
		player_background.appendChild(bul);

		var new_danmaku_element = {idle: false, generating: false, posX: 0, posY: 0, clear_request: false, element: bul, ref_danmaku: preview_danmaku};
		var danmaku_Animation = new Danmaku_Animation(new_danmaku_element);
		danmaku_Animation.startAnimation();
		pop_ajax_message('Previewing!', 'success');
	});
	$('#advanced-danmaku-form').submit(function(evt) {
		var button = document.querySelector('#advanced-danmaku-form .special-danmaku-button.special');
		button.disabled = true;

        var error = advanced_danmaku_form_check();
		if (error) {
			button.disabled = false;
			return false;
		}

		var data = $(this).serialize();
		if ($('#use-cur-timestamp').is(':checked')) {
			data += '&'+$.param({timestamp: player.getCurrentTime()});
		} else {
			data += '&'+$.param({timestamp: $('#new-timestamp').val()});
		}

		$.ajax({
			type: "POST",
			url: '/video/advanced_danmaku/' + url_suffix,
			data: data,
			success: function(result) {
				if(!result.error) {
					$('#danmaku-input').val('');
					pop_ajax_message('Danmaku sent!', 'success');
					result.timestamp = player.getCurrentTime() + 0.05;
					result.blocked = false;
					$('#danmaku-list').append('<div class="per-bullet container">\
						<div class="bullet-time-value">' + secondsToTime(result.timestamp) + '</div>\
						<div class="bullet-content-value" title="' + result.content + '">' + result.content + '</div>\
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

	$(document).keydown(function(e) {
		// console.log(e.keyCode)
		if (e.keyCode == 27) {
			$('.danmaku-menu').addClass('hidden');
			$('.danmaku-pool-menu').addClass('hidden');
			if ($('#page-wide').hasClass('on')) {
				$('#page-wide').removeClass('on').addClass('off');
				var player_container = document.getElementById('player-container');
				player_container.style.position = 'relative';
				$(window).off('resize', page_wide_player);

				widescreen_change();
			}
		}
	});

	var timestamp = parseFloat(getParameterByName('timestamp'));
	if (!isNaN(timestamp)) {
		player.seekTo(timestamp - 0.05, true);
	}
	var autoplay = getParameterByName('autoplay');
	if (autoplay === '1') {
		player.playVideo();
	}
}

function advanced_danmaku_form_check() {
	var error = false;
	var content = $('#advanced-danmaku-content').val().trim();
	if (!content) {
		pop_ajax_message('You can\'t post empty comment.', 'error');
		error = true;
	} else if (content.length > 350) {
		pop_ajax_message('Comment is too long (less than 350 characters).', 'error');
		error = true;
	}

	if ($('input[name="birth-position-X"]').val() === $('input[name="death-position-X"]').val()
		&& $('input[name="birth-position-Y"]').val() === $('input[name="death-position-Y"]').val()
		&& $('input[name="longevity"]').val() === '0') {
		pop_ajax_message('Longevity must be specified for static danmaku.', 'error');
		error = true;
	}
	if (($('input[name="birth-position-X"]').val() !== $('input[name="death-position-X"]').val() && $('input[name="speed-X"]').val() === '0')
		|| ($('input[name="birth-position-Y"]').val() !== $('input[name="death-position-Y"]').val() && $('input[name="speed-Y"]').val() === '0')) {
		pop_ajax_message('Speed must be specified for moving danmaku.', 'error');
		error = true;
	}

	if (!$('textarea[name="danmaku-css"]').val().trim()) {
		pop_ajax_message('CSS must be specified.', 'error');
		error = true;
	}
	return error;
}

function quality_youtube2local(quality) {
	if (quality === 'small') {
		return '240p';
	} else if (quality === 'medium') {
		return '360p';
	} else if (quality === 'large') {
		return '480p';
	} else if (quality === 'hd720') {
		return '720p';
	} else if (quality === 'hd1080') {
		return '1080p';
	} else if (quality === 'auto') {
		return 'Auto';
	}
}

function quality_local2youtube(quality) {
	if (quality === '240p') {
		return 'small';
	} else if (quality === '360p') {
		return 'medium';
	} else if (quality === '480p') {
		return 'large';
	} else if (quality === '720p') {
		return 'hd720';
	} else if (quality === '1080p') {
		return 'hd1080';
	} else if (quality === 'Auto') {
		return 'auto';
	}
}

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

function secondsToTime(secs) {
	var curTime;
	if (Math.floor(secs/60) < 10) {
		curTime = "0"+Math.floor(secs/60);
	} else {
		curTime = ""+Math.floor(secs/60);
	}
	curTime += ":"+("0"+Math.floor(secs%60)).substr(-2);
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
		if (danmaku_list[i].blocked) {
			per_container.className = "per-bullet blocked";
		} else {
			per_container.className = "per-bullet";
		}
		per_container.setAttribute('data-creator', danmaku_list[i].creator);

		var time_value = document.createElement('div');
		time_value.className = "bullet-time-value";
		time_value.appendChild(document.createTextNode(secondsToTime(danmaku_list[i].timestamp)));
		var content_value = document.createElement('div');
		content_value.className = "bullet-content-value";
		content_value.title = danmaku_list[i].content;
		content_value.appendChild(document.createTextNode(danmaku_list[i].content));
		var date_value = document.createElement('div');
		date_value.className = "bullet-date-value";
		date_value.appendChild(document.createTextNode(danmaku_list[i].created));
		
		per_container.appendChild(time_value);
		per_container.appendChild(content_value);
		per_container.appendChild(date_value);
		listNode.appendChild(per_container);
	}
}

function refresh_danmaku_pool() {
	var pool_list = document.querySelectorAll('.per-bullet')
	for (var i = 0; i < danmaku_list.length; i++) {
		if (danmaku_list[i].blocked) {
			pool_list[i].classList.add('blocked');
		} else {
			pool_list[i].classList.remove('blocked');
		}
	}
}

function isCookieExisted(cname) {
	var cookie = getCookie(cname);
	var res = (cookie != "");
	var now = new Date().toUTCString();
	var extime = 60 * 60 *1000; // 60 mins window to block next operation
	setCookie(cname, now, extime);
	return res;
}

$(document).ready(function() {
	$('div.more-episode').click(function() {
		$('a.episode-link.hidden').removeClass('hidden');
		$('div.more-episode').addClass('hidden');
		$('div.less-episode').removeClass('hidden');
	});
	$('div.less-episode').click(function() {
		$('a.episode-link').addClass('hidden');
		var active_link = $('a.episode-link.active');
		active_link.removeClass('hidden');
		if (active_link.index() == 0) {
			active_link.next().removeClass('hidden');
			active_link.next().next().removeClass('hidden');
		} else if (active_link.index() == $('a.episode-link').length - 1) {
			active_link.prev().removeClass('hidden');
			active_link.prev().prev().removeClass('hidden');
		} else {
			active_link.prev().removeClass('hidden');
			active_link.next().removeClass('hidden');
		}
		$('div.more-episode').removeClass('hidden');
		$('div.less-episode').addClass('hidden');
	});

	if (!isCookieExisted(video_id + '_last_hit')) {
		// Send to server hit +1
		$.ajax({
			type: "POST",
			url: '/video/hit/dt' + video_id,
			success: function(result) {
				if(!result.error) {
					// console.log('hit +1 success.');
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
				$('#total-danmaku-span').text(numberWithCommas(result.length));
				for(var i = 0; i < result.length; i++) {
					result[i].blocked = false;
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
	$('#shooter').submit(function(evt){
		if (!player) {
			return false;
		}

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

		$.ajax({
			type: "POST",
			url: '/video/danmaku/' + url_suffix,
			data: $(this).serialize()+'&'+$.param({timestamp: player.getCurrentTime()}),
			success: function(result) {
				if(!result.error) {
					$('#danmaku-input').val('');
					pop_ajax_message('Danmaku sent!', 'success');
					result.timestamp = player.getCurrentTime() + 0.05;
					result.blocked = false;
					$('#danmaku-list').append('<div class="per-bullet container">\
						<div class="bullet-time-value">' + secondsToTime(result.timestamp) + '</div>\
						<div class="bullet-content-value" title="' + result.content + '">' + result.content + '</div>\
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

	$('#danmaku-pool').on('click', 'div.per-bullet', function(evt) {
		$('div.per-bullet.selected').removeClass('selected');
		$(this).addClass('selected');
	});

	$('#danmaku-pool').on('contextmenu', 'div.per-bullet', function(evt) {
		evt.originalEvent.preventDefault();
		$('div.per-bullet.selected').removeClass('selected');
		$(this).addClass('selected');

		$('.danmaku-pool-menu').attr('data-creator', $(this).attr('data-creator'));
		$('#danmaku-pool-copy-content').attr('data-clipboard-text', $(this).children('.bullet-content-value').text());

		var rect = $('#player-container').offset();
		$('.danmaku-pool-menu').removeClass('hidden');
		$('.danmaku-pool-menu')[0].style.left = evt.originalEvent.pageX - rect.left+'px';
		$('.danmaku-pool-menu')[0].style.top = evt.originalEvent.pageY - rect.top+'px';
		var hide_menu = function() {
			$('.danmaku-pool-menu').addClass('hidden');
			$(document).off('click', hide_menu);
		}
		$(document).click(hide_menu);
	});
	$('#danmaku-pool-block-sender').click(function() {
		var block_type = 'User';
		var block_content = $('.danmaku-pool-menu').attr('data-creator');
		add_block_rule(block_type, block_content);
	});
	{
		var client = new ZeroClipboard(document.getElementById("danmaku-pool-copy-content"));
	}
	$('#danmaku-pool-check-all-sent').click(function() {
		var block = '';
		var user = $('.danmaku-pool-menu').attr('data-creator');
		for (var i = 0; i < danmaku_list.length; i++) {
			if (danmaku_list[i].creator.toString() === user) {
				block += '<div class="check-per-bullet">\
						<div class="bullet-time-value">'+secondsToTime(danmaku_list[i].timestamp)+'</div>\
						<div class="bullet-content-value" title="'+danmaku_list[i].content+'">'+danmaku_list[i].content+'</div>\
						<div class="bullet-date-value">'+danmaku_list[i].created+'</div>\
					</div>';
			}
		}
		$('#danmaku-list-all').empty();
		$('#danmaku-list-all').append(block);
		$('.player-full-setting.check-all-sent').removeClass('hidden');
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
		$('#comment-id-input').val(comment_id);

		if (error) {
			button.disabled = false;
			return false;
		}

		$.ajax({
			type: "POST",
			url: '/video/reply_post/dt'+video_id,
			data: $(evt.target).serialize(),
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
		var user_name = comment_box.find('a.user-name').text();
		inner_comment_container.append($('#user-reply-form'));
		$('#user-reply-form').removeClass('hidden');
		$('#reply-textarea').val('@' + user_name + ': ');
	});

	floorth = parseInt(getParameterByName('comment'));
	if (!isNaN(floorth)) {
		var total = parseInt($('#comments-block-title span').text());
		var rev = total - floorth + 1;
		update_comments(Math.ceil(rev/20), video_id);
	}
	inner_floorth = parseInt(getParameterByName('reply'));

	$('#report-button').click(function() {
		$('#report-box').addClass('show');
	});
	$('#report-dismiss').click(function() {
		$('#report-box').removeClass('show');	
	});
	$('#report-submission-form').submit(function(evt) {
		var button = document.querySelector('input#submit-report');
		button.disabled = true;

		$.ajax({
		  type: "POST",
		  url: evt.target.action,
		  data: $('#report-submission-form').serialize(),
		  success: function(result) {
		    console.log(result);
		    if(result.error) {
		      pop_ajax_message(result.message, 'error');
		    } else {
		      pop_ajax_message(result.message, 'success');
		      $('#report-submission-form')[0].reset();
		      setTimeout(function(){
		        $('#report-box').removeClass('show');
		        button.disabled = false;
		      }, 3000);
		    }
		    button.disabled = false;
		  },
		  error: function (xhr, ajaxOptions, thrownError) {
		    console.log(xhr.status);
		    console.log(thrownError);
		    button.disabled = false;
		    pop_ajax_message(xhr.status+' '+thrownError, 'error');
		  }
		});
		return false;
	});
});

function update_comments(page, video_id) {
	var comment_container = $('#comments-list-container');
	var pagination_container = $('div.pagination-line.all');
	$('#user-comment-form').after($('#user-reply-form'));
	$('#user-reply-form').addClass('hidden')
	comment_container.append('<div class="comment-entry loading"></div>');
	$.ajax({
		type: "GET",
		url: '/video/comment/dt'+video_id,
		data: {page: page},
		success: function(result) {
			comment_container.empty();
			pagination_container.empty();
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
	                    	if (!isNaN(inner_floorth)) {
		                    	update_inner_comments(Math.ceil(inner_floorth/10), video_id, cur_div.children('div.inner-comment-container'))
		                    }
	                    }
                    }
				}
			} else {
				pop_ajax_message(result.message, 'error');
				comment_container.append('<div class="comment-entry no-comment error" data-page="'+page+'">Load error.</div>');
			}
		},
		error: function (xhr, ajaxOptions, thrownError) {
			console.log(xhr.status);
			console.log(thrownError);
			comment_container.empty();
			pagination_container.empty();
			pop_ajax_message(xhr.status+' '+thrownError, 'error');
			comment_container.append('<div class="comment-entry no-comment error" data-page="'+page+'">Load error.</div>');
		}
	});
}

function update_inner_comments(page, video_id, inner_comment_container) {
	var comment_id = inner_comment_container.parent().attr('data-id');
	inner_comment_container.children('div.display-button.replies').remove();
	var pagination_container = inner_comment_container.children('div.pagination-line.replies');
	if (pagination_container.length == 0) {
		inner_comment_container.append('<div class="pagination-line replies"></div>');
		pagination_container = inner_comment_container.children('div.pagination-line.replies');
	}
	pagination_container.before('<div class="comment-entry loading"></div>');

	$.ajax({
		type: "GET",
		url: '/video/inner_comment/dt'+video_id,
		data: {page: page, comment_id: comment_id},
		success: function(result) {
			inner_comment_container.children('div.comment-entry').remove();
			if(!result.error) {
				if (result.total_pages != 0) {
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
	                } else {
	                	pagination_container.remove();
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
				inner_comment_container.prepend('<div class="comment-entry no-comment inner error" data-page="'+page+'">Load error.</div>');
			}
		},
		error: function (xhr, ajaxOptions, thrownError) {
			console.log(xhr.status);
			console.log(thrownError);
			inner_comment_container.empty();
			pop_ajax_message(xhr.status+' '+thrownError, 'error');
			inner_comment_container.append('<div class="comment-entry no-comment inner error" data-page="'+page+'">Load error.</div>');
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
        <div class="comment-content">' + comment.content + '</div>\
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
