$(document).ready(function() {
    var message_show = document.getElementById('message-contain-body');
    if (message_show != null) {
        message_show.scrollTop = message_show.scrollHeight;
    }

    $('a.notification-title').click(function(evt) {
        var content = $(evt.target).parent().siblings('div.notification-detail');
        if (content.hasClass('show')) {
            content.height(0);
            content.removeClass('show');
        } else {
            content.height(content[0].scrollHeight);
            content.addClass('show');
        }
    });

    $('div.delete-button').click(function(evt) {
        if ($(evt.target).hasClass('delete')) {
            var id = $(evt.target).attr('data-id');
            $(evt.target).text('Deleting');
            $.ajax({
                type: "POST",
                url: '/account/messages/delete/'+id,
                async: false,
                success: function(result) {
                    console.log(result);
                    if (!result.error) {
                        pop_ajax_message('Message deleted!', 'success');
                        $('#'+id).slideUp(function(){ $(this).remove(); });
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
        }
        $('div.popup-window-container').removeClass('show');
    });

    $('div.message-container').on('click', 'div.message-delete', function(evt) {
        $('div.popup-window-container').addClass('show');
        var id = $(evt.target).attr('data-id');
        var subject = $(evt.target).attr('data-subject');
        $('div.delete-button.delete').attr('data-id', id);
        $('div.delete-message-subject').text(subject);
    });

    var cur_page = 0;
    var message_container = $('.message-container');
    var pagination_container = $('.pagination-line');
    update_page({'page': 1});

    $('div.pagination-line').on('click', 'div', function(evt) {
        var next_page = $(this).attr('data-page');
        if(next_page != cur_page) {
            update_page({'page': next_page});
        }
    });

    function update_page(query) {
        message_container.empty();
        message_container.append('<div class="message-entry loading"></div>');
        $.ajax({
            type: "GET",
            url: '/account/messages',
            data: query,
            success: function(result) {
                if(result.error)
                    pop_ajax_message(result.message, 'error');
                else {
                    message_container.empty();
                    pagination_container.empty();
                    cur_page = result.page;
                    console.log(result.threads.length)
                    if(result.threads.length == 0) {
                        message_container.append('<div class="message-entry none">No messages found.</div>');
                    } else {
                        for(var i = 0; i < result.threads.length; i++) {
                            var message_div = render_message_div(result.threads[i]);
                            message_container.append(message_div);
                        }
                        var pagination = render_pagination(cur_page, result.total_pages);
                        pagination_container.append(pagination);
                    }
                }
            },
            error: function (xhr, ajaxOptions, thrownError) {
                console.log(xhr.status);
                console.log(thrownError);
                pop_ajax_message(xhr.status+' '+thrownError, 'error');
            }
        });
    }
});

render_message_div = function(thread) {
    var div = '<div class="message-entry ';
    if (thread.unread) div += 'unread';
    div += '" id="' + thread.id + '">' +
          '<a href="' + thread.partner.space_url + '" target="_blank" class="user-img">' +
              '<img src="' + thread.partner.avatar_url + '">' +
          '</a>' +
          '<div class="message-info">' +
              '<div class="info-line">' +
                  '<label>About</label>' +
                  '<a class="message-title" href="' + thread.url + '">' + thread.subject + '</a>' +
              '</div>' +
              '<div class="info-line">' +
                  '<label>With</label>' +
                  '<a href="' + thread.partner.space_url + '" target="_blank" class="user-name">' + thread.partner.nickname + '</a>' +
              '</div>' +
              '<div class="info-line">' +
                  '<label>' + thread.updated + ' ';
    if (thread.is_last_sender) div += 'You';
    else div += thread.partner.nickname;
    div += ' said: ' + thread.last_message + '</label>' +
              '</div>' +
              '<div class="message-delete" data-id="' + thread.id + '" data-subject="' + thread.subject + '"></div>' +
          '</div>' +
      '</div>';
    return div;
}