(function(dt, $) {
var danmaku_prefix = 'https://storage.googleapis.com/danmaku/';
// var danmaku_prefix = 'http://localhost:8080/_ah/gcs/danmaku/';
var video_id;
var clip_id;
var clip_index;
var clip_vid;
var player;
var ws;
var isPlaying = false;
var player_width = 640;
var player_height = 446;
var player_inner_width = 640;
var player_inner_height = 360;
var danmakuVar = null;
var progressVar = null;
var bufferingVar = null;
var progressHold = false;
var autoSwitch = false;
var isLoop = false;
var danmaku_pointer = 0;
var danmaku_pool_list = [];
var danmaku_elements = [];
var curTime = 0;
var lastTime = 0;
var occupation_normal = [];
var accumulate_normal = [];
var occupation_bottom = [];
var accumulate_bottom = [];
var occupation_top = [];
var accumulate_top = [];
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
var normal_danmaku_sequence = new DanmakuTimeSequence([]);
var show_subtitles = 0;
var ori_subtitles_font_size = 16;
var subtitles_font_size = 16;
var ori_subtitles_longevity = 5;
var subtitles_longevity = 5;
var subtitles_opacity = 1;
var linked_elements = new dt.LinkedList();
var subtitles_danmaku_container = {};
var subtitles_danmaku_backup = {};

var code_intervals = [];
var code_timeouts = [];
var oldSetInterval = window.setInterval;
var oldSetTimeout = window.setTimeout;
var setInterval = function(func, time) {
    var temp = oldSetInterval(func, time);
    code_intervals.push(temp);
    return temp;
}
var setTimeout = function(func, time) {
    var temp = oldSetTimeout(func, time);
    code_timeouts.push(temp);
    return temp;
}

function DanmakuTimeSequence(danmaku_list) {
    this.danmaku_list = danmaku_list;
    this.danmaku_pointer = 0;
    dt.quick_sort(this.danmaku_list, 0, this.danmaku_list.length-1, danmaku_timestamp_lower_compare);
}
DanmakuTimeSequence.prototype.addOne = function(danmaku) {
    this.danmaku_list.push(danmaku);
    dt.quick_sort(this.danmaku_list, 0, this.danmaku_list.length-1, danmaku_timestamp_lower_compare);
}
DanmakuTimeSequence.prototype.addMult = function(danmaku_list) {
    this.danmaku_list = this.danmaku_list.concat(danmaku_list);
    dt.quick_sort(this.danmaku_list, 0, this.danmaku_list.length-1, danmaku_timestamp_lower_compare);
}
DanmakuTimeSequence.prototype.locate = function() {
    if (curTime < lastTime && (this.danmaku_pointer >= this.danmaku_list.length || this.danmaku_list[this.danmaku_pointer].timestamp > curTime)) {
        while(this.danmaku_pointer > 0 && this.danmaku_list[this.danmaku_pointer - 1].timestamp >= curTime) {
            this.danmaku_pointer -= 1;
        }
    } else {
        while (this.danmaku_pointer < this.danmaku_list.length && this.danmaku_list[this.danmaku_pointer].timestamp < curTime - 1) {
            this.danmaku_pointer += 1;
        }
    }
}
DanmakuTimeSequence.prototype.next = function() {
    while (this.danmaku_pointer < this.danmaku_list.length
        && this.danmaku_list[this.danmaku_pointer].blocked
        && this.danmaku_list[this.danmaku_pointer].timestamp <= curTime) {
        this.danmaku_pointer += 1;
    }
    if (this.danmaku_pointer >= this.danmaku_list.length 
        || this.danmaku_list[this.danmaku_pointer].timestamp > curTime) {
        return null;
    } else {
        return this.danmaku_list[this.danmaku_pointer];
    }
}
DanmakuTimeSequence.prototype.consume = function() {
    this.danmaku_pointer += 1;
}

function Danmaku_Animation(ele) {
    var lTime = Date.now();
    var type = ele.ref_danmaku.type;
    var existingTime;
    if (type !== 'Subtitles') existingTime = existing_time;
    else existingTime = subtitles_longevity;
    var offsetWidth = ele.element.offsetWidth;
    var offsetHeight = ele.element.offsetHeight;
    var direct_x, direct_y, death_x, death_y;

    if (type === 'Scroll') {
        requestAnimationFrame(scroll_update);
    } else if (type === 'Top' || type === 'Bottom') {
        ele.posX = (player_width + offsetWidth)/2;
        ele.element.style.WebkitTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        ele.element.style.msTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        ele.element.style.transform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        requestAnimationFrame(static_update);
    } else if (type === 'Advanced') {
        ele.posX = get_positionX(ele.ref_danmaku.birth_x);
        ele.posY = get_positionY(ele.ref_danmaku.birth_y);
        death_x  = get_positionX(ele.ref_danmaku.death_x);
        death_y = get_positionY(ele.ref_danmaku.death_y);

        if (death_x > ele.posX) direct_x = 1;
        else if (death_x < ele.posX) direct_x = -1;
        else direct_x = 0;

        if (death_y > ele.posY) direct_y = 1;
        else if (death_y < ele.posY) direct_y = -1;
        else direct_y = 0;

        if (ele.ref_danmaku.longevity !== 0) {
            existingTime = ele.ref_danmaku.longevity;
        }
        requestAnimationFrame(advanced_update);
    } else if (type === 'Subtitles') {
        ele.posX = (player_width + offsetWidth)/2;
        ele.element.style.WebkitTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        ele.element.style.msTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        ele.element.style.transform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        requestAnimationFrame(subtitles_update);
    } else if (type === 'Custom') {
        requestAnimationFrame(custom_update);
    }

    function get_positionX(x) {
        if (x >= 0) {
            if (ele.ref_danmaku.relative) {
                if (ele.ref_danmaku.as_percent) {
                    return x/100*player_inner_width + get_player_inner_pos_right();
                } else {
                    return x + get_player_inner_pos_right();
                }
            } else {
                if (ele.ref_danmaku.as_percent) {
                    return x/100*player_width;
                } else {
                    return x;
                }
            }
        } else {
            if (ele.ref_danmaku.relative) {
                if (ele.ref_danmaku.as_percent) {
                    return x/100*player_inner_width + get_player_inner_pos_left() + offsetWidth;
                } else {
                    return x + get_player_inner_pos_left() + offsetWidth;
                }
            } else {
                if (ele.ref_danmaku.as_percent) {
                    return x/100*player_width + player_width + offsetWidth;
                } else {
                    return x + player_width + offsetWidth;
                }
            }
        }
    }

    function get_positionY(y) {
        if (y >= 0) {
            if (ele.ref_danmaku.relative) {
                if (ele.ref_danmaku.as_percent) {
                    return y/100*player_inner_height + get_player_inner_pos_top();
                } else {
                    return y + get_player_inner_pos_top();
                }
            } else {
                if (ele.ref_danmaku.as_percent) {
                    return y/100*player_height;
                } else {
                    return y;
                }
            }
        } else {
            if (ele.ref_danmaku.relative) {
                if (ele.ref_danmaku.as_percent) {
                    return y/100*player_inner_height + get_player_inner_pos_bottom() + offsetHeight;
                } else {
                    return y + get_player_inner_pos_bottom() + offsetHeight;
                }
            } else {
                if (ele.ref_danmaku.as_percent) {
                    return y/100*player_height + player_height + offsetHeight;
                } else {
                    return y + player_height + offsetHeight;
                }
            }
        }
    }

    function scroll_update() {
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

        if (!ele.clear_request && ele.posX < offsetWidth + player_width) {
            requestAnimationFrame(scroll_update);
        } else {
            ele.element.style.WebkitTransform = "translate(-"+0+"px, "+ele.posY+"px)";
            ele.element.style.msTransform = "translate(-"+0+"px, "+ele.posY+"px)";
            ele.element.style.transform = "translate(-"+0+"px, "+ele.posY+"px)";
            ele.idle = true;
            ele.posX = 0;
        }
    }

    function static_update() {
        var curTime = Date.now();
        var deltaTime = curTime - lTime;
        lTime = curTime;
        if (isPlaying) {
            existingTime -= deltaTime/1000;
        }

        if (!ele.clear_request && existingTime > 0) {
            requestAnimationFrame(static_update);
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

        if (isPlaying) {
            existingTime -= deltaTime/1000;
            ele.posX += direct_x*ele.ref_danmaku.speed_x*deltaTime/1000;
            ele.posY += direct_y*ele.ref_danmaku.speed_y*deltaTime/1000;
            ele.element.style.WebkitTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
            ele.element.style.msTransform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
            ele.element.style.transform = "translate(-"+ele.posX+"px, "+ele.posY+"px)";
        }

        if (!ele.clear_request 
            && (direct_x !== 0 || direct_y !== 0 || (direct_x === 0 && direct_y === 0 && existingTime > 0))
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

    function subtitles_update() {
        var curTime = Date.now();
        var deltaTime = curTime - lTime;
        lTime = curTime;
        if (isPlaying) {
            existingTime -= deltaTime/1000;
        }

        if (!ele.clear_request && existingTime > 0) {
            requestAnimationFrame(subtitles_update);
        } else {
            occupation = occupation_bottom;
            for (var j = ele.posY; j < ele.element.offsetHeight + ele.posY; j++) {
                occupation[j] -= 1;
            }
            ele.element.parentNode.removeChild(ele.element);
            linked_elements.remove(ele);
        }
    }

    function custom_update() {
        var curTime = Date.now();
        var deltaTime = curTime - lTime;
        lTime = curTime;
        var isOver = false;
        if (isPlaying) {
            try {
                isOver = ele.ref_danmaku.callback(ele.element, deltaTime/1000);
            } catch (err) {
                console.log(err.name+': '+err.message);
                isOver = true;
            }
        }

        if (!ele.clear_request && !isOver) {
            requestAnimationFrame(custom_update);
        } else {
            ele.element.parentNode.removeChild(ele.element);
            linked_elements.remove(ele);
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
    subtitles_all_clear();
    code_all_clear();
}

function subtitles_all_clear() {
    var curNode = linked_elements.head;
    while (curNode) {
        if (typeof curNode.belong_to !== 'undefined') {
            curNode.clear_request = true;
        }
        curNode = curNode.next;
    }
}

function subtitles_one_clear(key) {
    var curNode = linked_elements.head;
    while (curNode) {
        if (curNode.belong_to === key) {
            curNode.clear_request = true;
        }
        curNode = curNode.next;
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
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].type === 'Top') {
                danmaku_pool_list[i].blocked = true;
            }
        }
    } else {
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].type === 'Top' && !danmaku_filter(i)) {
                danmaku_pool_list[i].blocked = false;
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
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].type === 'Bottom') {
                danmaku_pool_list[i].blocked = true;
            }
        }
    } else {
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].type === 'Bottom' && !danmaku_filter(i)) {
                danmaku_pool_list[i].blocked = false;
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
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].type !== 'Advanced' && danmaku_pool_list[i].color.toString(16) !== 'ffffff') {
                danmaku_pool_list[i].blocked = true;
            }
        }
    } else {
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].type !== 'Advanced' && danmaku_pool_list[i].color.toString(16) !== 'ffffff' && !danmaku_filter(i)) {
                danmaku_pool_list[i].blocked = false;
            }
        }
    }
    refresh_danmaku_pool();
}

function add_block_rule(block_type, block_content) {
    if (!block_content) return;
    // console.log(block_content);
    block_content = dt.escapeHTML(block_content);
    for (var i = 0; i < block_rules.length; i++) {
        if (block_type === block_rules[i].type && block_content === block_rules[i].content) {
            if (!block_rules[i].isOn) {
                block_rules[i].isOn = true;
                change_block_rule(i);
                dt.setCookie('block-rules', encodeURIComponent(JSON.stringify(block_rules)), 0);
                $('.block-rule-entry:nth-child('+(i+1)+') .rule-status').removeClass('off').text('On');
            }
            return;
        }
    }

    $('.block-list').append('<div class="block-rule-entry">\
      <div class="block-rule rule-type">' + block_type + '</div>\
      <div class="block-rule rule-content" title="' + block_content + '">' + block_content + '</div>\
      <div class="block-rule rule-status">On</div>\
      <div class="block-rule rule-delete"></div>\
    </div>');
    block_rules.push({type: block_type, content: block_content, isOn: true});
    change_block_rule(block_rules.length - 1);
    dt.setCookie('block-rules', encodeURIComponent(JSON.stringify(block_rules)), 0);
    return;
}

function change_block_rule(index) {
    if (block_rules[index].isOn) {
        for (var i = 0; i < danmaku_elements.length; i++) {
            var ele = danmaku_elements[i];
            if (ele.idle) continue;

            if (block_rules[index].type === 'Keywords') {
                if (dt.unescapeHTML(ele.ref_danmaku.content).indexOf(dt.unescapeHTML(block_rules[index].content)) > -1) {
                    ele.clear_request = true;
                }
            } else if (block_rules[index].type === 'RegExp') {
                var regex = new RegExp(dt.unescapeHTML(block_rules[index].content));
                if (regex.test(dt.unescapeHTML(ele.ref_danmaku.content))) {
                    ele.clear_request = true;
                }
            } else if (block_rules[index].type === 'User') {
                if (ele.ref_danmaku.creator.toString() === block_rules[index].content) {
                    ele.clear_request = true;
                }
            }
        }
        for (var j = 0; j < danmaku_pool_list.length; j++) {
            if (single_rule_filter(j, index)) {
                danmaku_pool_list[j].blocked = true;
            }
        }
    } else {
        for (var j = 0; j < danmaku_pool_list.length; j++) {
            if (single_rule_filter(j, index) && !danmaku_filter(j)) {
                danmaku_pool_list[j].blocked = false;
            }
        }
    }
    refresh_danmaku_pool();
}

function danmaku_filter(index) {// return true to filter.
    if ((danmaku_pool_list[index].type === 'Top' && !show_top) || 
        (danmaku_pool_list[index].type === 'Bottom' && !show_bottom) ||
        (danmaku_pool_list[index].type !== 'Advanced' && !show_colored && danmaku_pool_list[index].color.toString(16) != 'ffffff' )) {
        return true;
    } else {
        for (var i = 0; i < block_rules.length; i++) {
            if (!block_rules[i].isOn) continue;
            if (single_rule_filter(index, i)) {
                return true;
            }
        }
        return false;
    }
}

function single_rule_filter(index, i) {
    if (block_rules[i].type === 'Keywords') {
        if (dt.unescapeHTML(danmaku_pool_list[index].content).indexOf(dt.unescapeHTML(block_rules[i].content)) > -1) {
            return true;
        }
    } else if (block_rules[i].type === 'RegExp') {
        var regex = new RegExp(dt.unescapeHTML(block_rules[i].content));
        if (regex.test(dt.unescapeHTML(danmaku_pool_list[index].content))) {
            return true;
        }
    } else if (block_rules[i].type === 'User') {
        if (danmaku_pool_list[index].creator.toString() === block_rules[i].content) {
            return true;
        }
    }
    return false;
}

function change_danmaku_outline() {
    if (has_text_outline) {
        for (var i = 0; i < danmaku_elements.length; i++) {
            var ele = danmaku_elements[i];
            if (!ele.idle && ele.ref_danmaku.type !== 'Advanced') {
                var outline_color = reverse_color(ele.ref_danmaku.color);
                ele.element.style.textShadow = '1px 0 1px '+outline_color+', -1px 0 1px '+outline_color+', 0 1px 1px '+outline_color+', 0 -1px 1px '+outline_color;
            }
        }
    } else {
        for (var i = 0; i < danmaku_elements.length; i++) {
            var ele = danmaku_elements[i];
            if (!ele.idle && ele.ref_danmaku.type !== 'Advanced') {
                ele.element.style.textShadow = '0 0 0';
            }
        }
    }
}

function change_danmaku_opacity() {
    for (var i = 0; i < danmaku_elements.length; i++) {
        var ele = danmaku_elements[i];
        if (!ele.idle && ele.ref_danmaku.type !== 'Advanced') {
            ele.element.style.opacity = danmaku_opacity;
        }
    }
}

function change_subtitles_danmaku_opacity() {
    var curNode = linked_elements.head;
    while (curNode) {
        curNode.element.style.opacity = subtitles_opacity;
        curNode = curNode.next;
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
    curTime = player.getCurrentTime();

    if (show_danmaku) {
        normal_danmaku_sequence.locate();
        var i = 0;
        var ref_danmaku;
        while (ref_danmaku = normal_danmaku_sequence.next()) {
            if (ref_danmaku.type === 'Code') {
                normal_danmaku_sequence.consume();
                execute_code_danmaku(dt.unescapeHTML(ref_danmaku.content));
                continue;
            }

            while (!danmaku_elements[i].idle && i < max_danmaku) i++;
            if (i >= max_danmaku) break;

            var ele = danmaku_elements[i];
            ele.ref_danmaku = ref_danmaku;
            normal_danmaku_sequence.consume();

            ele.idle = false;
            ele.clear_request = false;
            if (ele.ref_danmaku.type === 'Advanced') {
                ele.element.setAttribute('data-index', i);
                ele.element.lastChild.nodeValue = dt.unescapeHTML(ele.ref_danmaku.content);
                ele.element.setAttribute('style', ele.ref_danmaku.css);
                ele.element.style.left = player_width+'px';
            } else {
                ele.element.setAttribute('data-index', i);
                ele.element.lastChild.nodeValue = dt.unescapeHTML(ele.ref_danmaku.content);
                ele.element.setAttribute('style', '');
                ele.element.style.left = player_width+'px';
                ele.element.style.opacity = danmaku_opacity;
                ele.element.style.color = dt.dec2hexColor(ele.ref_danmaku.color);
                if (has_text_outline) {
                    var outline_color = reverse_color(ele.ref_danmaku.color);
                    ele.element.style.textShadow = '1px 0 1px '+outline_color+', -1px 0 1px '+outline_color+', 0 1px 1px '+outline_color+', 0 -1px 1px '+outline_color;
                }
                ele.element.style.fontSize = Math.round(ele.ref_danmaku.size*danmaku_scale/3)+'px';
                ele.element.style.fontFamily = danmaku_font;
                // ele.element.lastChild.nodeValue = dt.secondsToTime(ele.ref_danmaku.timestamp);
                ele.generating = true;

                if (ele.ref_danmaku.type === 'Scroll') {
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
                var offsetHeight = ele.element.offsetHeight;
                for (var z = 0; z < offsetHeight && z < player_height; z++) {
                    accumulate[0] += occupation[z];
                }
                for (var j = 1; j < player_height - offsetHeight + 1; j++) {
                    accumulate[j] = accumulate[j-1];
                    accumulate[j] -= occupation[j-1];
                    accumulate[j] += occupation[j+offsetHeight-1];
                }

                var min_value = 2000000;
                var min_line = 0;
                for (var j = 0; j < player_height - offsetHeight + 1; j++) {
                    if ((ele.ref_danmaku.type === 'Bottom' && accumulate[j] <= min_value)
                        || (ele.ref_danmaku.type != 'Bottom' && accumulate[j] < min_value)) {
                        min_value = accumulate[j];
                        min_line = j;
                    }
                }

                ele.posY = min_line;
                for (var j = ele.posY; j < offsetHeight + ele.posY; j++) {
                    occupation[j] += 1;
                }
            }
            Danmaku_Animation(ele);
        }
    }

    if (show_subtitles) {
        var player_background = document.getElementById('player-background');
        for(var key in subtitles_danmaku_container) {
            var subtitle_danmaku_list = subtitles_danmaku_container[key];
            subtitle_danmaku_list.locate();
            var ref_danmaku;
            while (ref_danmaku = subtitle_danmaku_list.next()) {
                var bul = document.createElement('div');
                bul.setAttribute('class', 'danmaku');
                bul.appendChild(document.createTextNode(dt.unescapeHTML(ref_danmaku.content)));
                bul.style.left = player_width+'px';
                bul.style.opacity = subtitles_opacity;
                bul.style.fontSize = subtitles_font_size+'px';
                player_background.appendChild(bul);
                var ele = {prev: null, next: null, posX: 0, posY: 0, clear_request: false, element: bul, ref_danmaku: ref_danmaku, belong_to: key};
                linked_elements.push(ele);
                subtitle_danmaku_list.consume();

                accumulate = accumulate_bottom;
                occupation = occupation_bottom;
                accumulate[0] = 0;
                var offsetHeight = ele.element.offsetHeight;
                for (var z = 0; z < offsetHeight && z < player_height; z++) {
                    accumulate[0] += occupation[z];
                }
                for (var j = 1; j < player_height - offsetHeight + 1; j++) {
                    accumulate[j] = accumulate[j-1];
                    accumulate[j] -= occupation[j-1];
                    accumulate[j] += occupation[j+offsetHeight-1];
                }

                var min_value = 2000000;
                var min_line = 0;
                for (var j = 0; j < player_height - offsetHeight + 1; j++) {
                    if (accumulate[j] <= min_value) {
                        min_value = accumulate[j];
                        min_line = j;
                    }
                }

                ele.posY = min_line;
                for (var j = ele.posY; j < offsetHeight + ele.posY; j++) {
                    occupation[j] += 1;
                }
                Danmaku_Animation(ele);
            }
        }
    }
    lastTime = curTime;
}

function player_seek(time) {
    player.seekTo(time, true);
    danmaku_all_clear();
}

function auto_switch_count_down(target_link) {
    var count_down = 5;
    var one_down = function() {
        console.log('one down '+count_down)
        if (count_down > 0) {
            $('#switch-count-span').text('Switch to the next part in '+count_down+' seconds.');
            count_down -= 1;
            switch_count_down = oldSetTimeout(one_down, 1000);
        } else {
            window.location.href = (target_link.attr('href')+"?autoplay=1").replace(/\?/g, '&').replace('&', '?');
        }
    }

    $('#switch-count-down').removeClass('hidden');
    $('#switch-count-span').text('Switch to the next part in '+count_down+' seconds.');
    count_down -= 1;
    switch_count_down = oldSetTimeout(one_down, 1000);
}

function stop_switch_count_down() {
    clearTimeout(switch_count_down);
    switch_count_down = null;
    $('#switch-count-down').addClass('hidden');
}

function player_resize() {
    player_width = $('#player-background').width();
    player_height = $('#player-background').height();
    player_inner_width = player_width;
    player_inner_height = player_height;
    if (player_inner_height/9*16 < player_inner_width) {
        player_inner_width = Math.round(player_inner_height/9*16);
    } else {
        player_inner_height = Math.round(player_inner_width/16*9);
    }
    if (player) player.setSize(player_inner_width, player_inner_height);
    var player_canvas = document.getElementById("player-canvas");
    player_canvas.style.width = player_inner_width+"px";
    player_canvas.style.height = player_inner_height+"px";
}

function buffer_update() {
    var buffered = player.getVideoLoadedFraction();
    var progress_buffered = document.getElementById("progress-bar-buffered");
    progress_buffered.style.width = buffered*100+'%';
    if (buffered === 1) {
        clearInterval(bufferingVar);
        bufferingVar = null;
    }
}

var quality_reg = / \((.*)\)/;
function progress_update() {
    if (progressHold) return;

    var currentTime = player.getCurrentTime();
    dt.setCookie(video_id, clip_index+'|'+currentTime, 0);
    
    var progress_number = document.getElementById("progress-number");
    progress_number.lastChild.nodeValue = dt.secondsToTime(currentTime)+"/"+dt.secondsToTime(player.getDuration());
    var progress_played = document.getElementById("progress-bar-played");
    progress_played.style.width = currentTime/player.getDuration()*100+'%';

    var cur_quality = quality_youtube2local(player.getPlaybackQuality());
    if (typeof cur_quality !== 'undefined') {
        var quality_ele = $('.list-selected.quality');
        var quality_text = quality_ele.text();
        var matched = quality_text.match(quality_reg);
        if (!matched) {
            quality_ele.text(quality_text+' ('+cur_quality+')');
        } else if (matched && matched[1] !== cur_quality) {
            quality_text = quality_text.replace(quality_reg, '');
            quality_ele.text(quality_text+' ('+cur_quality+')');
        }
    }
}

dt.onPlayerStateChange = function(event) {
    if (event.data == YT.PlayerState.PLAYING) {
        isPlaying = true;
        $("#play-pause-button").removeClass('play')
                                .addClass('pause');

        if (danmakuVar === null) {
            danmakuVar = oldSetInterval(danmaku_update, 250);
            danmaku_update();
        }
        if (progressVar === null) {
            progressVar = oldSetInterval(progress_update, 500);
            progress_update();
        }
        if (bufferingVar === null) {
            bufferingVar = oldSetInterval(buffer_update, 500);
        }
        if (switch_count_down !== null) {
            stop_switch_count_down();
        }
    } else if (event.data == YT.PlayerState.PAUSED || event.data == YT.PlayerState.BUFFERING) {
        isPlaying = false;
        $("#play-pause-button").removeClass('pause')
                                .addClass('play');

        clearInterval(danmakuVar);
        clearInterval(progressVar);
        danmakuVar = null;
        progressVar = null;
        if (bufferingVar === null) {
            bufferingVar = oldSetInterval(buffer_update, 500);
        }
    } else if (event.data == YT.PlayerState.ENDED) {
        isPlaying = false;
        $("#play-pause-button").removeClass('pause')
                                .addClass('play');

        if (isLoop) {
            player.playVideo();
        } else if (autoSwitch) {
            // fire switch event
        // } else if (autoSwitch && $('a.episode-link.active').length != 0 && $('a.episode-link.active').next().length != 0) {
        //     auto_switch_count_down($('a.episode-link.active').next());
        // } else if (autoSwitch && $('a.list-entry.active').length != 0 && $('a.list-entry.active').next().length != 0) {
        //     auto_switch_count_down($('a.list-entry.active').next());
        } else {
            clearInterval(danmakuVar);
            clearInterval(progressVar);
            danmakuVar = null;
            progressVar = null;
        }
    }
}

dt.onPlayerReady = function(event) {
    player = dt.player;
    $('#progress-number').text("00:00"+"/"+dt.secondsToTime(player.getDuration()));

    var volume = dt.getCookie('player_volume');
    if (!volume) {
        volume = 50;
    } else {
        volume = parseInt(volume);
    }
    volume = parseInt(volume);
    player.setVolume(volume);
    dt.setCookie('player_volume', volume);
    // var volume_bar = document.getElementById("volume-bar");
    var len = 50*volume/100;
    $('#volume-magnitude')[0].style.height = len + "px";
    var volume_pointer = $('#volume-pointer')[0];
    volume_pointer.style.WebkitTransform = "translateY(-"+len+"px)";
    volume_pointer.style.msTransform = "translateY(-"+len+"px)";
    volume_pointer.style.transform = "translateY(-"+len+"px)";
    var volume_tip = $('#volume-tip')[0];
    volume_tip.style.WebkitTransform = "translateY(-"+len+"px)";
    volume_tip.style.msTransform = "translateY(-"+len+"px)";
    volume_tip.style.transform = "translateY(-"+len+"px)";
    if (volume < 10) {
        volume = "0" + volume;
    }
    $(volume_tip).text(volume);

    $('#volume-switch').click(function() {
        var volume_controller = $('#volume-controller');
        if (volume_controller.hasClass('on')) {
            volume_controller.removeClass('on')
                            .addClass('off');
            player.setVolume(0);
        } else {//off
            volume_controller.removeClass('off')
                            .addClass('on');
            player.setVolume($('#volume-magnitude').height()/$('#volume-bar').height()*100);
        }
    });

    $('#volume-background').mousedown(function(evt) {
        var volume = $('#volume-bar')[0];
        function volume_move(evt) {
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
            var value = Math.floor(len/volume.offsetHeight*100);
            if (value < 10) {
                value = "0" + value;
            }
            $(volume_tip).text(value);

            player.setVolume(Math.floor(len/volume.offsetHeight*100));
            dt.setCookie('player_volume', Math.floor(len/volume.offsetHeight*100));
        }

        function volume_end(evt) {
            if (evt.target.id === "volume-background") {
                $(document).off('mousemove mouseup mouseout');
            }
        }

        volume_move(evt);
        $(document).mousemove(volume_move);
        $(document).mouseup(volume_end);
        $(document).mouseout(volume_end);
    });

    // create danmaku divs
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

    function video_toggle() {
        if (isPlaying) {
            player.pauseVideo();
        } else {
            player.playVideo();
        }
    }
    $('#play-pause-button').click(video_toggle);
    $('#player-background').click(video_toggle);

    $('#backward-button').click(function() {
        var time = Math.max(player.getCurrentTime() - 3, 0);
        player_seek(time);
        player.playVideo();
    });
    $('#forward-button').click(function() {
        var time = Math.min(player.getCurrentTime() + 3, player.getDuration());
        player_seek(time);
        player.playVideo();
    });

    $('#danmaku-switch').click(function() {
        var danmaku_controller = $('#danmaku-controller');
        if (danmaku_controller.hasClass('on')) {
            danmaku_controller.removeClass('on')
                                .addClass('off');
            show_danmaku = false;
            danmaku_all_clear();
        } else {//off
            danmaku_controller.removeClass('off')
                                .addClass('on');
            show_danmaku = true;
        }
    });

    $('#wide-screen').click(function() {
        if($('#full-screen').hasClass('on') || $('#page-wide').hasClass('on')) return;

        if ($(this).hasClass('on')) {
            esc_restore();
        } else {//off
            $(this).removeClass('off')
                    .addClass('on');
            $('#player-container').addClass('wide');
            window.parent.$(window.parent.document).trigger('wide');
        }
        player_resize();
    });

    $('#page-wide').click(function() {
        if ($('#full-screen').hasClass('on')) return;

        if ($(this).hasClass('on')) {
            esc_restore();
        } else {//off
            $(this).removeClass('off')
                    .addClass('on');
            $('#player-container').addClass('wide');
            window.parent.$(window.parent.document).trigger('pagewide');
        }
        player_resize();
        // fire event
    });

    function fullscreen_switch() {
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
    $('#full-screen').click(fullscreen_switch);
    $('#player-background').dblclick(fullscreen_switch);

    function esc_restore() {
        $('.danmaku-menu').addClass('hidden');
        $('.danmaku-pool-menu').addClass('hidden');
        $('#page-wide').removeClass('on')
                        .addClass('off');
        $('#wide-screen').removeClass('on')
                        .addClass('off');
        $('#full-screen').addClass('off')
                            .removeClass('on');
        $('#player-container').removeClass('wide');
        $('#player-container').removeClass('auto-hide');
        window.parent.$(window.parent.document).trigger('restore');
        player_resize();
    }

    function fullscreen_change(evt) {
        if ($('#full-screen').hasClass('on')) {
            esc_restore();
        } else {//off
            $('#full-screen').addClass('on')
                            .removeClass('off');
            $('#player-container').addClass('wide');
            if (hide_controls) {
                $('#player-container').addClass('auto-hide');
            }
            player_resize();
        }
    }
    document.addEventListener("fullscreenchange", fullscreen_change, false);      
    document.addEventListener("webkitfullscreenchange", fullscreen_change, false);
    document.addEventListener("mozfullscreenchange", fullscreen_change, false);
    document.addEventListener("MSFullscreenChange", fullscreen_change, false);

    $('.layon-close').click(function(e) {
        $('.input-layon-block').addClass('hidden');
        $('#danmaku-input').removeClass('reply');
        $('#danmaku-reply-input').val('');
    });
    $('#danmaku-input').keydown(function(e) {
        if (e.keyCode === 8 && e.target.selectionStart === 0 && !$('.input-layon-block').hasClass('hidden')) {
            $('.layon-close').trigger('click');
        }
    });

    $(document).keydown(function(e) {
        // console.log(e.keyCode)
        if (e.keyCode == 27) { // ESC
            esc_restore();
        }
    });
    $(window).resize(player_resize);
    player_resize();

    $('#switch-cancel').click(stop_switch_count_down);

    $('#time').click(function() {
        var time_title = $(this);
        if (!time_title.hasClass("up")) {
            time_title.removeClass('down')
                        .addClass('up');
            dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_timestamp_lower_compare);
        } else {
            time_title.removeClass('up')
                        .addClass('down');
            dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_timestamp_upper_compare);
        }
        generate_danmaku_pool_list();
        $("#content").removeClass('up').removeClass('down');
        $("#date").removeClass('up').removeClass('down');
    });
    $('#content').click(function() {
        var content_title = $(this);
        if (!content_title.hasClass("up")) {
            content_title.removeClass('down')
                        .addClass('up');
            dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_content_lower_compare);
        } else {
            content_title.removeClass('up')
                        .addClass('down');
            dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_content_upper_compare);
        }
        generate_danmaku_pool_list();
        $("#time").removeClass('up').removeClass('down');
        $("#date").removeClass('up').removeClass('down');
    });
    $('#date').click(function() {
        var date_title = $(this);
        if (!date_title.hasClass("up")) {
            date_title.removeClass('down')
                        .addClass('up');
            dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_date_lower_compare);
        } else {
            date_title.removeClass('up')
                        .addClass('down');
            dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_date_upper_compare);
        }
        generate_danmaku_pool_list();
        $("#time").removeClass('up').removeClass('down');
        $("#content").removeClass('up').removeClass('down');
    });

    $('#progress-bar').mousedown(function(evt) {
        progressHold = true;
        var progress_bar = $(this)[0];
        function progress_bar_move(evt) {
            var progress_played = $('#progress-bar-played')[0];
            var offset = evt.pageX;
            if (offset < 0) {
                offset = 0;
            }
            if (offset > progress_bar.offsetWidth) {
                offset = progress_bar.offsetWidth;
            }
            progress_played.style.width = offset + "px";
        }

        function progress_bar_stop(evt) {
            progressHold = false;

            progress_bar_move(evt);
            var offset = evt.pageX;
            if (offset < 5) {
                offset = 0;
            }
            if (offset > progress_bar.offsetWidth) {
                offset = progress_bar.offsetWidth;
            }
            var num = offset/progress_bar.offsetWidth*player.getDuration();
            var progress_number = document.getElementById("progress-number");
            progress_number.lastChild.nodeValue = dt.secondsToTime(num)+"/"+progress_number.lastChild.nodeValue.split('/')[1];
            player_seek(num);
            $(document).off('mousemove mouseout mouseup');
        }

        progress_bar_move(evt);
        $(document).mousemove(progress_bar_move);
        $(document).mouseup(progress_bar_stop);
        $(document).mouseout(progress_bar_stop);
    });

    function progress_tip_show(evt) {
        var tip = $("#progress-tip")[0];
        $(tip).removeClass('hidden');
        var progress_bar = $("#progress-bar")[0];
        var offset = evt.pageX;
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
        $(tip).text(dt.secondsToTime(curTime));
    }
    $('#progress-bar').mouseover(progress_tip_show);
    $('#progress-bar').mousemove(progress_tip_show);
    $('#progress-bar').mouseout(function() {
        $('#progress-tip').addClass('hidden');
    });

    var opacity = dt.getCookie('danmaku_opacity');
    if (opacity) {
        opacity = parseFloat(opacity);
        // var indicator = document.getElementById("opacity-indicator");
        var pointer = $('#opacity-pointer')[0];
        var offset = (1 - opacity)*155;
        pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
        pointer.style.msTransform = "translateX(-"+offset+"px)";
        pointer.style.transform = "translateX(-"+offset+"px)";
        danmaku_opacity = opacity;
    }
    $('#opacity-indicator').mousedown(function(evt) {
        var indicator = $(this)[0];
        function move_pointer(evt) {
            var rect = indicator[0].getBoundingClientRect();
            var offset = rect.right - evt.clientX;
            if (offset < 0) {
                offset = 0;
            }
            if (offset > indicator.offsetWidth) {
                offset = indicator.offsetWidth;
            }
            var pointer = $('#opacity-pointer')[0];
            pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
            pointer.style.msTransform = "translateX(-"+offset+"px)";
            pointer.style.transform = "translateX(-"+offset+"px)";
            var opacity = 1 - offset/indicator.offsetWidth;
            if (danmaku_opacity != opacity) {
                danmaku_opacity = opacity;
                change_danmaku_opacity();
                dt.setCookie('danmaku_opacity', opacity, 0);
            }
        }
        
        function stop_move() {
            $(document).off('mousemove, mouseup mouseout');
        }

        move_pointer(evt);
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
        if (isLoop === false) {
            isLoop = true;
        } else {
            isLoop = false;
        }
    });

    var cookie_str = dt.getCookie('autoSwitch');
    if (cookie_str && cookie_str === 'true') {
        autoSwitch = true;
    }
    if (autoSwitch) {
        $('#auto-switch').removeClass('off');
        $('#auto-switch').addClass('on');
    }
    $('#auto-switch').click(function() {
        if (autoSwitch === false) {
            autoSwitch = true;
        } else {
            autoSwitch = false;
        }
        dt.setCookie('autoSwitch', autoSwitch, 0);
    });

    var cookie_str = dt.getCookie('danmaku_font');
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
    $('.setting-reset-button.font').click(function() {
        danmaku_font = ori_danmaku_font;
        dt.setCookie('danmaku_font', danmaku_font, 0);
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

    $('.list-option').click(function(evt) {
        if ($(this).hasClass('quality')) {
            player.setPlaybackQuality(quality_local2youtube($(this).text()));
        } else if ($(this).hasClass('speed')) {
            player.setPlaybackRate(parseFloat($(this).text()));
        } else if ($(this).hasClass('font')) {
            danmaku_font = $(this).text();
            dt.setCookie('danmaku_font', danmaku_font, 0);
        }
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
        $('#danmaku-list-all').empty();
    });

    $('.number-adjust-bar').each(function() {
        var bar = $(this)[0];
        var offset = 0;
        if ($(bar).hasClass('speed')) {
            var cookie_str = dt.getCookie('danmaku_speed');
            if (cookie_str) danmaku_speed = parseFloat(cookie_str);
            $(bar).prev().text(danmaku_speed);
            offset = (1 - (danmaku_speed - 1)/7)*300;
        } else if ($(bar).hasClass('danmaku-num')) {
            var cookie_str = dt.getCookie('max_danmaku');
            if (cookie_str) max_danmaku = parseInt(cookie_str);
            $(bar).prev().text(max_danmaku);
            offset = (1 - (max_danmaku - 10)/110)*300;
        } else if ($(bar).hasClass('scale')) {
            var cookie_str = dt.getCookie('danmaku_scale');
            if (cookie_str) danmaku_scale = parseFloat(cookie_str);
            $(bar).prev().text(danmaku_scale);
            offset = (1 - (danmaku_scale - 1)/4)*300;
        } else if ($(bar).hasClass('time')) {
            var cookie_str = dt.getCookie('existing_time');
            if (cookie_str) existing_time = parseFloat(cookie_str);
            $(bar).prev().text(existing_time);
            offset = (1 - (existing_time - 3)/5)*300;
        } else if ($(bar).hasClass('subtitles-size')) {
            var cookie_str = dt.getCookie('subtitles_font_size');
            if (cookie_str) subtitles_font_size = parseInt(cookie_str);
            offset = (1 - (subtitles_font_size - 8)/32)*300;
            $(bar).prev().text(subtitles_font_size);
        } else if ($(bar).hasClass('subtitles-longevity')) {
            var cookie_str = dt.getCookie('subtitles_longevity');
            if (cookie_str) subtitles_longevity = parseFloat(cookie_str);
            offset = (1 - (subtitles_longevity - 3)/5)*300;
            $(bar).prev().text(subtitles_longevity);
        } else if ($(bar).hasClass('subtitles-opacity')) {
            var cookie_str = dt.getCookie('subtitles_opacity');
            if (cookie_str) subtitles_opacity = parseFloat(cookie_str);
            offset = (1 - subtitles_opacity)*300;
            $(bar).prev().text(subtitles_opacity);
        }
        var pointer = $(bar).children('.number-adjust-pointer')[0];
        pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
        pointer.style.msTransform = "translateX(-"+offset+"px)";
        pointer.style.transform = "translateX(-"+offset+"px)";
    });
    $('.number-adjust-bar').mousedown(function(evt) {
        var bar = $(this)[0];
        function move_pointer(evt) {
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
                danmaku_speed = Math.round((1 - offset/bar.offsetWidth)*70 + 10)/10;
                $(bar).prev().text(danmaku_speed);
                dt.setCookie('danmaku_speed', danmaku_speed, 0);
            } else if ($(bar).hasClass('danmaku-num')) {
                max_danmaku = Math.round((1 - offset/bar.offsetWidth)*110 + 10);
                $(bar).prev().text(max_danmaku);
                dt.setCookie('max_danmaku', max_danmaku, 0);
            } else if ($(bar).hasClass('scale')) {
                danmaku_scale = Math.round((1 - offset/bar.offsetWidth)*40 + 10)/10;
                $(bar).prev().text(danmaku_scale);
                dt.setCookie('danmaku_scale', danmaku_scale, 0);
            } else if ($(bar).hasClass('time')) {
                existing_time = Math.round((1 - offset/bar.offsetWidth)*50 + 30)/10;
                $(bar).prev().text(existing_time);
                dt.setCookie('existing_time', existing_time, 0);
            } else if ($(bar).hasClass('subtitles-size')) {
                subtitles_font_size = Math.round((1 - offset/bar.offsetWidth)*32 + 8);
                $(bar).prev().text(subtitles_font_size);
                dt.setCookie('subtitles_font_size', subtitles_font_size, 0);
            } else if ($(bar).hasClass('subtitles-longevity')) {
                subtitles_longevity = Math.round((1 - offset/bar.offsetWidth)*50 + 30)/10;
                $(bar).prev().text(subtitles_longevity);
                dt.setCookie('subtitles_longevity', subtitles_longevity, 0);
            } else if ($(bar).hasClass('subtitles-opacity')) {
                subtitles_opacity = Math.round((1 - offset/bar.offsetWidth)*100 + 0)/100;
                $(bar).prev().text(subtitles_opacity);
                dt.setCookie('subtitles_opacity', subtitles_opacity, 0);
                change_subtitles_danmaku_opacity();
            }
        }

        function stop_move() {
            $(document).off('mousemove mouseup');
            // $(document).off('mouseout', stop_move);
        }

        move_pointer(evt);
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
            offset = (1 - (danmaku_speed - 1)/7)*300;
            dt.setCookie('danmaku_speed', danmaku_speed, 0);
        } else if ($(bar).hasClass('danmaku-num')) {
            max_danmaku = ori_max_danmaku;
            $(bar).prev().text(max_danmaku);
            offset = (1 - (max_danmaku - 10)/110)*300;
            dt.setCookie('max_danmaku', max_danmaku, 0);
        } else if ($(bar).hasClass('scale')) {
            danmaku_scale = ori_danmaku_scale;
            $(bar).prev().text(danmaku_scale);
            offset = (1 - (danmaku_scale - 1)/4)*300;
            dt.setCookie('danmaku_scale', danmaku_scale, 0);
        } else if ($(bar).hasClass('time')) {
            existing_time = ori_existing_time;
            $(bar).prev().text(existing_time);
            offset = (1 - (existing_time - 3)/5)*300;
            dt.setCookie('existing_time', existing_time, 0);
        } else if ($(bar).hasClass('subtitles-size')) {
            subtitles_font_size = ori_subtitles_font_size;
            $(bar).prev().text(subtitles_font_size);
            offset = (1 - (subtitles_font_size - 8)/32)*300;
            dt.setCookie('subtitles_font_size', subtitles_font_size, 0);
        } else if ($(bar).hasClass('subtitles-longevity')) {
            subtitles_longevity = ori_subtitles_longevity;
            $(bar).prev().text(subtitles_longevity);
            offset = (1 - (subtitles_longevity - 3)/5)*300;
            dt.setCookie('subtitles_longevity', subtitles_longevity, 0);
        } else if ($(bar).hasClass('subtitles-opacity')) {
            subtitles_opacity = 1;
            $(bar).prev().text(subtitles_opacity);
            offset = (1 - subtitles_opacity)*300;
            dt.setCookie('subtitles_opacity', subtitles_opacity, 0);
            change_subtitles_danmaku_opacity();
        }
        var pointer = $(bar).children('.number-adjust-pointer')[0];
        pointer.style.WebkitTransform = "translateX(-"+offset+"px)";
        pointer.style.msTransform = "translateX(-"+offset+"px)";
        pointer.style.transform = "translateX(-"+offset+"px)";
    });

    $('.checkbox-selection').each(function() {
        if ($(this).hasClass('text-outline')) {
            var cookie_str = dt.getCookie('text_outline');
            if (cookie_str) has_text_outline = parseInt(cookie_str);
            if (!has_text_outline) {
                $(this).removeClass('on');
                $(this).addClass('off');
            }
        } else if ($(this).hasClass('hide-controls')) {
            var cookie_str = dt.getCookie('hide_controls');
            if (cookie_str) hide_controls = parseInt(cookie_str);
            if (hide_controls) {
                $(this).removeClass('off');
                $(this).addClass('on');
            }
        }
    });
    $('.checkbox-selection').click(function() {
        $(this).toggleClass('off');
        $(this).toggleClass('on');
        
        if ($(this).hasClass('text-outline')) {
            if ($(this).hasClass('off')) {
                has_text_outline = 0;
            } else {
                has_text_outline = 1;
            }
            dt.setCookie('text_outline', has_text_outline, 0);
            change_danmaku_outline();
        } else if ($(this).hasClass('hide-controls')) {
            if ($(this).hasClass('off')) {
                hide_controls = 0;
            } else {
                hide_controls = 1;
            }
            dt.setCookie('hide_controls', hide_controls, 0);
        } else if ($(this).hasClass('subtitles')) {
            if ($(this).hasClass('off')) {
                $('.subtitles-block').addClass('hidden');
                show_subtitles = 0;
                subtitles_all_clear();
            } else {
                $('.subtitles-block').removeClass('hidden');
                show_subtitles = 1;
            }
        }
    });

    var cookie_str = decodeURIComponent(dt.getCookie('block-rules'));
    if (cookie_str) {
        block_rules = JSON.parse(cookie_str);
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
        for (var j = 0; j < danmaku_pool_list.length; j++) {
            if (danmaku_filter(j)) {
                danmaku_pool_list[j].blocked = true;
            }
        }
        refresh_danmaku_pool();
    }
    $('#add-rule-form').submit(function(evt) {
        var block_type = $('.list-selected.block').text();
        var block_content = $('.block-condition-input').val();
        add_block_rule(block_type, block_content);
        $('.block-condition-input').val('');
        return false;
    });
    $('.block-list').on('click', '.block-rule.rule-status', function() {
        var entry = $(this).parent();
        var block_type = entry.children('.block-rule.rule-type').text();
        var block_content = entry.children('.block-rule.rule-content').text();
        if ($(this).hasClass('off')) {
            $(this).removeClass('off');
            $(this).text('On');
            for (var i = 0; i < block_rules.length; i++) {
                if (block_type === block_rules[i].type && block_content === dt.unescapeHTML(block_rules[i].content)) {
                    block_rules[i].isOn = true;
                    change_block_rule(i);
                    dt.setCookie('block-rules', encodeURIComponent(JSON.stringify(block_rules)), 0);
                    break;
                }
            }
        } else {
            $(this).addClass('off');
            $(this).text('Off');
            for (var i = 0; i < block_rules.length; i++) {
                if (block_type === block_rules[i].type && block_content === dt.unescapeHTML(block_rules[i].content)) {
                    block_rules[i].isOn = false;
                    change_block_rule(i);
                    dt.setCookie('block-rules', encodeURIComponent(JSON.stringify(block_rules)), 0);
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
            if (block_type === block_rules[i].type && block_content === dt.unescapeHTML(block_rules[i].content)) {
                if (block_rules[i].isOn) {
                    block_rules[i].isOn = false;
                    change_block_rule(i);
                }
                block_rules.splice(i, 1);
                dt.setCookie('block-rules', encodeURIComponent(JSON.stringify(block_rules)), 0);
                break;
            }
        }
        entry.remove();
    });

    $('.number-input-arrow').mousedown(function() {
        var target = $(this);
        var number_input = target.siblings('.number-input');

        function inc_dec_number() {
            var num = parseFloat(number_input.val());
            if (isNaN(num)) num = 0;

            num = Math.round(num*100);
            if (target.hasClass('up')) {
                num += 10;
            }
            if (target.hasClass('down') && (number_input.hasClass('negative') || num >= 10)) {
                num -= 10;
            }
            num /= 100;
            number_input.val(num);
        }

        var number_change_time = oldSetInterval(inc_dec_number, 100);
        inc_dec_number();
        target.on('mouseup mouseleave', function() {
            clearInterval(number_change_time);
            target.off('mouseup mouseleave');
        });
    });

    $('#player-background').on('contextmenu', 'div.danmaku', function(evt) {
        evt.originalEvent.preventDefault();
        $('#danmaku-copy-content').attr('data-clipboard-text', $(this).text());
        var element_index = $(this).attr('data-index');
        if (element_index) {
            var ele = danmaku_elements[element_index];
            var danmaku_list_index = danmaku_pool_list.indexOf(ele.ref_danmaku);
            $('.danmaku-menu').attr('data-creator', ele.ref_danmaku.creator)
                            .attr('data-index', danmaku_list_index)
                            .attr('data-type', ele.ref_danmaku.type)
                            .attr('data-danmaku-index', ele.ref_danmaku.index);
            $('#danmaku-block-sender').removeClass('disabled');
            $('#danmaku-locate-it').removeClass('disabled');
            $('#danmaku-reply').removeClass('disabled');
            if (typeof ele.ref_danmaku.index !== 'undefined') {
                $('#danmaku-report').removeClass('disabled');
            } else {
                $('#danmaku-report').addClass('disabled');
            }
        } else {
            $('#danmaku-block-sender').addClass('disabled');
            $('#danmaku-locate-it').addClass('disabled');
            $('#danmaku-reply').addClass('disabled');
            $('#danmaku-report').addClass('disabled');
        }

        var rect = $('#player-container').offset();
        $('.danmaku-menu').removeClass('hidden');
        if (evt.pageY + $('.danmaku-menu')[0].scrollHeight > player_height + rect.top) {
            $('.danmaku-menu')[0].style.top = player_height + rect.top - $('.danmaku-menu')[0].scrollHeight+'px';
        } else {
            $('.danmaku-menu')[0].style.top = evt.pageY+'px';
        }
        if (evt.pageX + $('.danmaku-menu')[0].scrollWidth > player_width + rect.left) {
            $('.danmaku-menu')[0].style.left = player_width + rect.left - $('.danmaku-menu')[0].scrollWidth+'px';
        } else {
            $('.danmaku-menu')[0].style.left = evt.pageX+'px';
        }

        function hide_menu() {
            $('.danmaku-menu').addClass('hidden');
            $(document).off('click', hide_menu);
        }
        $(document).click(hide_menu);
    });
    new ZeroClipboard(document.getElementById("danmaku-copy-content"));
    $('#danmaku-block-sender').click(function(e) {
        if ($(this).hasClass('disabled')) return;

        var block_type = 'User';
        var block_content = $('.danmaku-menu').attr('data-creator');
        add_block_rule(block_type, block_content);
    });
    $('#danmaku-locate-it').click(function(e) {
        if ($(this).hasClass('disabled')) return;

        var danmaku_pool_index = $('.danmaku-menu').attr('data-index');
        $('.per-bullet.selected').removeClass('selected');
        var target = $('.per-bullet')[danmaku_pool_index];
        target.classList.add('selected');
        $('#danmaku-list').scrollTop(target.offsetHeight*danmaku_pool_index);
    });
    $('#danmaku-reply').click(function(e) {
        if ($(this).hasClass('disabled')) return;
        
        $('.input-layon-block').removeClass('hidden');
        var reply_to = $('.danmaku-menu').attr('data-creator');
        $('#danmaku-reply-input').val(reply_to);
        $('#danmaku-input').addClass('reply')
                            .focus();
    });
    $('#danmaku-report').click(function() {
        if ($(this).hasClass('disabled')) return;

        $('#report-danmaku-form').removeClass('hidden');
        $('#report-danmaku-index').val($('.danmaku-menu').attr('data-danmaku-index'));
        var danmaku_type = $('.danmaku-menu').attr('data-type');
        if (danmaku_type === 'Advanced') {
            $('#report-danmaku-type').val('advanced');
        } else {
            $('#report-danmaku-type').val('danmaku');
        }
        $('#report-danmaku-textarea').focus();
        player.pauseVideo();
    });
    $('#report-danmaku-form').submit(function() {
        dt.send_report($(this), 'danmaku');
        return false;
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

    $('#danmaku-pool').on('click', 'div.per-bullet', function(evt) {
        $('div.per-bullet.selected').removeClass('selected');
        $(this).addClass('selected');
    });
    $('#danmaku-pool').on('contextmenu', 'div.per-bullet', function(evt) {
        evt.originalEvent.preventDefault();
        $('div.per-bullet.selected').removeClass('selected');
        $(this).addClass('selected');

        $('#danmaku-pool-copy-content').attr('data-clipboard-text', $(this).children('.bullet-content-value').text());
        var ref_danmaku = danmaku_pool_list[$(this).attr('data-index')];
        $('.danmaku-pool-menu').attr('data-creator', ref_danmaku.creator)
                            .attr('data-type', ref_danmaku.type)
                            .attr('data-danmaku-index', ref_danmaku.index);
        if (typeof ref_danmaku.index !== 'undefined') {
            $('#danmaku-pool-report').removeClass('disabled');
        } else {
            $('#danmaku-pool-report').addClass('disabled');
        }

        var rect = $('#player-container').offset();
        $('.danmaku-pool-menu').removeClass('hidden');
        if (evt.pageY + $('.danmaku-pool-menu')[0].scrollHeight > $(document).height()) {
            $('.danmaku-pool-menu')[0].style.top = $(document).height() + rect.top - $('.danmaku-pool-menu')[0].scrollHeight+'px';
        } else {
            $('.danmaku-pool-menu')[0].style.top = evt.pageY+'px';
        }
        if (evt.pageX + $('.danmaku-pool-menu')[0].scrollWidth > $(document).width()) {
            $('.danmaku-pool-menu')[0].style.left = $(document).width() + rect.left - $('.danmaku-pool-menu')[0].scrollWidth+'px';
        } else {
            $('.danmaku-pool-menu')[0].style.left = evt.pageX+'px';
        }
        var hide_menu = function() {
            $('.danmaku-pool-menu').addClass('hidden');
            $(document).off('click', hide_menu);
        }
        $(document).click(hide_menu);
    });
    new ZeroClipboard(document.getElementById("danmaku-pool-copy-content"));
    $('#danmaku-pool-block-sender').click(function() {
        var block_type = 'User';
        var block_content = $('.danmaku-pool-menu').attr('data-creator');
        add_block_rule(block_type, block_content);
    });
    $('#danmaku-pool-check-all-sent').click(function() {
        $('#danmaku-list-all').empty();
        var listNode = $('#danmaku-list-all')[0];
        var user = $('.danmaku-pool-menu').attr('data-creator');
        for (var i = 0; i < danmaku_pool_list.length; i++) {
            if (danmaku_pool_list[i].creator.toString() === user) {
                listNode.appendChild(generate_danmaku_pool_entry(i))
            }
        }
        $('.player-full-setting.check-all-sent').removeClass('hidden');
    });
    $('#danmaku-pool-report').click(function() {
        if ($(this).hasClass('disabled')) return;
        $('#report-danmaku-form').removeClass('hidden');
        $('#report-danmaku-index').val($('.danmaku-pool-menu').attr('data-danmaku-index'));
        var danmaku_type = $('.danmaku-pool-menu').attr('data-type');
        if (danmaku_type === 'Advanced') {
            $('#report-danmaku-type').val('advanced');
        } else {
            $('#report-danmaku-type').val('danmaku');
        }
        $('#report-danmaku-textarea').focus();
        player.pauseVideo();
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
            $('#danmaku-type-input').val('Scroll');
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

    // sending danmaku form
    $('#shooter').submit(function(evt){
        var button = document.querySelector('#fire-button');
        button.disabled = true;

        var error = false;
        var content = $('#danmaku-input').val().trim();
        if (!content) {
            dt.pop_ajax_message('You can\'t post empty comment.', 'error');
            error = true;
        } else if (content.length > 350) {
            dt.pop_ajax_message('Comment is too long (less than 350 characters).', 'error');
            error = true;
        }

        if (error) {
            button.disabled = false;
            return false;
        }

        if (ws.readyState === 1) {
            ws.send($(this).serialize()+'&'+$.param({timestamp: player.getCurrentTime()}));
        }
        $.ajax({
            type: "POST",
            url: '/video/danmaku/'+clip_id,
            data: $(this).serialize()+'&'+$.param({timestamp: player.getCurrentTime()}),
            success: function(result) {
                if(!result.error) {
                    // var entry = result.entry;
                    $('#danmaku-input').val('');
                    dt.pop_ajax_message('Fired!', 'success');
                    // entry.timestamp = player.getCurrentTime() + 0.05;
                    // entry.blocked = false;
                    // var listNode = document.getElementById("danmaku-list");
                    // danmaku_pool_list.push(entry);
                    // listNode.appendChild(generate_danmaku_pool_entry(danmaku_pool_list.length-1));
                    // normal_danmaku_sequence.addOne(entry);
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
                button.disabled = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                button.disabled = false;
            }
        });
        return false;
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
            as_percent: $('input[name="as-percent"]').is(':checked'),
            relative: $('input[name="relative"]').is(':checked'),
            type: 'Advanced',
        }
        var bul = document.createElement('div');
        bul.setAttribute('class', 'danmaku');
        bul.setAttribute('style', preview_danmaku.css);
        bul.style.left = player_width+'px';
        var text = document.createTextNode(preview_danmaku.content);
        bul.appendChild(text);
        player_background.appendChild(bul);

        var new_danmaku_element = {idle: false, generating: false, posX: 0, posY: 0, clear_request: false, element: bul, ref_danmaku: preview_danmaku};
        Danmaku_Animation(new_danmaku_element);
        dt.pop_ajax_message('Previewing!', 'success');
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
        if ($('#advanced-use-cur-timestamp').is(':checked')) {
            data += '&'+$.param({timestamp: player.getCurrentTime()});
        } else {
            data += '&'+$.param({timestamp: $('#advanced-timestamp').val()});
        }

        $.ajax({
            type: "POST",
            url: '/video/advanced_danmaku/'+clip_id,
            data: data,
            success: function(result) {
                if(!result.error) {
                    $('#advanced-danmaku-content').val('');
                    dt.pop_ajax_message('Advanced danmaku has been submitted. Please wait for approval by the UPer.', 'success');
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
                button.disabled = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                button.disabled = false;
            }
        });

        return false;
    });

    $('#subtitles-danmaku-form input[type="button"]').click(function() {
        var error = subtitles_danmaku_form_check();
        if (error) return;

        var subtitles_list = [];
        var lines = $('textarea[name="subtitles"]').val().replace(/\r/g, '').split('\n');
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line) {
                var result = line.match(dt.subtitle_format);
                if (result[4]) {
                    subtitles_list.push({
                        'timestamp': parseInt(result[1])*60+parseInt(result[2])+parseInt(result[3])/100,
                        'content': dt.escapeHTML(result[4]),
                        'type': 'Subtitles',
                    });
                }
            }
        }
        subtitles_danmaku_container[-1] = new DanmakuTimeSequence(subtitles_list);
        var checkbox = $('.checkbox-selection.subtitles');
        if (checkbox.hasClass('off')) {
            checkbox.trigger('click');
        }
        dt.pop_ajax_message('Previewing', 'success');
    });
    $('#subtitles-danmaku-form').submit(function(evt) {
        var button = document.querySelector('#subtitles-danmaku-form .special-danmaku-button.special');
        button.disabled = true;

        var error = subtitles_danmaku_form_check();
        if (error) {
            button.disabled = false;
            return false;
        }

        $.ajax({
            type: "POST",
            url: '/video/subtitles_danmaku/'+clip_id,
            data: $(this).serialize(),
            success: function(result) {
                if(!result.error) {
                    dt.pop_ajax_message('Subtitles have been submitted. Please wait for approval by the UPer.', 'success');
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
                button.disabled = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                button.disabled = false;
            }
        });
        return false;
    });

    new ZeroClipboard(document.getElementById("copy-code"));
    new ZeroClipboard(document.getElementById("copy-output"));
    $('#clear-code').click(function() {
        $('#textarea-code-danmaku').val('');
    });
    $('#clear-output').click(function() {
        $('#textarea-danmaku-output').val('');
    });
    $('#code-danmaku-form input[type="button"]').click(function() {
        var error = code_danmaku_form_check();
        if (error) return;

        var code = $('#textarea-code-danmaku').val().trim();
        dt.pop_ajax_message('Previewing', 'success');
        execute_code_danmaku(code);
    });
    $('#code-danmaku-form').submit(function() {
        var button = document.querySelector('#code-danmaku-form .special-danmaku-button.special');
        button.disabled = true;

        var error = code_danmaku_form_check();
        if (error) {
            button.disabled = false;
            return false;
        }

        var data = $(this).serialize();
        if ($('#code-use-cur-timestamp').is(':checked')) {
            data += '&'+$.param({timestamp: player.getCurrentTime()});
        } else {
            data += '&'+$.param({timestamp: $('#code-timestamp').val()});
        }

        $.ajax({
            type: "POST",
            url: '/video/code_danmaku/'+clip_id,
            data: data,
            success: function(result) {
                if(!result.error) {
                    dt.pop_ajax_message('Program has been submitted. Please wait for approval by the UPer.', 'success');
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
                button.disabled = false;
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
                button.disabled = false;
            }
        });
        return false;
    });

    var param_timestamp = parseFloat(dt.getParameterByName('timestamp'));
    var last_timestamp = dt.getCookie(video_id);
    if (!isNaN(param_timestamp)) {
        player_seek(param_timestamp - 0.1);
    } else if (last_timestamp) {
        var parts = last_timestamp.split('|');
        var last_index = parts[0];
        last_timestamp = parseFloat(parts[1]);
        if (last_index === $('#clip-index').val() && last_timestamp !== 0) {
            player_seek(last_timestamp);
        }
    }
    var autoplay = dt.getParameterByName('autoplay');
    if (autoplay === '1') {
        player.playVideo();
    }

    ws = new WebSocket("ws://104.197.128.177/"+clip_id+"?session="+dt.getCookie('db_session'));
    ws.onopen = function (event) {
        console.log('WebSocket connected!');
    }
    ws.onclose = function(event) {
        console.log('WebSocket closed by server!');
    }
    ws.onmessage = function (event) {
        // console.log('ws:'+event.data);
        var data = JSON.parse(event.data);
        if (data.type === 'viewers') {
            $('span.current-number').text(dt.numberWithCommas(data.current));
            $('span.peak-number').text(dt.numberWithCommas(data.peak));
        } else if (data.type === 'danmaku') {
            var entry = data.entry;
            var listNode = document.getElementById("danmaku-list");
            danmaku_pool_list.push(entry);
            if (danmaku_filter(danmaku_pool_list.length-1)) {
                entry.blocked = true;
            } else {
                entry.blocked = false;
            }
            listNode.appendChild(generate_danmaku_pool_entry(danmaku_pool_list.length-1));
            normal_danmaku_sequence.addOne(entry);
        }
    }
    ws.onerror = function(evt) {
        console.log(JSON.stringify(evt));
    }

    //redirect message
    if (typeof console == "object" && console.log) {
        var oldLog = console.log;
        console.log = function (message) {
            var textarea_output = document.getElementById('textarea-danmaku-output');
            textarea_output.value += message+'\n';
            textarea_output.scrollTop = textarea_output.scrollHeight;
            oldLog.apply(console, arguments);
        };
    } else {
        console = {
            log: function(message) {
                var textarea_output = document.getElementById('textarea-danmaku-output');
                textarea_output.value += message+'\n';
                textarea_output.scrollTop = textarea_output.scrollHeight;
            }
        }
    }

    var gOldOnError = window.onerror;
    window.onerror = function(errorMsg, url, lineNumber) {
        var textarea_output = document.getElementById('textarea-danmaku-output');
        textarea_output.value += errorMsg+'\n';
        textarea_output.scrollTop = textarea_output.scrollHeight;
        if (gOldOnError) {
        // Call previous handler.
            return gOldOnError(errorMsg, url, lineNumber);
        }
        return false;
    };
}

function code_danmaku_form_check() {
    var error = false;
    var code = $('#textarea-code-danmaku').val().trim();
    if (!code) {
        dt.pop_ajax_message('Please write some code.');
        error = true;
    } else if (/([^a-zA-Z_$]|^)(document|window|location|oldSetInterval|oldSetTimeout|XMLHttpRequest|XDomainRequest|jQuery|\$)([^a-zA-Z_$]|$)/.test(code)) {
        dt.pop_ajax_message('Code contains invalid keywords. Please check the document.', 'error');
        error = true;
    }
    return error;
}

function subtitles_danmaku_form_check() {
    var error = false;
    var name = $('input[name="name"]').val().trim();
    if (!name) {
        dt.pop_ajax_message('Please fill in a name', 'error');
        error = true;
    } else if (name.length > 350) {
        dt.pop_ajax_message('Name is too long (less than 350 characters).', 'error');
        error = true;
    }

    var subtitle_content = $('textarea[name="subtitles"]').val().replace(/\r/g, '').trim();
    if (!subtitle_content) {
        dt.pop_ajax_message('Please fill in subtitles.', 'error');
        error = true;
    } else {
        var lines = subtitle_content.split('\n');
        var pos = 0;
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line) {
                var result = line.match(dt.subtitle_format);
                if (!result || parseInt(result[2]) >= 60) {
                    dt.pop_ajax_message('Format error at line '+(i+1), 'error');
                    $('textarea[name="subtitles"]')[0].focus();
                    $('textarea[name="subtitles"]')[0].setSelectionRange(pos, pos);
                    error = true;
                    break;
                }
            }
            pos +=  lines[i].length+1;
        }
    }
    return error;
}

function advanced_danmaku_form_check() {
    var error = false;
    var content = $('#advanced-danmaku-content').val().trim();
    if (!content) {
        dt.pop_ajax_message('You can\'t post empty comment.', 'error');
        error = true;
    } else if (content.length > 350) {
        dt.pop_ajax_message('Comment is too long (less than 350 characters).', 'error');
        error = true;
    }

    $('.advanced-danmaku-input.number-input').each(function() {
        var num = parseFloat($(this).val());
        if (isNaN(num)) $(this).val('0');
    })

    if ($('input[name="birth-position-X"]').val() === $('input[name="death-position-X"]').val()
        && $('input[name="birth-position-Y"]').val() === $('input[name="death-position-Y"]').val()
        && $('input[name="longevity"]').val() === '0') {
        dt.pop_ajax_message('Longevity must be specified for static danmaku.', 'error');
        error = true;
    }
    if (($('input[name="birth-position-X"]').val() !== $('input[name="death-position-X"]').val() && $('input[name="speed-X"]').val() === '0')
        || ($('input[name="birth-position-Y"]').val() !== $('input[name="death-position-Y"]').val() && $('input[name="speed-Y"]').val() === '0')) {
        dt.pop_ajax_message('Speed must be specified for moving danmaku.', 'error');
        error = true;
    }

    if (!$('textarea[name="danmaku-css"]').val().trim()) {
        dt.pop_ajax_message('CSS must be specified.', 'error');
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

function danmaku_timestamp_lower_compare(x, y) {
    if (x.timestamp != y.timestamp) {
        return x.timestamp < y.timestamp;
    } else {
        return danmaku_date_lower_compare(x, y);
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
    for (var i = 0; i < danmaku_pool_list.length; i++) {
        listNode.appendChild(generate_danmaku_pool_entry(i));
    }
}

function generate_danmaku_pool_entry(i) {
    var entry = danmaku_pool_list[i];
    var per_container = document.createElement('div');
    if (entry.blocked) {
        per_container.className = "per-bullet blocked";
    } else {
        per_container.className = "per-bullet";
    }
    per_container.setAttribute('data-index', i);

    var time_value = document.createElement('div');
    time_value.className = "bullet-time-value";
    time_value.appendChild(document.createTextNode(dt.secondsToTime(entry.timestamp)));
    var content_value = document.createElement('div');
    content_value.className = "bullet-content-value";
    content_value.title = dt.unescapeHTML(entry.content);
    content_value.appendChild(document.createTextNode(dt.unescapeHTML(entry.content)));
    var date_value = document.createElement('div');
    date_value.className = "bullet-date-value";
    date_value.appendChild(document.createTextNode(entry.created));
    
    per_container.appendChild(time_value);
    per_container.appendChild(content_value);
    per_container.appendChild(date_value);
    return per_container;
}

function refresh_danmaku_pool() {
    var pool_list = document.querySelectorAll('#danmaku-list .per-bullet');
    for (var i = 0; i < danmaku_pool_list.length; i++) {
        if (danmaku_pool_list[i].blocked) {
            pool_list[i].classList.add('blocked');
        } else {
            pool_list[i].classList.remove('blocked');
        }
    }

    pool_list = document.querySelectorAll('#danmaku-list-all .per-bullet');
    for (var i = 0; i < pool_list.length; i++) {
        if (danmaku_pool_list[pool_list[i].getAttribute('data-index')].blocked) {
            pool_list[i].classList.add('blocked');
        } else {
            pool_list[i].classList.remove('blocked');
        }
    }
}

$(document).ready(function() {
    video_id = $('#video-id').val();
    clip_id = $('#clip-id').val();
    clip_index = $('#clip-index').val();
    clip_vid = $('#clip-vid').val();

    var tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

    player_resize();
    onYouTubeIframeAPIReady = function() {
        dt.player = new YT.Player('player', {
                width: player_inner_width,
                height: player_inner_height,
                videoId: clip_vid,
                playerVars: {
                autoplay: 0,
                controls: 0,
                showinfo: 0,
                modestbranding: 1,
                enablejsapi: 1,
                rel: 0,
                fs: 0,
            },
            events: {
                'onReady': dt.onPlayerReady,
                'onStateChange': dt.onPlayerStateChange,
            }
        });
    }

    // Retrieve Danmaku
    load_danmaku(JSON.parse($('#danmaku-buffer').val()));
    $.ajax({
        type: "GET",
        url: danmaku_prefix + clip_id + '/danmaku',
        dataType: 'json',
        success: load_danmaku,
    });
    $.ajax({
        type: "GET",
        url: danmaku_prefix + clip_id + '/advanced',
        dataType: 'json',
        success: load_danmaku,
    });
    $.ajax({
        type: "GET",
        url: danmaku_prefix + clip_id + '/code',
        dataType: 'json',
        success: load_danmaku,
    });
    $.ajax({
        type: "GET",
        url: danmaku_prefix + clip_id + '/subtitles',
        dataType: 'json',
        success: load_subtitles,
    });
});

function load_danmaku(danmaku_list) {
    var count = 0;
    for(var i = 0; i < danmaku_list.length; i++) {
        if (danmaku_list[i].hasOwnProperty('approved') && !danmaku_list[i].approved) continue;

        count++;
        danmaku_list[i].blocked = false;
        danmaku_pool_list.push(danmaku_list[i]);
    }
    $('#total-danmaku-span').text(dt.numberWithCommas(count + parseInt($('#total-danmaku-span').text())));
    dt.quick_sort(danmaku_pool_list, 0, danmaku_pool_list.length - 1, danmaku_date_lower_compare);
    generate_danmaku_pool_list();
    normal_danmaku_sequence.addMult(danmaku_list);
}

function load_subtitles(subtitles_list) {
    for (var i = 0; i < subtitles_list.length; i++) {
        if (!subtitles_list[i].approved) continue;

        $('.subtitles-list').append('<label class="check-label subtitle">\
                                      <div class="pseudo-checkbox"></div>\
                                      <input type="checkbox" class="hidden">\
                                      <span>'+dt.escapeHTML(subtitles_list[i].name)+'</span>\
                                    </label>')

        var content = subtitles_list[i].subtitles;
        var subtitles = [];
        var lines = content.split('\n');
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (line) {
                var result = line.match(dt.subtitle_format);
                if (result[4]) {
                    subtitles.push({
                        'timestamp': parseInt(result[1])*60+parseInt(result[2])+parseInt(result[3])/100,
                        'content': result[4],
                        'type': 'Subtitles',
                    });
                }
            }
        }
        subtitles_danmaku_backup[i] = new DanmakuTimeSequence(subtitles);
    }

    $('label.check-label.subtitle input[type="checkbox"]').change(function() {
        if ($(this).is(':checked')) {
            $(this).prev().addClass('checked');
        } else {
            $(this).prev().removeClass('checked');
        }

        var subtitle_index = $('label.check-label.subtitle').index($(this).parent()).toString();
        if ($(this).is(':checked')) {
            subtitles_danmaku_container[subtitle_index] = subtitles_danmaku_backup[subtitle_index];
        } else {
            delete subtitles_danmaku_container[subtitle_index];
            subtitles_one_clear(subtitle_index);
        }
    });
}

function get_player_inner_pos_left() {
    return (player_width + player_inner_width)/2;
}

function get_player_inner_pos_right() {
    return (player_width - player_inner_width)/2;
}

function get_player_inner_pos_top() {
    return (player_height - player_inner_height)/2;
}

function get_player_inner_pos_bottom() {
    return (player_height + player_inner_height)/2;
}

function create_danmaku(content, update_callback) {
    if (typeof update_callback !== 'function') throw {name: 'TypeError', message: 'The second parameter in create_danmaku() must be a function.'};
    var new_danmaku = {
        content: content,
        callback: update_callback,
        type: 'Custom',
    }
    var bul = document.createElement('div');
    bul.setAttribute('class', 'danmaku');
    bul.innerHTML = content;
    var player_background = document.getElementById('player-background');
    player_background.appendChild(bul);

    var new_danmaku_element = {prev: null, next: null, clear_request: false, element: bul, ref_danmaku: new_danmaku};
    linked_elements.push(new_danmaku_element);
    Danmaku_Animation(new_danmaku_element);
    return bul;
}

function code_all_clear() {
    for (var i = 0; i < code_intervals; i++) {
        clearInterval(code_intervals[i]);
    }
    for (var i = 0; i < code_timeouts; i++) {
        clearTimeout(code_timeouts[i]);
    }
    code_intervals = [];
    code_timeouts = [];

    var curNode = linked_elements.head;
    while (curNode) {
        if (typeof curNode.belong_to === 'undefined') {
            curNode.clear_request = true;
        }
        curNode = curNode.next;
    }
}

function execute_code_danmaku(code) {
    try {
        eval(code);
    } catch (err) {
        console.log(err.name+': '+err.message);
    }
}
//end of the file
} (dt, jQuery));