/*
	Copyright (c) 2004-2008, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


dojo._xdResourceLoaded(function(dojo, dijit, dojox){
return {depends: [["provide", "dojox.jsonPath"],
["require", "dojox.jsonPath.query"]],
defineResource: function(dojo, dijit, dojox){if(!dojo._hasResource["dojox.jsonPath"]){ //_hasResource checks added by build. Do not use _hasResource directly in your code.
dojo._hasResource["dojox.jsonPath"] = true;
dojo.provide("dojox.jsonPath");
dojo.require("dojox.jsonPath.query");

}

}};});
