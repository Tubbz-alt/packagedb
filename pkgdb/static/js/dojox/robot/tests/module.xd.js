dojo._xdResourceLoaded(function(dojo, dijit, dojox){
return {depends: [["provide", "dojox.robot.tests.module"],
["require", "dojox.robot.tests.robotml"]],
defineResource: function(dojo, dijit, dojox){if(!dojo._hasResource["dojox.robot.tests.module"]){ //_hasResource checks added by build. Do not use _hasResource directly in your code.
dojo._hasResource["dojox.robot.tests.module"] = true;
dojo.provide("dojox.robot.tests.module");

try{
	dojo.require("dojox.robot.tests.robotml");
}catch(e){
	doh.debug(e);
}


}

}};});