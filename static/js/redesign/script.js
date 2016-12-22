$(document).ready(function() {
	$('div.popup_background').click(function() {
		$(this).css('display', 'none');
	});

	$('div.popup_background div.popup_contents').click(function(e) {
		e.stopPropagation();
	});

	$('header a.login').click(function() {
		$('div.pop_login').css('display', 'table');
		return false;
	});
	if($bidend - $timenow > 0) {
		$d = $('header .remaining_time .day');
		$h = $('header .remaining_time .hour');
		$m = $('header .remaining_time .minute');
		$s = $('header .remaining_time .second');
		$pageload = new Date();
		reloadFlag = false;
		function updateTime(ms) {
			var s = parseInt(ms / 1000);
			var d = parseInt(s / 86400);
			s -= d * 86400;
			var h = parseInt(s / 3600);
			s -= h * 3600;
			var m = parseInt(s / 60);
			s -= m * 60;

			$d.text(((d < 10) ? '0' : '') + d.toString());
			$h.text(((h < 10) ? '0' : '') + h.toString());
			$m.text(((m < 10) ? '0' : '') + m.toString());
			$s.text(((s < 10) ? '0' : '') + s.toString());
		}
		updateTime($bidend - $timenow);

		setInterval(function() {
			$start = $bidend - $timenow;
			$elapsed = new Date() - $pageload;
			$now = $start - $elapsed;
			if($now < 0) {
				location.reload();
			} else {
				updateTime($now);
			}
		}, 300);
	} else {
		$('header .remaining_time').html('CLOSED');
		$('.remaining_time_label').addClass('disp-none');
	}
});
