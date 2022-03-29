(function(){'use strict';window.addEventListener('load',function(){var c=document.getElementsByClassName('needs-validation');Array.prototype.filter.call(c,function(b){b.addEventListener('submit',function(a){if(b.checkValidity()===false){a.preventDefault();a.stopPropagation()}b.classList.add('was-validated')},false)})},false)})();var selected_type='m5.xlarge';$(function(){updateTypes();$("#arch").change(function(){updateFamily()});$("#region").change(function(){selected_type=$("#types").val();updateTypes()});$("#family").change(function(){updateTypes()});$("#btnquery").click(function(){queryInstance();queryVolume()})});function updateFamily(){var c=$("#region").val();var d=$("#arch").val();$.getJSON("instance/family",{region:c,arch:d},function(b){let familyops="<option value=''>Choose...</option>";let default_family=['m5','m6g'];$.each(b,function(i,a){if(default_family.indexOf(a.name)>=0){familyops+="<option selected value='"+a.name+"'>"+a.description+": "+a.name+"</option>";updateTypes(a.name)}else{familyops+="<option value='"+a.name+"'>"+a.description+": "+a.name+"</option>"}});$("#family").html(familyops)})};function updateTypes(c){var d=$("#region").val();var e=$("#arch").val();var c=(typeof c==='undefined')?$("#family").val():c;$.getJSON("instance/types",{region:d,arch:e,family:c},function(b){let typeops="<option value=''>Choose...</option>";let unmatch=true;$.each(b,function(i,a){if(a.instanceType==selected_type){typeops+="<option selected value='"+a.instanceType+"'>"+a.instanceType+"</option>";unmatch=false}else{typeops+="<option value='"+a.instanceType+"'>"+a.instanceType+"</option>"}});$("#types").html(typeops);if(unmatch){$("#types").prop("selectedIndex",1)}})};function queryInstance(){var f=$("#region").val();var g=$("#operation").val();var h=$("#types").val();$.getJSON("product/instance",{region:f,type:h,op:g},function(a){if("listPrice"in a){$("#insprice").html(a.listPrice.pricePerUnit.currency+" "+a.listPrice.pricePerUnit.value.toFixed(2));$("#insunit").html(a.listPrice.unit);$("#insdate").html(a.listPrice.effectiveDate);$("#insfamily").html(a.productMeta.instanceFamily);$("#instenan").html(a.productMeta.tenancy);$("#insloca").html(a.productMeta.location);$("#insurl").attr('href',a.productMeta.introduceUrl);$("#tbdetail").show();$("#detailurl").attr('href','detail?region='+f+'&type='+h)}else{$("#insprice").html('unknown');$("#insunit").html('Month');$("#insdate").html(null);$("#insfamily").html('Not Found');$("#instenan").html(null);$("#insloca").html(null);$("#insurl").attr('href','');$("#tbdetail").hide()};var b='';$.each(a.hardwareSpecs,function(k,v){b+="<tr><td>"+k+"</td><td>"+v+"</td></tr>"});$("#tbhardware").html(b);var c='';$.each(a.softwareSpecs,function(k,v){c+="<tr><td>"+k+"</td><td>"+v+"</td></tr>"});$("#tbsoftware").html(c);var d='';$.each(a.instanceSotrage,function(k,v){d+="<tr><td>"+k+"</td><td>"+v+"</td></tr>"});$("#tbinstorage").html(d);var e='';$.each(a.productFeature,function(k,v){e+="<tr><td>"+k+"</td><td>"+v+"</td></tr>"});$("#tbfeature").html(e)})};function queryVolume(){var c=$("#region").val();var d=$("#voltypes").val();var e=$("#volsize").val();$.getJSON("product/volume",{region:c,type:d,size:e},function(a){var b='';$.each(a.productSpecs,function(k,v){b+="<tr><td>"+k+"</td><td>"+v+"</td></tr>"});$("#tbvolspec").html(b);$("#volprice").html(a.listPrice.pricePerUnit.currency+" "+a.listPrice.pricePerUnit.value.toFixed(2));$("#volunit").html(a.listPrice.unit);$("#voldate").html(a.listPrice.effectiveDate);$("#voltype").html(a.productMeta.volumeType);$("#usagetype").html(a.productMeta.usagetype);$("#volmedia").html(a.productMeta.storageMedia);$("#volurl").attr('href',a.productMeta.introduceUrl)})};