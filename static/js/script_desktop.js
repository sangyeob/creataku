$(document).ready(function() {
	$.fn.shake = function (options) {
        // defaults
        var settings = {
            'shakes': 2,
            'distance': 10,
            'duration': 200
        };
        // merge options
        if (options) {
            $.extend(settings, options);
        }
        // make it so
        var pos;
        return this.each(function () {
            $this = $(this);
            // position if necessary
            pos = $this.css('position');
            if (!pos || pos === 'static') {
                $this.css('position', 'relative');
            }
            // shake it
            for (var x = 1; x <= settings.shakes; x++) {
                $this.animate({ left: settings.distance * -1 }, (settings.duration / settings.shakes) / 4)
                    .animate({ left: settings.distance }, (settings.duration / settings.shakes) / 2)
                    .animate({ left: 0 }, (settings.duration / settings.shakes) / 4);
            }
        });
    };

    $('section.page1 div.button1').click(function() {
    	var $wrapper = $('div.sectionWrapper');
		$wrapper.addClass('blockEvent');
		var currentPage = 6;
		$wrapper.attr('data-current-page', currentPage)
		for(var i = 1; i <= 6; i ++) {
			$wrapper.removeClass('currentPage' + i);
		}
		$wrapper.addClass('currentPage' + currentPage);

		setTimeout(function() {
			$('div.sectionWrapper').removeClass('blockEvent');
		}, 1500);
    });

    $('section.page1 div.button2').click(function() {
    	var $wrapper = $('div.sectionWrapper');
		$wrapper.addClass('blockEvent');
		var currentPage = 5;
		$wrapper.attr('data-current-page', currentPage)
		for(var i = 1; i <= 6; i ++) {
			$wrapper.removeClass('currentPage' + i);
		}
		$wrapper.addClass('currentPage' + currentPage);

		setTimeout(function() {
			$('div.sectionWrapper').removeClass('blockEvent');
		}, 1500);
    });

	$('div.logo').click(function() {
		var $wrapper = $('div.sectionWrapper');
		$wrapper.addClass('blockEvent');
		var currentPage = 1;
		$wrapper.attr('data-current-page', currentPage)
		for(var i = 1; i <= 6; i ++) {
			$wrapper.removeClass('currentPage' + i);
		}
		$wrapper.addClass('currentPage' + currentPage);

		setTimeout(function() {
			$('div.sectionWrapper').removeClass('blockEvent');
		}, 1500);
	});
	$('nav.dotnav li').click(function() {
		var $wrapper = $('div.sectionWrapper');
		$wrapper.addClass('blockEvent');
		var currentPage = +$(this).attr('data-page-number');
		$wrapper.attr('data-current-page', currentPage)
		for(var i = 1; i <= 6; i ++) {
			$wrapper.removeClass('currentPage' + i);
		}
		$wrapper.addClass('currentPage' + currentPage);

		setTimeout(function() {
			$('div.sectionWrapper').removeClass('blockEvent');
		}, 1500);
	});
	$('div.sectionWrapper').bind('mousewheel DOMMouseScroll', function(e) {
		if($(this).hasClass('blockEvent')) return false;
		var currentPage = +$(this).attr('data-current-page');
		if(e.originalEvent.wheelDelta > 20 || e.originalEvent.detail < 0) {
			// scrolling up	
			if(currentPage == 1) return false;
			currentPage -= 1;
			
		} else if (e.originalEvent.wheelDelta < -20 || e.originalEvent.detail > 0) {
			// scrolling down
			if(currentPage == 6) return false;
			currentPage += 1;
		}
		else { return false; }
		$(this).addClass('blockEvent');
		$(this).attr('data-current-page', currentPage);
		for(var i = 1; i <= 6; i ++) {
			$(this).removeClass('currentPage' + i);
		}
		$(this).addClass('currentPage' + currentPage);

		setTimeout(function() {
			$('div.sectionWrapper').removeClass('blockEvent');
		}, 1500);
	});

	$('section.page5 div.submit').click(function() {
		if($(this).parents('article').hasClass('form_collector')) {
			var flag = false;
			if($('section.page5 article.form_collector input.field').val().trim() == "") {
				$('section.page5 article.form_collector input.field').shake();
				$('section.page5 article.form_collector input.field').focus();
				flag = true;
			}
			if($('section.page5 article.form_collector input.email').val().trim() == "") {
				$('section.page5 article.form_collector input.email').shake();
				$('section.page5 article.form_collector input.email').focus();
				flag = true;
			}
			if($('section.page5 article.form_collector input.name').val().trim() == "") {
				$('section.page5 article.form_collector input.name').shake();
				$('section.page5 article.form_collector input.name').focus();
				flag = true;
			}
			if(flag) return false;
			$('section.page5 article.form_collector').addClass('finishing');
			$.ajax({
				url: '/register_collector/',
				contentType: 'application/json;chatset=UTF-8',
				method: 'POST',
				data: JSON.stringify({
					name: $('section.page5 article.form_collector input.name').val().trim(),
					email: $('section.page5 article.form_collector input.email').val().trim(),
					field: $('section.page5 article.form_collector input.field').val().trim(),
				}),
				success: function(data, status, jqxhr) {
					$('section.page5 article.form_collector').removeClass('finishing');
					$('section.page5 article.form_collector').addClass('finished');
				},
				error: function(req, st, error) {
					$('section.page5 article.form_collector').removeClass('finishing');
					alert('에러가 발생했습니다. 잠시 후 다시 시도해주세요.');
				} 
			});
		} else {
			var flag = false;
			if($('section.page5 article.form_creator input.email').val().trim() == "") {
				$('section.page5 article.form_creator input.email').shake();
				$('section.page5 article.form_creator input.email').focus();
				flag = true;
			}
			if($('section.page5 article.form_creator input.mobile').val().trim() == "") {
				$('section.page5 article.form_creator input.mobile').shake();
				$('section.page5 article.form_creator input.mobile').focus();
				flag = true;
			}
			if($('section.page5 article.form_creator input.field').val().trim() == "") {
				$('section.page5 article.form_creator input.field').shake();
				$('section.page5 article.form_creator input.field').focus();
				flag = true;
			}
			if($('section.page5 article.form_creator input.nickname').val().trim() == "") {
				$('section.page5 article.form_creator input.nickname').shake();
				$('section.page5 article.form_creator input.nickname').focus();
				flag = true;
			}
			if($('section.page5 article.form_creator input.name').val().trim() == "") {
				$('section.page5 article.form_creator input.name').shake();
				$('section.page5 article.form_creator input.name').focus();
				flag = true;
			}
			if(flag) return false;
			$('section.page5 article.form_creator').addClass('finishing');
			$.ajax({
				url: '/register_creator/',
				contentType: 'application/json;chatset=UTF-8',
				method: 'POST',
				data: JSON.stringify({
					name: $('section.page5 article.form_creator input.name').val().trim(),
					email: $('section.page5 article.form_creator input.email').val().trim(),
					field: $('section.page5 article.form_creator input.field').val().trim(),
					nickname: $('section.page5 article.form_creator input.nickname').val().trim(),
					mobile: $('section.page5 article.form_creator input.mobile').val().trim(),
				}),
				success: function(data, status, jqxhr) {
					$('section.page5 article.form_creator').removeClass('finishing');
					$('section.page5 article.form_creator').addClass('finished');
				},
				error: function(req, st, error) {
					$('section.page5 article.form_creator').removeClass('finishing');
					alert('에러가 발생했습니다. 잠시 후 다시 시도해주세요.');
				} 
			});
		}
	});
	$('section.page6 div.inputwrapper input').bind('change', function() {
		$('section.page6 div.inputwrapper').addClass('selected');
	});
	$('section.page6 div.submit').click(function() {
		var flag = false;
		if($('section.page6 textarea').val().trim() == "") {
			$('section.page6 textarea').shake();
			$('section.page6 textarea').focus();
			flag = true;
		}
		if($('section.page6 input.email').val().trim() == "") {
			$('section.page6 input.email').shake();
			$('section.page6 input.email').focus();
			flag = true;
		}
		if($('section.page6 input.name').val().trim() == "") {
			$('section.page6 input.name').shake();
			$('section.page6 input.name').focus();
			flag = true;
		}
		if(flag) return false;
		$('section.page6 div.form_request').addClass('finishing');
		var fd = new FormData($('section.page6 form')[0]);
		console.log(fd);

		$.ajax({
	        url: '/request/',
	        type: 'POST',
	        data: fd,
	        async: true,
	        success: function (data) {
	            $('section.page6 div.form_request').removeClass('finishing');
	            $('section.page6 div.form_request').addClass('finished');
	        },
	        cache: false,
	        contentType: false,
	        processData: false
	    });

	});
});