/*!
 * Start Bootstrap - Handu
 * Copyright 2013-2016 Start Bootstrap
 * Licensed under MIT (https://github.com/BlackrockDigital/startbootstrap/blob/gh-pages/LICENSE)
 */
$(function() {
    $('#side-menu').metisMenu();
});

//Loads the correct sidebar on window load,
//collapses the sidebar on window resize.
// Sets the min-height of #page-wrapper to window size
$(function() {
    $(window).bind("load resize", function() {
        var topOffset = 50;
        var width = (this.window.innerWidth > 0) ? this.window.innerWidth : this.screen.width;
        if (width < 768) {
            $('div.navbar-collapse').addClass('collapse');
            topOffset = 100; // 2-row-menu
        } else {
            $('div.navbar-collapse').removeClass('collapse');
        }

        var height = ((this.window.innerHeight > 0) ? this.window.innerHeight : this.screen.height) - 1;
        height = height - topOffset;
        if (height < 1) height = 1;
        if (height > topOffset) {
            $("#page-wrapper").css("min-height", (height) + "px");
        }
    });

    var url = window.location;
    // var element = $('ul.nav a').filter(function() {
    //     return this.href == url;
    // }).addClass('active').parent().parent().addClass('in').parent();
    var element = $('ul.nav a').filter(function() {
        return this.href == url;
    }).addClass('active').parent();

    while (true) {
        if (element.is('li')) {
            element = element.parent().addClass('in').parent();
        } else {
            break;
        }
    }
});
$("#userModal").on("hidden.bs.modal", function() {
	    $("#password").val("");
    	$("#confirmpass").val("");
    	$("div.form-group span").remove()
	});
$("#userinfo").click(function(){
	  	  $.ajax(
				 {type: "POST",
			       url: "/hd_mesos/userinfo",
			       success: function(data){
			    	   var obj = eval('(' + data + ')');
			    	   $("#username").val(obj.username);
			    	   $("#nickname").val(obj.nickname);
			       }
					});
	    });
$("#useredit").validate({
	onfocusout: function(element) { $(element).valid(); },
	errorElement:'span',
	submitHandler:function(){
          ajaxSubmitForm();
      },
});
function ajaxSubmitForm() {
	 
	  $.ajax(
			{type: "POST",
			  url: "/hd_mesos/useredit",
		      data: {
		        	"Username":$('#username').val(),
		        	"Nickname":$('#nickname').val(),
		        	"Password":$('#password').val(),
		        	},
		        	success: function()	{
		        		$('#userModal').modal('hide');
		        	}
					});
}