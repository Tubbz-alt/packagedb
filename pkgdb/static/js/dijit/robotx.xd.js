/*
	Copyright (c) 2004-2008, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


dojo._xdResourceLoaded(function(dojo, dijit, dojox){
return {depends: [["provide", "dijit.robotx"],
["require", "dijit.robot"],
["require", "dojo.robotx"]],
defineResource: function(dojo, dijit, dojox){if(!dojo._hasResource["dijit.robotx"]){ //_hasResource checks added by build. Do not use _hasResource directly in your code.
dojo._hasResource["dijit.robotx"] = true;
dojo.provide("dijit.robotx");
dojo.require("dijit.robot");
dojo.require("dojo.robotx");
dojo.experimental("dijit.robotx");
(function(){
var __updateDocument = doh.robot._updateDocument;

dojo.mixin(doh.robot,{
	_updateDocument: function(){
		__updateDocument();
		var win = (dojo.doc.parentWindow || dojo.doc.defaultView);
		if(win["dijit"]){
			dijit.registry = win.dijit.registry;
		}
	}
});

})();

}

}};});