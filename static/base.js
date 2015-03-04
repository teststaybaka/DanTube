function quick_sort(array, start, end, compare) {
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

        quick_sort(array, start, storeIndex - 1, compare);
        quick_sort(array, storeIndex + 1, end, compare);
    }
}

function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

function hsl2rgb(hsl) {
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

function pop_ajax_message(content, type) {
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

    $('span.commas_number').each(function() {
        $(this).text(numberWithCommas($(this).text()) )
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
});

function get_video_list(url, query, callback) {
    $.ajax({
        type: "GET",
        url: url,
        data: query,
        success: function(result) {
            if (callback && typeof(callback) === "function") {
                if(result.error)
                    callback(result, []);
                else
                    callback(null, result);
            }
            else
                return result;
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
            var err = {'error': true, 'message': thrownError};
            if (callback && typeof(callback) === "function")
                callback(err, []);
            else
                return err;
        }
    });
}

render_pagination = function(cur_page, total_pages) {
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
