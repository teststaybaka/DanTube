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

$(document).ready(function() {
    if ($('#portrait').length != 0) {
        var uesr_id = $('#portrait').attr('data-id');
        var cookie = dt.getCookie(uesr_id+'_check');
        if (!cookie) {
            var now = new Date().toUTCString();
            var extime = 10 * 60 *1000; // 10 mins wait
            dt.setCookie(uesr_id+'_check', now, extime);
            count_new_mentions();
            count_new_notifications();
            count_new_subscriptions();
        }
        var num = dt.getCookie('new_notifications');
        $('#user-notification-new-num').text(num);
        num = dt.getCookie('new_mentions');
        $('#user-at-new-num').text(num);
        num = dt.getCookie('new_subscriptions');
        $('#user-subscriptions-new-num').text(num);
    }

    $('#portrait').mouseover(function() {
        $('#user-box').addClass('show');
        $('#user-box').removeClass('hide');
        clearTimeout(window.user_box_hide);
        clearTimeout(window.user_box_clear);
    });

    $('#portrait').mouseout(function() {
        window.user_box_hide = setTimeout(function() {
            $('#user-box').addClass('hide');
            window.user_box_clear = setTimeout(function() {
                $('#user-box').removeClass('show');
            }, 100);
        }, 100);
    });

    $('.subscribe-button').hover(
        function() {
            if ($(this).hasClass('unsubscribe')) {
                $(this).children('.subscribe-text').text('Unsubscribe');
            }
        }, 
        function() {
            if ($(this).hasClass('unsubscribe')) {
                $(this).children('.subscribe-text').text('Subscribed');
            }
        }
    );
    $('.subscribe-button').click(function(evt) {
        var button = $(this);
        var uploader_id = button.attr('data-id');
        var action = ''
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
                    if (result.change) {
                        if (button.hasClass('unsubscribe')) {
                            button.removeClass('unsubscribe');
                            button.children('.subscribe-text').text('Subscribe');
                        } else {
                            button.addClass('unsubscribe');
                            button.children('.subscribe-text').text('Subscribed');
                        }
                    }
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    });

    $('span.commas_number').each(function() {
        $(this).text(dt.numberWithCommas($(this).text()) )
    });

    $('div.emoticons-select').append('<div class="emoticons-menu container">\
                <div class="emoticons-option">(⌒▽⌒)</div>\
                <div class="emoticons-option">（￣▽￣）</div>\
                <div class="emoticons-option">(=・ω・=)</div>\
                <div class="emoticons-option">(｀・ω・´)</div>\
                <div class="emoticons-option">(〜￣△￣)〜</div>\
                <div class="emoticons-option">(･∀･)</div>\
                <div class="emoticons-option">(°∀°)ﾉ</div>\
                <div class="emoticons-option">(￣3￣)</div>\
                <div class="emoticons-option">╮(￣▽￣)╭</div>\
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
                <div class="emoticons-option">(´；ω；`)</div>\
                <div class="emoticons-option">（/TДT)/</div>\
                <div class="emoticons-option">(^・ω・^ )</div>\
                <div class="emoticons-option">(｡･ω･｡)</div>\
                <div class="emoticons-option">(●￣(ｴ)￣●)</div>\
                <div class="emoticons-option">ε=ε=(ノ≧∇≦)ノ</div>\
                <div class="emoticons-option">(´･_･`)</div>\
                <div class="emoticons-option">(-_-#)</div>\
                <div class="emoticons-option">（￣へ￣）</div>\
                <div class="emoticons-option">(￣ε(#￣) Σ</div>\
                <div class="emoticons-option">ヽ(`Д´)ﾉ</div>\
                <div class="emoticons-option">(╯°口°)╯(┴—┴</div>\
                <div class="emoticons-option">（#-_-)┯━┯</div>\
                <div class="emoticons-option">_(:3」∠)_</div>\
                <div class="emoticons-option">T_T</div>\
                <div class="emoticons-option">OTL</div>\
            </div>\
            <div class="emoticons-label">Emoticons</div>');
    $('div.emoticons-select').click(function() {
        if ($(this).hasClass('show')) {
            $(this).removeClass('show');
        } else {
            $(this).addClass('show')
        }
    });
    $('div.emoticons-option').click(function(evt) {
        var textarea = $(evt.target).parent().parent().parent().prev();
        textarea.val(textarea.val() + $(evt.target).text());
    });

    $('label.check-label input[type="checkbox"]').change(function(evt) {
        if ($(this).is(':checked')) {
            $(this).prev().addClass('checked');
        } else {
            $(this).prev().removeClass('checked');
        }
    });

    $('.checkbox-selection').click(function() {
        if ($(this).hasClass('off')) {
            $(this).removeClass('off');
            $(this).addClass('on');
        } else {
            $(this).addClass('off');
            $(this).removeClass('on');
        }
    });
});

dt.render_pagination = function(cur_page, total_pages) {
    var page_range = 10;
    cur_page = parseInt(cur_page);
    var max_page;
    var min_page;
    if (cur_page > total_pages) {
        max_page = total_pages;
        min_page = Math.min(max_page - page_range + 1, 1);
    } else if (cur_page < 1) {
        min_page = 1;
        max_page = Math.max(min_page + page_range - 1, total_pages);
    } else {
        max_page = Math.min(cur_page + 4, total_pages);
        min_page = Math.max(cur_page - 5, 1);
        var remain_page = page_range - (max_page - cur_page) - (cur_page - min_page) - 1;

        if (remain_page > 0) {
            max_page = Math.min(max_page + remain_page, total_pages);
            min_page = Math.max(min_page - remain_page, 1);
        }
    }
    
    var pagination = "";
    if(cur_page > 1) {
        pagination += '<a class="page-change" data-page="' + 1 + '"><<</a>';
        pagination += '<a class="page-change" data-page="' + (cur_page - 1) + '"><</a>';
    }
    for(var i = min_page; i <= max_page; i++) {
        if(i == cur_page) {
            pagination += '<a class="page-num active" data-page="' + i + '">' + i + '</a>';
        } else {
            pagination += '<a class="page-num" data-page="' + i + '">' + i + '</a>';
        }
    }
    if(cur_page < total_pages) {
        pagination += '<a class="page-change" data-page="' + (cur_page + 1) + '">></a>';
        pagination += '<a class="page-change" data-page="' + total_pages + '">>></a>';
    }
    return pagination;
}

function count_new_subscriptions() {
    $.ajax({
        type: "POST",
        url: '/user/new_subscriptions',
        success: function(result) {
            if(!result.error) {
                if (result.count > 99) {
                    dt.setCookie('new_subscriptions', '99+');
                    $('#user-subscriptions-new-num').text('99+');
                } else if (result.count == 0) {
                    dt.setCookie('new_subscriptions', '');
                    $('#user-subscriptions-new-num').text('');
                } else {
                    dt.setCookie('new_subscriptions', result.count);
                    $('#user-subscriptions-new-num').text(result.count);
                }
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

function count_new_mentions() {
    $.ajax({
        type: "POST",
        url: '/user/new_mentions',
        success: function(result) {
            if(!result.error) {
                if (result.count > 99) {
                    dt.setCookie('new_mentions', '99+');
                    $('#user-at-new-num').text('99+');
                } else if (result.count == 0) {
                    dt.setCookie('new_mentions', '');
                    $('#user-at-new-num').text('');
                } else {
                    dt.setCookie('new_mentions', result.count);
                    $('#user-at-new-num').text(result.count);
                }
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

function count_new_notifications() {
    $.ajax({
        type: "POST",
        url: '/user/new_notifications',
        success: function(result) {
            if(!result.error) {
                if (result.count > 99) {
                    dt.setCookie('new_notifications', '99+');
                    $('#user-notification-new-num').text('99+');
                } else if (result.count == 0) {
                    dt.setCookie('new_notifications', '');
                    $('#user-notification-new-num').text('');
                } else {
                    dt.setCookie('new_notifications', result.count);
                    $('#user-notification-new-num').text(result.count);
                }
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

// Modified from http://www.w3schools.com/js/js_cookies.asp
dt.setCookie = function(cname, cvalue, extime) {
    if (extime == 0) {
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
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
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
//end of the file
} (dt, jQuery));
