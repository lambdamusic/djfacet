
// OLD VERSION



function disable_UI(message, id_location, color){
	if (!id_location) var id_location = "#cs";	// the main DIV
	if (!color) var color = "#2B3856";
	// if (!message) var message = "processing query.... <br /><br /><img src='/dj_app_media/paul/i/g.gif' alt='loading data' />"
	if (!message) var message = "processing query...."
	$("#blockUImessage1").empty().append(message);
	$(id_location).block({	message: $('#blockUImessage1'), 
							css: { padding: '10px', fontsize: '5px'}, 
							overlayCSS : {opacity: '.3', filter:'alpha(opacity=30)', backgroundColor : color }	//backgroundColor : '#2B3856'
						}); 
}

function enable_UI(id_location){
	if (!id_location) var id_location = "#cs"; 
	$(id_location).unblock(); 
}





function explain_results(){
	var resulttype = what_result_type();
	$("#blockUImessage2").load("explain_results?resulttype=" + resulttype);
	$("#cs").block({ 
					message: $('#blockUImessage2'), 
					centerY: 0, 
					css: { padding: '10px', top: '10%', left: '', width: '50%', textAlign: 'left' } , 
					overlayCSS : {opacity: '.3', backgroundColor : '#2B3856'} 
					}); 
	$('.blockOverlay').attr('title','Click to unblock').click(function () { 
																  $("#cs").unblock(); 
																});
}





// called when a column header is clicked on to order the result list
function change_ordering(ordering){
	old_ordering = $("#active_ordering").val();
	if (!(old_ordering == ordering)) {
		$("#active_ordering").val(ordering);
		reload_results(1, ordering)
	} else {  //the back end checks whether it's  an annotation or not
		$("#active_ordering").val("-" + ordering);
		reload_results(1, "-" + ordering)
	}
}


function what_result_type(){
	return $("li.ui-state-active").attr('id');	
}



function isFacetedCountActive() {
	return True;
	// var test = $("#refresh_facets").attr('value');
	// if (test == 'True') {
	//	return true;
	// }
	// else {
	//	return false;
	// }
}


// resets all the flags used to determine whether to call the backend or not!
function resetFacetFlags() {
	$("#accordion h5").each(function (i) {
		$(this).parent().removeClass("values_are_updated");
	});
}






// time= the delay time	  -- flag= whether 'updateFacetValues' should Disable the UI too...
function delayUpdateFacetValues(time, flag) {
	if (!time) var time = 400;
	if (!flag) var flag = false;

	// this is a hidden field that contains a Flag (set at initial loading time) indicating whether refresh is automatic
	if (isFacetedCountActive()) {
		// hack for IE
		var myfun = function() { updateFacetValues(flag); };
		setTimeout(myfun, time);
	}  else {
		enable_UI();
	}
		
}



// toggleClass("highlight");

// 2010-07-22: refreshes the facet values available..
// flag is used to determine whether the update is run by itself, or after updating the result list 
// in the first case, we need to block the screen; in the second one, that is managed in 'ajax_update1'
function OLD_updateFacetValues(flag) {
	if (!flag) var flag = false;
	var resulttype = what_result_type();
	var activefacet = $("#accordion h5.ui-state-active").parent(); // the <LI> element
	var is_tree_facet = $("#accordion h5.ui-state-active").parent().hasClass('istreefacet')
	var activefacetid = $("#accordion h5.ui-state-active").parent().attr('id'); // the unique ID
	var divelement = $("#accordion h5.ui-state-active").next(); // where the list is contained
	var activegroup = $("#accordion h5.ui-state-active").parent().parent().prev().attr('id');
	
	if (activefacetid && !(activefacet.hasClass("values_are_updated"))) {
		
		activefacet.addClass("values_are_updated");	 // so that it doesn't get reloaded unless necessary
				
		if (flag) {
			$(divelement).add_loading_icon();
			// var message = "updating facets.... <br /><br /><img src='/dj_app_media/paul/i/g.gif' alt='loading data' />"		
			var message = "updating facets...."		
			disable_UI(message);
		}

		$.get('update_facet',
			 { resulttype : resulttype, activefacet: activefacetid, activegroup: activegroup},
				  function(data){
						$(divelement).empty().append(data); 
						
						add_onclick_events();  // clicking items selects them..
						activate_filtering();  //prepares the filter box 
						
						if (is_tree_facet) {   // 2010-11-12
							$("#tree_" + activefacetid).treeview({
									// url: "source.php",
									animated: "fast",
									collapsed: true,
									control: "#treecontrol_" + activefacetid
									});
						} 
						
						
						if (true) {
							enable_UI();
						}				
				  }
	   );					
	}	
	else {
		// alert("here");
		enable_UI();
	}	
}






function updateFacetValues() {
	var activefacet = $("#facets_list h4.ui-state-active") // the <H4> element
	var is_tree_facet = $("#facets_list h4.ui-state-active").hasClass('istreefacet')
	var activefacetid = $("#facets_list h4.ui-state-active").attr('id'); // the unique ID
	var divelement = $("#facets_list h4.ui-state-active").next(); // where the list is contained
	var rec_num = $("#rec_num").html();
	
	
	if (activefacetid && !(activefacet.hasClass("values_are_updated"))) {		
		activefacet.addClass("values_are_updated");	 // so that it doesn't get reloaded unless necessary
		var list_ids = new Array();
		$("#active_filters li").each( function(index) {
			list_ids.push(this.id);
		});

		$.get('update_facet',
			 { activefacet: activefacetid, totitems : rec_num , active_filters: list_ids},
				  function(data){
						$(divelement).empty().append(data); 
			
				  }
	   );					
	}	
	else {
		//alert("here");
		// nothing to do!
	}
}




// ONLOAD FUNCTION
// ....................... do the make_next_element collapasable behaviour manually....

$(document).ready(function() {
	$("#facets_list").accordion({ header: 'h4', collapsible: true , active: false, fillSpace: true});

	$("#facets_list ").bind( "accordionchange", function(event, ui) {
	  updateFacetValues(50, true); 
	}); 
});





