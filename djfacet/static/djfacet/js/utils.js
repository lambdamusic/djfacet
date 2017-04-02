/* creator: michelepasin */


/*** Temporary text filler function. Remove when deploying template. ***/
var gibberish=["This is just some filler text", "Sometimes some gibberish may mean more than what you think", "Amore non amato amar perdona"]
function filltext(words){
	var output = "";
	for (var i=0; i<words; i++) 
		output = output + (gibberish[Math.floor(Math.random()*3)]+" ");
		return output;
}

function addGibberish(number, location) {
	var stuff = filltext(number);
	$(location).empty().append(stuff);
}




/*
generic functions for jquery operations
*/

function updateDiv(divname, ajaxcall) {
    $.get(ajaxcall,
   		 { },
              function(data){
                 $("#" + divname).append(data);
              }
   );  
}

function clear_and_updateDiv(divname, ajaxcall) {
    $.get(ajaxcall,
   		 { },
              function(data){
                 $("#" + divname).empty().append(data);
              }
   );  
}




