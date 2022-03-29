(function($){function isCollapsable(a){return a instanceof Object&&Object.keys(a).length>0}function isUrl(a){var b=/^(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;return b.test(a)}function json2html(a,b){var c='';if(typeof a==='string'){a=a.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');if(isUrl(a))c+='<a href="'+a+'" class="json-string">'+a+'</a>';else c+='<span class="json-string">"'+a+'"</span>'}else if(typeof a==='number'){c+='<span class="json-literal">'+a+'</span>'}else if(typeof a==='boolean'){c+='<span class="json-literal">'+a+'</span>'}else if(a===null){c+='<span class="json-literal">null</span>'}else if(a instanceof Array){if(a.length>0){c+='[<ol class="json-array">';for(var i=0;i<a.length;++i){c+='<li>';if(isCollapsable(a[i])){c+='<a href class="json-toggle"></a>'}c+=json2html(a[i],b);if(i<a.length-1){c+=','}c+='</li>'}c+='</ol>]'}else{c+='[]'}}else if(typeof a==='object'){var d=Object.keys(a).length;if(d>0){c+='{<ul class="json-dict">';for(var e in a){if(a.hasOwnProperty(e)){c+='<li>';var f=b.withQuotes?'<span class="json-string">"'+e+'"</span>':e;if(isCollapsable(a[e])){c+='<a href class="json-toggle">'+f+'</a>'}else{c+=f}c+=': '+json2html(a[e],b);if(--d>0)c+=',';c+='</li>'}}c+='</ul>}'}else{c+='{}'}}return c}$.fn.jsonViewer=function(e,f){f=f||{};return this.each(function(){var d=json2html(e,f);if(isCollapsable(e))d='<a href class="json-toggle"></a>'+d;$(this).html(d);$(this).off('click');$(this).on('click','a.json-toggle',function(){var a=$(this).toggleClass('collapsed').siblings('ul.json-dict, ol.json-array');a.toggle();if(a.is(':visible')){a.siblings('.json-placeholder').remove()}else{var b=a.children('li').length;var c=b+(b>1?' items':' item');a.after('<a href class="json-placeholder">'+c+'</a>')}return false});$(this).on('click','a.json-placeholder',function(){$(this).siblings('a.json-toggle').click();return false});if(f.collapsed==true){$(this).find('a.json-toggle').click()}})}})(jQuery);