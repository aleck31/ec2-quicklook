// Empty JS for your own code to be here

// form-validation js,
// disabling form submissions if there are invalid fields
(function () {
    'use strict';
  
    window.addEventListener('load', function () {
      // Fetch all the forms we want to apply custom Bootstrap validation styles to
      var forms = document.getElementsByClassName('needs-validation');
  
      // Loop over them and prevent submission
      Array.prototype.filter.call(forms, function (form) {
        form.addEventListener('submit', function (event) {
          if (form.checkValidity() === false) {
            event.preventDefault();
            event.stopPropagation();
          }
  
          form.classList.add('was-validated')
        }, false)
      })
    }, false)
  })();


//jquery入口函数 
  $(function(){
    var region='us-east-1';
    var arch='x86_64';
    var family='m5';

    $("#arch").change(function(){      
      var arch=$("#arch").val(); 
      var region=$("#region").val();
      //update instance family
      $.getJSON("instance/family",{region:region,arch:arch},  
      function(result){
        var familyops='';
        $.each(result, function(i, item){
          familyops+="<option value='"+item.name+"'>"+item.description+": "+item.name+"</option>";
        });
        $("#family").html(familyops);
        //设置第一项选中
        // $('#family option:first').attr('selected','selected');
      });
      //update instance types
    });

    $("#region").change(function(){
      var region=$("#region").val();
      var arch=$("#arch").val(); 
      var family=$("#family").val(); 
      //update instance types
      $.getJSON("instance/types",{region:region,arch:arch,family:family}, 
      function(result){
        var typeops='';
        $.each(result, function(i, item){
          typeops+="<option value='"+result[i].instanceType+"'>"+result[i].instanceType+"</option>";
        });
        $("#types").html(typeops)
      });
    });

    $("#family").change(function(){
      var family=$("#family").val(); 
      var region=$("#region").val();
      var arch=$("#arch").val(); 
      //update instance types
      $.getJSON("instance/types",{region:region,arch:arch,family:family},  
      function(result){
        var typeops='';
        $.each(result, function(i, item){
          typeops+="<option value='"+item.instanceType+"'>"+item.instanceType+"</option>";
        });
        $("#types").html(typeops)
      });
    });

    $("#btnquery").click(function(){
      queryInstance();
      queryVolume();
    });

  });


function queryInstance(){
  var region=$("#region").val();
  var type=$("#types").val(); 
  var op=$("#operation").val(); 
  //invoke instance api
  $.getJSON("product/instance",{region:region,type:type,op:op},  
  function(result){
    var tabhw='';
    $.each(result.hardwareSpecs, function(k, v){
      tabhw+="<tr><td>"+k+"</td><td>"+v+"</td></tr>";
    });
    $("#tbhardware").html(tabhw);

    var tabsw='';
    $.each(result.softwareSpecs, function(k, v){
      tabsw+="<tr><td>"+k+"</td><td>"+v+"</td></tr>";
    });
    $("#tbsoftware").html(tabsw);

    var tabisto='';
    $.each(result.instanceSotrage, function(k, v){
      tabisto+="<tr><td>"+k+"</td><td>"+v+"</td></tr>";
    });
    $("#tbinstorage").html(tabisto);

    var tabfeat='';
    $.each(result.productFeature, function(k, v){
      tabfeat+="<tr><td>"+k+"</td><td>"+v+"</td></tr>";
    });
    $("#tbfeature").html(tabfeat); 

    //update instance price card
    $("#insprice").html(result.listPrice.pricePerUnit.currency+" "+result.listPrice.pricePerUnit.value.toFixed(2));
    $("#insunit").html(result.listPrice.unit);
    $("#insdate").html(result.listPrice.effectiveDate);
    $("#insfamily").html(result.productMeta.instanceFamily);
    $("#instenan").html(result.productMeta.tenancy);
    $("#insloca").html(result.productMeta.location);
    $("#insurl").attr('href',result.productMeta.introduceUrl);

  });
};

function queryVolume(){
  var region=$("#region").val();
  var type=$("#voltypes").val(); 
  var size=$("#volsize").val(); 
  //invoke volume api
  $.getJSON("product/volume",{region:region,type:type,size:size},  
  function(result){
    var tabvol='';
    $.each(result.productSpecs, function(k, v){
      tabvol+="<tr><td>"+k+"</td><td>"+v+"</td></tr>";
    });
    $("#tbvolspec").html(tabvol);

    //update volume price card
    $("#volprice").html(result.listPrice.pricePerUnit.currency+" "+result.listPrice.pricePerUnit.value.toFixed(2));
    $("#volunit").html(result.listPrice.unit);
    $("#voldate").html(result.listPrice.effectiveDate);
    $("#voltype").html(result.productMeta.volumeType);
    $("#usagetype").html(result.productMeta.usagetype);
    $("#volmedia").html(result.productMeta.storageMedia);
    $("#volurl").attr('href',result.productMeta.introduceUrl);
  });
};
