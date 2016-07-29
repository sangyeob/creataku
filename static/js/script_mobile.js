$(document).ready(function() {
	$('div.btn1').click(function() {
		$('.realbody').animate({scrollTop: parseInt($('.realbody').prop('scrollHeight') * 0.6232)}, 500);
	});
	$('div.btn2').click(function() {
		window.open('/mobile/request_form/');
	});
	$('div.btn3').click(function() {
		window.open('/mobile/register_collector_form/');
	});
	$('div.btn4').click(function() {
		window.open('/mobile/register_creator_form/');
	});
	$('div.btn5').click(function() {
		window.open('/mobile/request_form/');
	});
});