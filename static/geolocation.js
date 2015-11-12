/*
@filename: geolocation.js
@description: This piece of JS code implements the HTML5 geolocation
@author: Daniele Di Mitri
@date: 12-11-2015
*/

// Default Lat, Long (of the OU)
var def_lat = 50; //50.8779846;
var def_long = 5; //5.9582749;

geoFindMe(); // call it at pageload 

function geoFindMe() {
	if (navigator.geolocation) {
	 navigator.geolocation.getCurrentPosition(getPosition,error);         
	} 
	
	else { //In case browser doesn't support geolocation set the default values 
	    user_lat  = def_lat;
	    user_long = def_long; 
	}
	
}

function getPosition(position) {
  user_lat  = position.coords.latitude;
  user_long = position.coords.longitude; 
  $("#latitude-input").attr("value",user_lat);
  $("#longitude-input").attr("value",user_long);
}

function error(err) {
  console.warn('ERROR(' + err.code + '): ' + err.message);
};