dojo._xdResourceLoaded(function(dojo, dijit, dojox){
return {depends: [["provide", "tests._base.Deferred"]],
defineResource: function(dojo, dijit, dojox){if(!dojo._hasResource["tests._base.Deferred"]){ //_hasResource checks added by build. Do not use _hasResource directly in your code.
dojo._hasResource["tests._base.Deferred"] = true;
dojo.provide("tests._base.Deferred");

doh.register("tests._base.Deferred", 
	[

		function callback(t){
			var nd = new dojo.Deferred();
			var cnt = 0;
			nd.addCallback(function(res){
				doh.debug("debug from dojo.Deferred callback");
				return res;
			});
			nd.addCallback(function(res){
				// t.debug("val:", res);
				cnt+=res;
				return cnt;
			});
			nd.callback(5);
			// t.debug("cnt:", cnt);
			t.assertEqual(cnt, 5);
		},

		function callback_extra_args(t){
			var nd = new dojo.Deferred();
			var cnt = 0;
			nd.addCallback(dojo.global, function(base, res){ cnt+=base; cnt+=res; return cnt; }, 30);
			nd.callback(5);
			t.assertEqual(cnt, 35);
		},

		function errback(t){
			var nd = new dojo.Deferred();
			var cnt = 0;
			nd.addErrback(function(val){
				return ++cnt;
			});
			nd.errback();
			t.assertEqual(cnt, 1);
		},

		function callbackTwice(t){
			var nd = new dojo.Deferred();
			var cnt = 0;
			nd.addCallback(function(res){
				return ++cnt;
			});
			nd.callback();
			t.assertEqual(cnt, 1);
			var thrown = false;
			try{
				nd.callback();
			}catch(e){
				thrown = true;
			}
			t.assertTrue(thrown);
		},

		function addBoth(t){
			var nd = new dojo.Deferred();
			var cnt = 0;
			nd.addBoth(function(res){
				return ++cnt;
			});
			nd.callback();
			t.assertEqual(cnt, 1);

			// nd.callback();
			// t.debug(cnt);
			// t.assertEqual(cnt, 1);
		}
	]
);

}

}};});