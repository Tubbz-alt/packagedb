/*
	Copyright (c) 2004-2008, The Dojo Foundation All Rights Reserved.
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	see: http://dojotoolkit.org/license for details
*/


dojo._xdResourceLoaded(function(dojo, dijit, dojox){
return {depends: [["provide", "dojox.highlight.languages.pygments._www"],
["require", "dojox.highlight.languages.pygments.xml"],
["require", "dojox.highlight.languages.pygments.html"],
["require", "dojox.highlight.languages.pygments.css"],
["require", "dojox.highlight.languages.pygments.javascript"]],
defineResource: function(dojo, dijit, dojox){if(!dojo._hasResource["dojox.highlight.languages.pygments._www"]){ //_hasResource checks added by build. Do not use _hasResource directly in your code.
dojo._hasResource["dojox.highlight.languages.pygments._www"] = true;
dojo.provide("dojox.highlight.languages.pygments._www");

/* common web-centric languages */
dojo.require("dojox.highlight.languages.pygments.xml");
dojo.require("dojox.highlight.languages.pygments.html");
dojo.require("dojox.highlight.languages.pygments.css");
//dojo.require("dojox.highlight.languages.pygments.django");
dojo.require("dojox.highlight.languages.pygments.javascript");

}

}};});
