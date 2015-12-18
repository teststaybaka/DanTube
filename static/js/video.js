(function(dt, $) {
var video_id;
var clip_id;

$(document).ready(function() {
	video_id = $('#video-id').val();
	clip_id = $('#clip-id').val();

	$('.intro-content').each(content_collapse_wrapper);
	$('.display-button.intro').click(click_collapse);

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

	$('#like-this').click(function() {
		var button = $(this);
		if (button.hasClass('liked')) {
			$.ajax({
				type: 'POST',
				url: '/video/unlike/'+video_id,
				success: function(result) {
					if (!result.error) {
						button.removeClass('liked');
						button.find('.commas_number').text(parseInt(dt.numberWithCommas(button.find('.commas_number').text()) - 1));
					} else if (result.message) {
						dt.pop_ajax_message(result.message, 'error');
					}
				},
	            error: function (xhr, ajaxOptions, thrownError) {
	                console.log(xhr.status);
	                console.log(thrownError);
	                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
	            }
			});
		} else {
			$.ajax({
				type: 'POST',
				url: '/video/like/'+video_id,
				success: function(result) {
					if (!result.error) {
						button.addClass('liked');
						button.find('.commas_number').text(parseInt(dt.numberWithCommas(button.find('.commas_number').text()) + 1));
					} else if (result.message) {
						dt.pop_ajax_message(result.message, 'error');
					}
				},
	            error: function (xhr, ajaxOptions, thrownError) {
	                console.log(xhr.status);
	                console.log(thrownError);
	                dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
	            }
			});
		}
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
			dt.pop_ajax_message('You can\'t add an empty tag.', 'error');
			error = true;
		} else if (new_tag.length > 100) {
			dt.pop_ajax_message('Tag is too long (less than 100 characters).', 'error');
			error = true;
		} else if (dt.puncts.test(new_tag)) {
			dt.pop_ajax_message('Contain illegal characters.', 'error');
			error = true;
		}

		if (error) {
			return false;
		}

		$('input.add-new-tag-input').focusout();
		$.ajax({
			type: "POST",
			url: '/video/new_tag/'+video_id,
			data: $(evt.target).serialize(),
			success: function(result) {
				if(!result.error) {
					dt.pop_ajax_message('A new tag has been added!', 'success');
					$('input.add-new-tag-input').val('');
				} else {
					$('input.add-new-tag-input').val('');
					dt.pop_ajax_message(result.message, 'error');
				}
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
			}
		});
		return false;
	});

	$('#user-comment-form').submit(function(evt) {
		var button = document.querySelector('#user-comment-form input.inline-button.post');
		button.disabled = true;

		var error = false;
		var content = $('#comment-textarea').val().trim();
		if (!content) {
			dt.pop_ajax_message('You can\'t post empty comment.', 'error');
			error = true;
		} else if (content.length > 2000) {
			dt.pop_ajax_message('Your comment is too long (less than 2000 characters).', 'error');
			error = true;
		}

		if (error) {
			button.disabled = false;
			return false;
		}

		$.ajax({
			type: "POST",
			url: '/video/comment_post/'+video_id,
			data: $(evt.target).serialize(),
			success: function(result) {
				if(!result.error) {
					dt.pop_ajax_message('Comment posted!', 'success');
					$('#comment-textarea').val('');
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

	$('#user-reply-form').submit(function(evt) {
		var button = document.querySelector('#user-reply-form input.inline-button.post');
		button.disabled = true;

		var error = false;
		var content = $('#reply-textarea').val().trim();
		if (!content) {
			dt.pop_ajax_message('You can\'t post empty comment.', 'error');
			error = true;
		} else if (content.length > 2000) {
			dt.pop_ajax_message('Your comment is too long (less than 2000 characters).', 'error');
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
			url: '/video/reply_post/'+video_id,
			data: $(evt.target).serialize(),
			success: function(result) {
				if(!result.error) {
					dt.pop_ajax_message('Reply posted!', 'success');
					$('#reply-textarea').val('');
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
	
	var comment_id = dt.getParameterByName('comment');
	var inner_comment_id = dt.getParameterByName('reply');

	function detectLoadComment() {
		if ($(window).scrollTop() < $('#comments-list-container').offset().top - 30  - $(window).height()) return;
		$(window).off('scroll', detectLoadComment);

		dt.scrollUpdate('/video/comment/'+video_id, {comment_id: comment_id}, 'comment-entry', $('#comments-list-container'),function(result) {
			var div = '';
			for (var i = 0; i < result.comments.length; i++) {
				div += render_comment_div(result.comments[i]);
			}
			return div;
		}, function() {
			$('#comments-list-container').children('.page-container:last-child').find('.comment-content').each(content_collapse_wrapper);
		}, 'Be the first one to comment!', true);
	}
	if (comment_id) {
		$.ajax({
			type: 'POST',
			url: '/video/check_comment/'+video_id,
			data: {comment_id: comment_id, inner_comment_id: inner_comment_id},
			success: function(result) {
				if(!result.error) {
					var div = render_comment_div(result.comment);
					$('#comments-list-container').prepend(div);
					$('.comment-entry.none').remove();
					$('#comments-list-container').children('.comment-entry:first-child').find('.comment-content').each(content_collapse_wrapper);
					$(window).scroll(detectLoadComment);
					$(window).scrollTop($('#comments-list-container').children('.comment-entry:first-child').offset().top);
				} else {
					dt.pop_ajax_message(result.message, 'error');
				}
			},
			error: function (xhr, ajaxOptions, thrownError) {
				console.log(xhr.status);
				console.log(thrownError);
				dt.pop_ajax_message(xhr.status+' '+thrownError, 'error');
			}
		})
	} else {
		$(window).scroll(detectLoadComment);
	}

	$('#comments-list-container').on('click', '.display-button.replies', function() {
		var button = $(this);
		var total_num = button.attr('data-num');
		var cursor = button.attr('data-cursor');
		var button_line = button.parent();
		var inner_comment_container = button_line.parent();
		var url = '/video/inner_comment/'+video_id;
		var comment_id = inner_comment_container.parent().attr('data-id');
		var params = {comment_id: comment_id};
		dt.setCursor(url, params)
		dt.loadNextPage(url, params, function() {
			button_line.remove();
			inner_comment_container.append('<div class="comment-entry loading"></div>');
		}, function(result, isOver) {
			if (!cursor) inner_comment_container.find('.comment-entry.inner').remove();
			inner_comment_container.children('.comment-entry.loading').remove();

			var div = '';
			for (var i = 0; i < result.inner_comments.length; i++) {
				div += render_inner_comment_div(result.inner_comments[i]);
			}
			dt.registerPageCollapse(div, inner_comment_container, true);

			cursor = dt.getCursor(url, params);
			if (!isOver) inner_comment_container.append('<div class="display-button-line replies"><span class="display-button replies" data-num="'+total_num+'" data-cursor="'+cursor+'">View more replies (' + (total_num - inner_comment_container.find('.comment-entry.inner').length) + ')</span></div>')

			inner_comment_container.children('.page-container:last-child').find('.comment-content').each(content_collapse_wrapper);
		}, function() {
			inner_comment_container.children('.comment-entry.loading').remove();
			inner_comment_container.append('<div class="display-button-line replies"><span class="display-button replies" data-num="'+total_num+'" data-cursor="'+cursor+'">View more replies (' + (total_num - inner_comment_container.find('.comment-entry.inner').length) + ')</span></div>')
		});
	});
	
	$('#comments-list-container').on('click', 'span.video-timestamp-quick-link', function() {
		var minutes = parseInt($(this).attr('data-minutes'));
		var seconds = parseInt($(this).attr('data-seconds'));
		player_seek(minutes*60 + seconds);
		player.playVideo();
	});
	$('#comments-list-container').on('click', 'div.display-button.comment', click_collapse);
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
		$('#reply-textarea').val('@' + user_name + ': ').focus();
	});

	$('#report-video-button').click(function() {
		$('#report-video-form').removeClass('hidden');
		$('#report-video-textarea').focus();
	});
	$('#report-video-form').submit(function(evt) {
		dt.send_report($(this), 'video');
		return false;
	});

	$('#comments-list-container').on('click', 'div.comment-operation.report', function() {
		var comment_box = $(this).parent().parent();
		var comment_entry = comment_box.parent();
		if (comment_entry.hasClass('inner')) {
			$('#report-comment-is-inner').val('on');
			$('#report-comment-inner-id').val(comment_entry.attr('data-id'));
			var parent_entry = comment_entry.parent().parent();
			$('#report-comment-id').val(parent_entry.attr('data-id'));
		} else {
			$('#report-comment-is-inner').val('');
			$('#report-comment-id').val(comment_entry.attr('data-id'));
		}
		var offset = $(this).offset();
		var form = $('#report-comment-form')[0];
		form.style.left = offset.left+'px';
		form.style.top = offset.top - $(this).height()+'px';
		$('#report-comment-form').removeClass('hidden');
		$('#report-comment-textarea').focus();
	});
	$('#report-comment-form').submit(function(evt) {
		dt.send_report($(this), 'comment');
		return false;
	});

	$('#list-scroll-bar').each(function() {
		var playlist_id = $(this).attr('data-id');
		var playlist_type = $(this).attr('data-type');
		if ($(this).attr('data-cursor-next')) {
			dt.setCursor('/video/list/'+playlist_id, {type: 'next', playlist_type: playlist_type}, $(this).attr('data-cursor-next'));
			$('#list-scroll-bar').scroll(detectLoadMorePlaylist);
		}
		if ($(this).attr('data-cursor-prev')) {
			dt.setCursor('/video/list/'+playlist_id, {type: 'prev', playlist_type: playlist_type}, $(this).attr('data-cursor-prev'));
			$('#list-scroll-bar').prepend('<a class="list-entry cursor prev">Load previous</a>')
			$('.list-entry.cursor.prev').click(loadPrevPlaylist);
		}
	});

	$('iframe#video-player').load(function() {
		console.log('iframe loaded')
		var subintro = $('iframe#video-player').contents().find('#clip-subintro').val();
		$('.intro-box.sub').empty();
		if (subintro) {
			$('.intro-box.sub').append('<div class="intro-content">'+subintro+'</div>\
										<div class="display-button intro"><span class="display-text">SHOW MORE</span><span class="display-arrow"></span></div>')
			$('.intro-box.sub .intro-content').each(content_collapse_wrapper);
			$('.intro-box.sub .display-button.intro').click(click_collapse);
		}

		$(document).on('wide', function() {
			$('body').removeClass('pagewide')
					.addClass('wide');
		});
		$(document).on('pagewide', function() {
			$('body').removeClass('wide')
					.addClass('pagewide');
		});
		$(document).on('restore', function() {
			$('body').removeClass('wide')
					.removeClass('pagewide');
		})
	});
});

function render_comment_div(comment) {
	var div = '<div class="comment-entry" data-id="' + comment.id + '">\
      <a href="' + comment.creator.space_url + '" target="_blank">\
        <img class="comment-img" src="' + comment.creator.avatar_url_small + '">\
      </a>\
      <div class="comment-detail-box">\
        <div class="user-title-line">'
        	if (comment.floorth) {
        		div += '<label class="floorth">#'+ comment.floorth +'</label>'
        	}
			div += '<a class="blue-link user-name" href="' + comment.creator.space_url + '" target="_blank">' + comment.creator.nickname + '</a>\
			<label class="comment-time">' + comment.created + '</label>\
        </div>\
        <div class="comment-content">' + comment.content + '</div>\
        <div class="display-button comment"><span class="display-text">Read more</span><span class="display-arrow"></span></div>\
        <div class="comment-operation-line">\
			<div class="comment-operation reply">Reply</div>\
			<div class="comment-operation report">Report</div>\
        </div>\
      </div>\
      <div class="inner-comment-container">'
    if (comment.inner_comments.length != 0) {
    	for (var i = 0; i < comment.inner_comments.length; i++) {
	        div += render_inner_comment_div(comment.inner_comments[i])
        }
        if (comment.inner_comment_counter > 3) {
    		div += '<div class="display-button-line replies"><span class="display-button replies" data-num="'+comment.inner_comment_counter+'" data-cursor="">View more replies (' + (comment.inner_comment_counter - 3) + ')</span></div>'
    	}
    }
    div += '</div>\
    	</div>'
    return div;
}

function render_inner_comment_div(inner_comment) {
	var div = '<div class="comment-entry inner" data-id="' + inner_comment.id + '">\
					<a href="' + inner_comment.creator.space_url + '" target="_blank">\
			          <img class="comment-img" src="' + inner_comment.creator.avatar_url_small + '">\
			        </a>\
			        <div class="comment-detail-box inner">\
			        	<div class="user-title-line">\
			              <a class="blue-link user-name" href="' + inner_comment.creator.space_url + '" target="_blank">' + inner_comment.creator.nickname + '</a>\
			              <label class="comment-time">' + inner_comment.created + '</label>\
			            </div>\
			            <div class="comment-content">' + inner_comment.content + '</div>\
			            <div class="display-button comment"><span class="display-text">Read more</span><span class="display-arrow"></span></div>\
						<div class="comment-operation-line">\
				          <div class="comment-operation reply">Reply</div>\
				          <div class="comment-operation report">Report</div>\
				        </div>\
			        </div>\
		        </div>'
	return div;
}

function loadPrevPlaylist() {
	var playlist_id = $('#list-scroll-bar').attr('data-id');
	dt.loadNextPage('/video/list/'+playlist_id, {type: 'prev'}, function() {
		$('.list-entry.cursor.prev').remove();
		$('#list-scroll-bar').prepend('<a class="list-entry prev loading"></a>')
	}, function(result, isOver) {
		$('.list-entry.prev.loading').remove();

		var div = '';
		for (var i = 0; i < result.videos.length; i++) {
			div += render_playlist_video(result.videos[i]);
		}
		$('#list-scroll-bar').prepend(div);

		if (!isOver) {
			$('#list-scroll-bar').prepend('<a class="list-entry cursor prev">Load previous</a>')
			$('.list-entry.cursor.prev').click(loadPrevPlaylist);
		}
	}, function() {
		$('.list-entry.prev.loading').remove();
	});
}

function detectLoadMorePlaylist() {
	function loadMorePlaylist() {
		var playlist_id = $('#list-scroll-bar').attr('data-id');
		dt.loadNextPage('/video/list/'+playlist_id, {type: 'next'}, function() {
			$('#list-scroll-bar').append('<a class="list-entry more loading"></a>')
		}, function(result, isOver) {
			$('.list-entry.more.loading').remove();
			if (isOver) $('#list-scroll-bar').off('scroll', detectLoadMorePlaylist);

			var div = '';
			for (var i = 0; i < result.videos.length; i++) {
				div += render_playlist_video(result.videos[i]);
			}
			$('#list-scroll-bar').append(div);
		}, function() {
			$('.list-entry.more.loading').remove();
		});
	}

	if ($('.list-entry:last-child').offset().top - $('#list-scroll-bar').offset().top < $('#list-scroll-bar').height()) {
		loadMorePlaylist();
	}
}

function render_playlist_video(video) {
	var div = '<a class="list-entry" href="'+video.url+'">\
			        <div class="list-entry-index">'+(video.index+1)+'</div>\
			        <img class="list-video-img" src="'+video.thumbnail_url+'">\
			        <div class="list-entry-info">\
			          	<div class="list-video-title">'+video.title+'</div>\
			          	<div>\
			            	<div class="list-video-statistic hits"><span class="statistic-icon views"></span>'+dt.numberWithCommas(video.hits)+'</div>\
			            	<div class="list-video-statistic comments"><span class="statistic-icon comment"></span>'+dt.numberWithCommas(video.comment_counter)+'</div>\
			          	</div>\
			        </div>\
			    </a>'
	return div;
}

function content_collapse_wrapper() {
	var content_div = $(this)[0];
	if (content_div.scrollHeight > 48) {
		content_div.style.height = '48px';
	} else {
		$(this).next().remove();
	}
	$(this).html(dt.contentWrapper($(this).html()));
}

function click_collapse() {
	var comment_div = $(this).prev()[0];
	if ($(this).hasClass('less')) {
		comment_div.style.height = '48px';
		$(this).removeClass('less');
		if ($(this).hasClass('comment')) {
			$(this).children('span.display-text').text('Read more');
		}  else {
			$(this).children('span.display-text').text('SHOW MORE');
		}
	} else {
		comment_div.style.height = comment_div.scrollHeight + 'px';
		$(this).addClass('less');
		if ($(this).hasClass('comment')) {
			$(this).children('span.display-text').text('Read less');
		} else {
			$(this).children('span.display-text').text('SHOW LESS');
		}
	}
}
//end of the file
} (dt, jQuery));