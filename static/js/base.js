var dt = {};
(function(dt, $) {
dt.quick_sort = function (array, start, end, compare) {
    if (start < end) {
        var pivotValue = array[end];
        var storeIndex = start;
        for (var i = start; i < end; i++) {
            if (compare(array[i], pivotValue)) {
                var temp = array[storeIndex];
                array[storeIndex] = array[i];
                array[i] = temp;
                storeIndex += 1;
            }
        }
        var temp = array[storeIndex];
        array[storeIndex] = array[end];
        array[end] = temp;

        dt.quick_sort(array, start, storeIndex - 1, compare);
        dt.quick_sort(array, storeIndex + 1, end, compare);
    }
}

dt.numberWithCommas = function(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

dt.hsl2rgb = function(hsl) {
    var h = hsl[0];
    var s = hsl[1];
    var l = hsl[2];

    var r, g, b;
    var c = (1 - Math.abs(2*l - 1))*s;
    h = h/60;
    var x = c*(1 - Math.abs(h%2 - 1));
    if (0 <= h && h < 1) {
        r = c;
        g = x;
        b = 0;
    } else if (1 <= h && h < 2) {
        r = x;
        g = c;
        b = 0;
    } else if (2 <= h && h < 3) {
        r = 0;
        g = c;
        b = x;
    } else if (3 <= h && h < 4) {
        r = 0;
        g = x;
        b = c;
    } else if (4 <= h && h < 5) {
        r = x;
        g = 0;
        b = c;
    } else {
        r = c;
        g = 0;
        b = x;
    }
    var m = l - c/2;
    return [Math.round((r+m)*255), Math.round((g+m)*255), Math.round((b+m)*255)];
}

dt.pop_ajax_message = function(content, type) {
     $('#ajax-message-box').append('<div class="ajax-message '+type+'"> \
            <div class="ajax-icon '+type+'"></div> \
            <div class="ajax-content">'+content+'</div> \
        </div>');

    var lasts = $('div.ajax-message:last-child');
    lasts.height(lasts[0].scrollHeight);
    // console.log(lasts[0].scrollHeight);

    setTimeout(function() {
        lasts.height(0);
        setTimeout(function() {
            lasts.remove();
        }, 280);
    }, 5000);
}

function count_new_subscriptions() {
    $.ajax({
        type: "POST",
        url: '/user/new_subscriptions',
        success: function(result) {
            if(!result.error) {
                $('#user-subscriptions-new-num').text(result.count);
                dt.setCookie('new_subscriptions', result.count, 0);
            } else {
                console.log(result.error);
            }
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });
}

var user_box_hide;
var user_box_clear;
$(document).ready(function() {
    // if ($('#portrait').length != 0) {
    //     var uesr_id = $('#portrait').attr('data-id');
    //     var cookie = dt.getCookie(uesr_id+'_check');
    //     if (!cookie) {
    //         var now = new Date().toUTCString();
    //         var extime = 10 * 60 * 1000; // 10 mins wait
    //         dt.setCookie(uesr_id+'_check', now, extime);
    //         count_new_subscriptions();
    //     }
    //     var num = dt.getCookie('new_subscriptions');
    //     $('#user-subscriptions-new-num').text(num);
    // }
    register_subscribe_button_hover();
    register_subscribe_button_action();

    $('#portrait').hover(function() {
        $('#user-box').addClass('show');
        $('#user-box').removeClass('hide');
        clearTimeout(user_box_hide);
        clearTimeout(user_box_clear);
    }, function() {
        user_box_hide = setTimeout(function() {
            $('#user-box').addClass('hide');
            user_box_clear = setTimeout(function() {
                $('#user-box').removeClass('show');
            }, 100);
        }, 100);
    });

    $('span.commas_number').each(function() {
        $(this).text(dt.numberWithCommas($(this).text()) );
    });
    $('div.preview-time').each(function() {
        $(this).text(dt.secondsToTime($(this).text()) );
    });

    $('div.emoticons-select').append('<div class="emoticons-menu">\
                <div class="emoticons-option">(⌒▽⌒)</div>\
                <div class="emoticons-option">（￣▽￣）</div>\
                <div class="emoticons-option">(=・ω・=)</div>\
                <div class="emoticons-option">=￣ω￣=</div>\
                <div class="emoticons-option">(｀・ω・´)</div>\
                <div class="emoticons-option">(〜￣△￣)〜</div>\
                <div class="emoticons-option">(･∀･)</div>\
                <div class="emoticons-option">(°∀°)ﾉ</div>\
                <div class="emoticons-option">(￣3￣)</div>\
                <div class="emoticons-option">╮(￣▽￣)╭</div>\
                <div class="emoticons-option">╮(╯▽╰)╭</div>\
                <div class="emoticons-option">╮(￣▽￣")╭</div>\
                <div class="emoticons-option">( ´_ゝ｀)</div>\
                <div class="emoticons-option">←_←</div>\
                <div class="emoticons-option">→_→</div>\
                <div class="emoticons-option">(&lt;_&lt;)</div>\
                <div class="emoticons-option">(&gt;_&gt;)</div>\
                <div class="emoticons-option">(;¬_¬)</div>\
                <div class="emoticons-option">("▔□▔)/</div>\
                <div class="emoticons-option">(ﾟДﾟ≡ﾟдﾟ)!?</div>\
                <div class="emoticons-option">Σ(ﾟдﾟ;)</div>\
                <div class="emoticons-option">Σ( ￣□￣||)</div>\
                <div class="emoticons-option">Σ(っ °Д °;)っ</div>\
                <div class="emoticons-option">（ˉ﹃ˉ）</div>\
                <div class="emoticons-option">(´；ω；`)</div>\
                <div class="emoticons-option">（/TДT)/</div>\
                <div class="emoticons-option">(´･ω･`)</div>\
                <div class="emoticons-option">(^・ω・^ )</div>\
                <div class="emoticons-option">(｡･ω･｡)</div>\
                <div class="emoticons-option">(●￣(ｴ)￣●)</div>\
                <div class="emoticons-option">(≧∀≦)</div>\
                <div class="emoticons-option">ε=ε=(ノ≧∇≦)ノ</div>\
                <div class="emoticons-option">(´･_･`)</div>\
                <div class="emoticons-option">( ˙-˙ )</div>\
                <div class="emoticons-option">(-_-#)</div>\
                <div class="emoticons-option">（￣へ￣）</div>\
                <div class="emoticons-option">(￣ε(#￣) Σ</div>\
                <div class="emoticons-option">ヽ(`Д´)ﾉ</div>\
                <div class="emoticons-option">(╯°口°)╯(┴—┴</div>\
                <div class="emoticons-option">（#-_-)┯━┯</div>\
                <div class="emoticons-option">_(:3」∠)_</div>\
                <div class="emoticons-option">T_T</div>\
                <div class="emoticons-option">QAQ</div>\
                <div class="emoticons-option">╭(°A°`)╮</div>\
                <div class="emoticons-option">(ಥ_ಥ)</div>\
                <div class="emoticons-option">(ಡωಡ)</div>\
                <div class="emoticons-option">(๑•̀ㅂ•́)و✧</div>\
                <div class="emoticons-option">(ง •̀_•́)ง</div>\
                <div class="emoticons-option">( ﾟДﾟ)_σ異議あり!!</div>\
            </div>\
            <div class="emoticons-label">Emoticons</div>');
    $('div.emoticons-select').click(function() {
        $(this).toggleClass('show');
    });
    $('div.emoticons-option').click(function(evt) {
        var textarea = $(evt.target).parent().parent().parent().siblings('textarea');
        textarea.val(textarea.val() + $(evt.target).text());
    });

    $('label.check-label input[type="checkbox"]').change(function(evt) {
        if ($(this).is(':checked')) {
            $(this).prev().addClass('checked');
        } else {
            $(this).prev().removeClass('checked');
        }
    });

    if ($('.list-selected').length > 0) {
        $('.list-selected.auto').each(function(evt) {
            var first_option = $($(this).prev().children()[0]);
            if (first_option.length > 0) {
                first_option.addClass('active');
                $(this).text(first_option.text());
                $(this).next().val(first_option.text());
            }
        });
        $(document).click(function() {
            $('.list-selection').addClass('hidden');
        });
        $(document).on('click', '.list-selected', function(evt) {
            evt.stopPropagation();
            $('.list-selection').addClass('hidden');
            $(this).prev().removeClass('hidden');
        });
        $(document).on('click', '.list-option', function(evt) {
            var list = $(this).parent();
            list.next().text($(this).text());
            list.next().next().val($(this).text());
            $(this).siblings().removeClass('active');
            $(this).addClass('active');
        });
    }

    $('.number-input').on('input propertychange paste', function (e) {
        if (($(this).hasClass('negative') && /^[-]?\d*[.]?\d*$/.test($(this).val()))
            || (!$(this).hasClass('negative') && /^\d*[.]?\d*$/.test($(this).val()))) { // is a number
            $(this).attr('data-old', $(this).val());
        } else { // not a number, preserve original value
            $(this).val($(this).attr('data-old'));
        }
    });

    $('#account-right-section').on('click', '.single-checkbox', function(evt) {
        $(this).toggleClass('checked');
    });
    $('#action-select .option-entry.deselect').click(function() {
        $('.single-checkbox.checked').removeClass('checked');
    });
    $('#action-select .option-entry.select').click(function() {
        $('.single-checkbox').addClass('checked');
    });
    deleteWindow(window.location.pathname+'/delete');

    if ($('.popup-window-container').length > 0) {
        $(document).keydown(function(e) {
            if (e.keyCode == 27) {
                $('body').removeClass('background');
                $('.popup-window-container').removeClass('show');
            }
        });
    }

    $('.popup-box .inline-button').click(function() {
        $(this).parent().parent().addClass('hidden');
    });
    if ($('.popup-box').length > 0) {
        $(document).keydown(function(evt) {
            if (evt.keyCode == 27) {
                $('.popup-box').addClass('hidden');
            }
        });
    }
});

function deleteWindow(url) {
    $('input.delete-button').click(function(evt) {
        var ids= $(evt.target).attr('data-id').split(';');
        dt.pop_ajax_message('Removing...', 'info');
        $(evt.target).prop('disabled', true);
        $.ajax({
            type: "POST",
            url: url,
            data: {ids: ids},
            success: function(result) {
                console.log(result);
                if (!result.error) {
                    dt.pop_ajax_message('Removed!', 'success');
                    for (var i = 0; i < ids.length; i++) {
                        $('div.content-entry.'+ids[i]).remove();
                    }
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
                $(evt.target).prop('disabled', false);
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                $(evt.target).prop('disabled', false);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
        $('div.popup-window-container.remove').removeClass('show');
    });

    $('div.delete-button').click(function(evt) {
        $('div.popup-window-container.remove').removeClass('show');
    });

    $('#action-select .option-entry.delete').click(function() {
        var checked_boxes = $('div.single-checkbox.checked');
        if (checked_boxes.length !== 0) {
            $('div.popup-window-container.remove').addClass('show');
            $('div.delete-target-name').remove();
            var ids = $(checked_boxes[0]).attr('data-id');
            var title = $(checked_boxes[0]).attr('data-title');
            $('div.delete-buttons-line').before('<div class="delete-target-name">'+dt.escapeHTML(title)+'</div>');
            for (var i = 1; i < checked_boxes.length; i++) {
                ids += ';'+ $(checked_boxes[i]).attr('data-id');
                title = $(checked_boxes[i]).attr('data-title');
                $('div.delete-buttons-line').before('<div class="delete-target-name">'+dt.escapeHTML(title)+'</div>');
            }
            $('input.delete-button').attr('data-id', ids);
        }
    });
}

function register_subscribe_button_hover() {
    $('.subscribe-button').off('mouseenter mouseleave');
    $('.subscribe-button').hover(function() {
        if ($(this).hasClass('unsubscribe')) {
            $(this).children('.subscribe-text').text('Unsubscribe');
        }
    }, function() {
        if ($(this).hasClass('unsubscribe')) {
            $(this).children('.subscribe-text').text('Subscribed');
        }
    });
}

function register_subscribe_button_action() {
    $('.subscribe-button').off('click');
    $('.subscribe-button').click(function() {
        var button = $(this);
        var uploader_id = button.attr('data-id');
        var action = '';
        if (button.hasClass('unsubscribe')) {
            action = "/user/unsubscribe/"+uploader_id;
        } else {
            action = "/user/subscribe/"+uploader_id;
        }
        $.ajax({
            type: "POST",
            url: action,
            success: function(result) {
                if(!result.error) {
                    if (button.hasClass('unsubscribe')) {
                        dt.pop_ajax_message('Unsubscribed successfully.', 'success');
                        button.removeClass('unsubscribe');
                        button.children('.subscribe-text').text('Subscribe');
                    } else {
                        dt.pop_ajax_message('You have successfully subscribed to the UPer.', 'success');
                        button.addClass('unsubscribe');
                        button.children('.subscribe-text').text('Subscribed');
                    }
                } else {
                    dt.pop_ajax_message(result.message, 'error');
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });
}

// Modified from http://www.w3schools.com/js/js_cookies.asp
dt.setCookie = function(cname, cvalue, extime) {
    if (extime === 0) {
        document.cookie = cname + "=" + cvalue + ';path=/';
    } else {
        var d = new Date();
        d.setTime(d.getTime() + extime);
        var expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + "; " + expires +';path=/';
    }
}

dt.getCookie = function(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1);
        if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return "";
}

dt.getParameterByName = function(name) {
   var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
   return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
};

Array.prototype.last = function() {
    return this[this.length - 1];
}

dt.LinkedList = function() {
    this.head = null;
    this.tail = null;
    this.length = 0;
}
dt.LinkedList.prototype.push = function(node) {
    // var node = {
    //     data: data,
    //     prev: null,
    //     next: null,
    // }
    if (this.head === null) {
        this.head = node;
        this.tail = node;
    } else {
        this.tail.next = node;
        node.prev = this.tail;
        this.tail = node;
    }
    this.length++;
}
dt.LinkedList.prototype.remove = function(node) {
    if (node.prev !== null) {
        node.prev.next = node.next;
    } else {
        this.head = node.next;
    }
    if (node.next !== null) {
        node.next.prev = node.prev;
    } else {
        this.tail = node.prev;
    }
    this.length--;
}

dt.secondsToTime = function(secs) {
    secs = Math.floor(secs);
    var curTime;
    if (Math.floor(secs/60) < 10) {
        curTime = "0"+Math.floor(secs/60);
    } else {
        curTime = ""+Math.floor(secs/60);
    }
    curTime += ":"+("0"+Math.floor(secs%60)).substr(-2);
    return curTime;
}

dt.millisecondsToTime = function(millisecs) {
    curTime = dt.secondsToTime(millisecs)+"."+("0"+Math.floor(millisecs*100)%100).substr(-2);
    return curTime;
}

dt.dec2hexColor = function(dec_color) {
    return '#'+('000000'+dec_color.toString(16)).substr(-6);
}

dt.escapeHTML = function(unsafe) {
    return unsafe.replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
}

dt.unescapeHTML = function(safe) {
    return safe.replace(/&amp;/g, "&")
                .replace(/&lt;/g, "<")
                .replace(/&gt;/g, ">");
}

var isLoading = {};
var cursors = {};
var isOver = {}
function getParams(params) {
    if (!params) {
        return {key: {}, more: {}}
    } else {
        if (!params.key) {
            params = {key: params, more: {}}
        } else if (!params.more) {
            params.more = {}
        }
        return params;
    }
}

dt.loadNextPage = function(url, params, before_callback, success_callback, failure_callback) {
    params = getParams(params);
    var key = url+'?'+$.param(params.key);
    if (isLoading[key] || isOver[key])
        return;

    isLoading[key] = true;
    if (!cursors[key]) cursors[key] = '';
    before_callback();

    $.ajax({
        type: 'POST',
        url: url,
        data: $.param(params.key)+'&'+$.param({cursor: cursors[key]})+'&'+$.param(params.more),
        success: function(result) {
            cursors[key] = result.cursor;
            isOver[key] = !result.cursor;
            isLoading[key] = false;
            success_callback(result, isOver[key]);
        },
        error: function (xhr, ajaxOptions, thrownError) {
            isLoading[key] = false;
            console.log(xhr.status);
            console.log(thrownError);
            failure_callback(xhr, ajaxOptions, thrownError);
        }
    });
}
dt.setCursor = function(url, params, cursor) {
    params = getParams(params);
    var key = url+'?'+$.param(params.key);
    cursors[key] = cursor;
}
dt.getCursor = function(url, params, cursor) {
    params = getParams(params);
    var key = url+'?'+$.param(params.key);
    return cursors[key];
}
dt.resetLoad = function(url, params) {
    params = getParams(params);
    var key = url+'?'+$.param(params.key);
    isOver[key] = false;
    cursors[key] = '';
}

dt.scrollUpdate = function(url, params, element_class, container, callback, finish_callback, no_data_string, not_use_page_number) {
    function before_callback() {
        container.append('<div class="'+element_class+' loading"></div>');
    }

    function failure_callback() {
        container.children('.'+element_class+'.loading').remove();
    }

    function success_callback(result, isOver) {
        if (isOver) $(window).off('scroll', detectReachBottom);
        container.children('.'+element_class+'.loading').remove();
        var div = callback(result);
        if (div === '') {
            if (container.find('.'+element_class).length === 0) {
                div = '<div class="'+element_class+' none">'
                if (no_data_string) {
                    div += no_data_string
                } else {
                    div += 'No results found.'
                }
                div += '</div>'
                container.append(div);
            }
        } else {
            dt.registerPageCollapse(div, container, not_use_page_number);
            if (finish_callback) finish_callback();
            register_subscribe_button_hover();
            register_subscribe_button_action();
        }
    }

    function detectReachBottom() {
        if ($(window).scrollTop() >= $('.'+element_class+':last-child').offset().top - $(window).height()) {
            dt.loadNextPage(url, params, before_callback, success_callback, failure_callback);
        }
    }
    $(window).scroll(detectReachBottom);
    dt.loadNextPage(url, params, before_callback, success_callback, failure_callback);
}

dt.registerPageCollapse = function(div, container, not_use_page_number) {
    var page = container.children('.pagination-line').length + 1;
    var content_div = div;
    div = '<div class="pagination-line">\
                <div class="page-expand-wrapper">\
                    <div class="page-expand-arrow"></div>\
                </div>\
                <div class="page-number">'
                if (not_use_page_number) {
                    div += 'Collpase'
                } else {
                    div += 'Page '+page
                }
                div += '</div>\
            </div>\
            <div class="page-container">'+content_div+'</div>'
    container.append(div);

    container.children('.page-container:last-child').prev().click(function() {
        var container = $(this).next();
        if (dt.pageStretchProgress[container[0]]) return;

        if ($(this).hasClass('collapse')) {
            dt.pageStretch(container[0], container[0].scrollHeight);
            $(this).removeClass('collapse');
            if (not_use_page_number) $(this).children('.page-number').text('Collapse');
        } else {
            dt.pageStretch(container[0], 0);
            $(this).addClass('collapse');
            if (not_use_page_number) $(this).children('.page-number').text('Expand');
        }
    });
}

dt.pageStretchProgress = {};
dt.pageStretch = function(ele, targetHeight) {
    var actualHeight = ele.offsetHeight;
    var contentHeight = ele.scrollHeight;
    if (targetHeight == actualHeight) return;

    dt.pageStretchProgress[ele] = true;
    var direction = (targetHeight - actualHeight)/Math.abs(targetHeight - actualHeight);
    var lTime = Date.now();
    function stretch() {
        var curTime = Date.now();
        var deltaTime = curTime - lTime;
        lTime = curTime;

        actualHeight += contentHeight*4*deltaTime/1000*direction;
        if ((targetHeight - actualHeight)*direction <= 0) {
            ele.style.height = targetHeight+'px';
            ele.scrollTop = contentHeight;
            dt.pageStretchProgress[ele] = false;
        } else {
            ele.style.height = actualHeight+'px';
            ele.scrollTop = contentHeight;
            requestAnimationFrame(stretch);
        }
    }
    stretch();
}

dt.contentWrapper = function(text) {
    text = text.replace(dt.http_format, function(_, $1, $2) {
        if (!$1) {
            return '<a class="blue-link" target="_blank" href="http://'+$2+'">'+$2+'</a>'
        } else {
            return '<a class="blue-link" target="_blank" href="'+$1+$2+'">'+$1+$2+'</a>'
        }
    });
    // text = text.replace(dt.at_user_format, '<a class="blue-link" target="_blank" href="/user/$1">$2</a>');
    text = text.replace(dt.video_id_format, function(_, $1, $2) {
        if (!$2) {
            return '<a class="blue-link" target="_blank" href="/video/'+$1+'">'+$1+'</a>'
        } else {
            return '<a class="blue-link" target="_blank" href="/video/'+$1+'?index='+$2+'">'+$1+'#'+$2+'</a>'
        }
    });
    text = text.replace(dt.video_time_format, '<span class="blue-link video-timestamp-quick-link" data-minutes="$2" data-seconds="$3">$1</span>');
    return text;
}

var check_watch;
dt.watched_or_not = function() {
    var container = $(this);
    if (container.hasClass('checked')) return;

    check_watch = setTimeout(function() {
        container.addClass('checked');
        var video_id = container.attr('data-id');
        $.ajax({
            type: "POST",
            url: '/video/watched/'+video_id,
            success: function(result) {
                if(!result.error) {
                    if (result.watched) {
                        container.append('<div class="watched-label">Watched</div>')
                    }
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    }, 400);
}
dt.cancel_watched = function() {
    clearTimeout(check_watch);
}

dt.send_report = function(form, type) {
    dt.pop_ajax_message('Reporting...', 'info');
    $.ajax({
      type: "POST",
      url: '/report/'+type+'/'+video_id+'/'+clip_id,
      data: form.serialize(),
      success: function(result) {
        if(result.error) {
            dt.pop_ajax_message(result.message, 'error');
        } else {
            $('#report-'+type+'-textarea').val('');
            dt.pop_ajax_message('We\'ve received your report. Thank you!', 'success');
        }
      },
      error: function (xhr, ajaxOptions, thrownError) {
        console.log(xhr.status);
        console.log(thrownError);
        dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
      }
    });
}

dt.http_format = /(https?:\/\/)?([A-Za-z][A-Za-z0-9_\-]*\.[A-Za-z][A-Za-z0-9_\-]*(?:\.[A-Za-z][A-Za-z0-9_\-]+)?(?:\:[0-9]+)?(?:\/[A-Za-z0-9_\-]+)?)/g;
dt.at_user_format = /\[(.+)(@.+)\]/g;
dt.video_id_format = /(dt\d+)(?:#(\d+))?/g;
dt.video_time_format = /(\[(\d+):(\d{1,2})\])/g;
dt.subtitle_format = /^\[(\d+):(\d{1,2}).(\d{1,2})\](.*)$/;
dt.email_format = /^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
dt.puncts = /[&@.,?!:/\\"'<>=]/;
//end of the file
} (dt, jQuery));
