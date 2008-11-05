/*
	Copyright (c) 2004-2008, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


dojo._xdResourceLoaded(function(dojo, dijit, dojox){
return {depends: [["provide", "dojox.sketch"],
["require", "dojox.xml.DomParser"],
["require", "dojox.sketch.UndoStack"],
["require", "dojox.sketch.Figure"],
["require", "dojox.sketch.Toolbar"]],
defineResource: function(dojo, dijit, dojox){if(!dojo._hasResource["dojox.sketch"]){ //_hasResource checks added by build. Do not use _hasResource directly in your code.
dojo._hasResource["dojox.sketch"] = true;
dojo.provide("dojox.sketch");
dojo.require("dojox.xml.DomParser");
dojo.require("dojox.sketch.UndoStack");
dojo.require("dojox.sketch.Figure");
dojo.require("dojox.sketch.Toolbar");

}

}};});
