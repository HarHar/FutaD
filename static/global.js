function isNumber (o) {
  return ! isNaN (o-0) && o !== null && o.replace(/^\s\s*/, '') !== "" && o !== false;
}

var time = 500;
if ($('#noanims').val() == 'True') {time = 0};

function yes() {
	$.get('/yes');
}

function no() {
	$.get('/no');
}

function diffsrs() {
	$('#diffEp').hide();
	$.get('/resizeTo_230');
	$('#diffSrs').slideDown(time);
}

function diffep() {
	$('#diffSrs').hide();
	$.get('/resizeTo_150');
	$('#diffEp').slideDown(time);
}

function doChangeEp() {
	if (isNumber($('#epn').val())) {
		$.get('/changeEp_' + $('#epn').val());
	} else {
		$('#epn').attr('value', 'not number');
	}
}

function doDiffSrs(el) {
	$.get('/changeSrs_' + $(el).text());
}

function cancelChEp() {
	$('#diffEp').slideUp(time, function() {$.get('/resizeTo_130')})
}

function cancelChSrs() {
	$('#diffSrs').slideUp(time, function() {$.get('/resizeTo_130')})
}