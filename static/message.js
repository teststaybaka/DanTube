(function(dt, $) {
$(document).ready(function() {
    $('#action-select div.option-entry.delete').click(function() {
        dt.delete_entries('/account/messages/delete');
    });
    $('div.messages-container').on('click', '.message-select-checkbox', function(evt) {
        $(this).toggleClass('checked');
    });

    dt.scrollUpdateMessage('/account/messages', render_message_div);
});

function render_message_div(thread) {
    var div = '<div class="message-entry ';
    if (thread.unread) div += 'unread';
    div += '" data-id="' + thread.id + '"> \
          <a href="' + thread.partner.space_url + '" target="_blank" class="user-img"> \
              <img src="' + thread.partner.avatar_url + '"> \
          </a> \
          <div class="message-info">\
              <div class="info-line">\
                  <label>About</label>\
                  <a class="message-title" href="' + thread.url + '">' + thread.subject + '</a>\
              </div>\
              <div class="info-line">\
                  <label>With</label>\
                  <a href="' + thread.partner.space_url + '" target="_blank" class="user-name blue-link">' + thread.partner.nickname + '</a>\
              </div>\
              <div class="info-line">\
                  <label>'
    if (thread.is_sender) div += 'You';
    else div += 'He'
    div += ' said: ' + thread.last_message + '</label>\
                  <label> '+thread.updated+'</label>\
              </div>\
          </div>\
          <div class="message-select-checkbox" data-id="' + thread.id + '"></div>\
      </div>'
    return div;
}
//end of the file
} (dt, jQuery));
