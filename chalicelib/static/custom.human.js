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

var selected_type = 'm5.xlarge';

//jquery入口函数 
$(function () {    
    // 初始化 Instance Types 列表
    updateTypes();
	$("#arch").change(function () {
		//update instance family
        updateFamily();
	});

	$("#region").change(function () {
        selected_type = $("#types").val();
		updateTypes();
	});

	$("#family").change(function () {
        // selected_type = null;
		updateTypes();
	});

	$("#btnquery").click(function () {
		queryInstance();
		queryVolume();
	});
});


//update instance family
function updateFamily() {
    var region = $("#region").val();
    var arch = $("#arch").val();
    $.getJSON("instance/family", { region: region, arch: arch },
        function (result) {
            let familyops = "<option value=''>Choose...</option>";
            let default_family = ['m5','m6g'];
            $.each(result, function (i, item) {
                if ( default_family.indexOf(item.name) >= 0 ) { familyops += "<option selected value='" + item.name + "'>" + item.description + ": " + item.name + "</option>"; updateTypes(item.name);}
                else { familyops += "<option value='" + item.name + "'>" + item.description + ": " + item.name + "</option>"; }                
            });
            $("#family").html(familyops);
        }
    );
};

//update instance types
function updateTypes(family) {
	var region = $("#region").val();
	var arch = $("#arch").val();
	var family = (typeof family === 'undefined') ? $("#family").val() : family;
	$.getJSON(
		"instance/types",
		{ region: region, arch: arch, family: family },
		function (result) {
			let typeops = "<option value=''>Choose...</option>";
            let unmatch = true;
			$.each(result, function (i, item) {
                if ( item.instanceType == selected_type ) { typeops += "<option selected value='" + item.instanceType + "'>" + item.instanceType + "</option>"; unmatch=false; }
                else { typeops += "<option value='" + item.instanceType + "'>" + item.instanceType + "</option>"; }
			});
			$("#types").html(typeops);
            if ( unmatch ) { $("#types").prop("selectedIndex", 1) }; 
            //$('#types option:first').attr('selected','selected') //设置第一项选中
		}
	);
};


function queryInstance() {
    var region = $("#region").val();
    var operat = $("#operation").val();
	var type = $("#types").val();
	//invoke instance api
	$.getJSON("product/instance", { region: region, type: type, op: operat },
		function (result) {
			//update instance price card
			if ("listPrice" in result) {
				$("#insprice").html(result.listPrice.pricePerUnit.currency + " " + result.listPrice.pricePerUnit.value.toFixed(2));
				$("#insunit").html(result.listPrice.unit);
				$("#insdate").html(result.listPrice.effectiveDate);
				$("#insfamily").html(result.productMeta.instanceFamily);
				$("#instenan").html(result.productMeta.tenancy);
				$("#insloca").html(result.productMeta.location);
				$("#insurl").attr('href', result.productMeta.introduceUrl);
				$("#tbdetail").show();
				$("#detailurl").attr('href', 'detail?region=' + region + '&type=' + type);
			} else {
				$("#insprice").html('unknown');
				$("#insunit").html('Month');
				$("#insdate").html(null);
				$("#insfamily").html('Not Found');
				$("#instenan").html(null);
				$("#insloca").html(null);
				$("#insurl").attr('href', '');
				$("#tbdetail").hide();
			};

			var tabhw = '';
			$.each(result.hardwareSpecs, function (k, v) {
				tabhw += "<tr><td>" + k + "</td><td>" + v + "</td></tr>";
			});
			$("#tbhardware").html(tabhw);

			var tabsw = '';
			$.each(result.softwareSpecs, function (k, v) {
				tabsw += "<tr><td>" + k + "</td><td>" + v + "</td></tr>";
			});
			$("#tbsoftware").html(tabsw);

			var tabisto = '';
			$.each(result.instanceSotrage, function (k, v) {
				tabisto += "<tr><td>" + k + "</td><td>" + v + "</td></tr>";
			});
			$("#tbinstorage").html(tabisto);

			var tabfeat = '';
			$.each(result.productFeature, function (k, v) {
				tabfeat += "<tr><td>" + k + "</td><td>" + v + "</td></tr>";
			});
			$("#tbfeature").html(tabfeat);
		});
};

function queryVolume() {
	var region = $("#region").val();
	var type = $("#voltypes").val();
	var size = $("#volsize").val();
	//invoke volume api
	$.getJSON("product/volume", { region: region, type: type, size: size },
		function (result) {
			var tabvol = '';
			$.each(result.productSpecs, function (k, v) {
				tabvol += "<tr><td>" + k + "</td><td>" + v + "</td></tr>";
			});
			$("#tbvolspec").html(tabvol);

			//update volume price card
			$("#volprice").html(result.listPrice.pricePerUnit.currency + " " + result.listPrice.pricePerUnit.value.toFixed(2));
			$("#volunit").html(result.listPrice.unit);
			$("#voldate").html(result.listPrice.effectiveDate);
			$("#voltype").html(result.productMeta.volumeType);
			$("#usagetype").html(result.productMeta.usagetype);
			$("#volmedia").html(result.productMeta.storageMedia);
			$("#volurl").attr('href', result.productMeta.introduceUrl);
		});
};
