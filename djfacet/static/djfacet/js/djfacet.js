
// DJFACET js functions




// ONLOAD FUNCTION <$(document).ready(function()..> included in base.html 




function toggle_facets() {
	$(".openclosefacet").click(function() {
		$(this).parent().next().slideToggle("slow");
		permute_plusminus($(this));
		});
}


function toggle_history() {
	$(".openclosehistory").click(function() {
		$(this).parent().next().slideToggle("slow");
		permute_plusminus($(this));
		});
}	
	

function permute_plusminus(el){
		
	if (el.text() == "+") {
		el.text("-");
		el.addClass('closeFacet');
	} 	
	else {
		$(el).text("+");
		el.removeClass('closeFacet');
		}
}	


function close_facets() {
	$(".openclosefacet").click();
}

function close_history() {
	$(".openclosehistory").click();
}






function updateFacetValues(span_openclosefacet) {
	
	// eg: TEST it with $(".openclosefacet").first().parent().next().children("ul").html("<p>cioa</p>")
	
	var resulttype  = $("#active_restype").val();
	var newurl_stub  = $("#active_urlstub").val();
	var activefacetid = span_openclosefacet.parent().parent().attr('id')
	
	if (!(span_openclosefacet.hasClass("values_are_updated"))) {		

		disable_UI("Updating available filters...");
		
		span_openclosefacet.addClass("values_are_updated");	 // so that it doesn't get reloaded unless necessary
		var facet_title = span_openclosefacet.parent();
		span_openclosefacet.parent().next().remove();

		// WHY USING THIS ACTIVE FILTERS?
		// var list_ids = new Array();
		// $("#active_filters li").each( function(index) {
		// 	list_ids.push(this.id);
		// });
		
		var ajax_url = "update_facet?activefacet=" + activefacetid + "&resulttype=" + resulttype + newurl_stub

		$.get(ajax_url, function(data){
						$(facet_title).after(data); 
						enable_UI();			
				  		});		
	}	
	else {
		//alert("here");
		// test
		// $(divelement).empty().append("<p>Ciao!</p><p>Ciao!2</p>");
	}
	
}



// STILL NOT USED, but it works


function disable_UI(message, id_location, color){
	if (!id_location) var id_location = "#djfacet_maindiv";	// the main DIV
	if (!color) var color = "#2B3856";
	// if (!message) var message = "processing query.... <br /><br /><img src='/dj_app_media/paul/i/g.gif' alt='loading data' />"
	if (!message) var message = "processing query...."
	$("#blockUImessage1").val(message);
	$(id_location).block({	message: $('#blockUImessage1').val(), 
							css: { padding: '10px', fontsize: '5px'}, 
							overlayCSS : {opacity: '.3', filter:'alpha(opacity=30)', backgroundColor : color }	//backgroundColor : '#2B3856'
						}); 
}

function enable_UI(id_location){
	if (!id_location) var id_location = "#djfacet_maindiv"; 
	$(id_location).unblock(); 
}


