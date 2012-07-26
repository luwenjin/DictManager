$(document).ready(function (e) {
    var url = URL(location.href);
    if (url.param('error')) {
        $('#info .controls').toggleClass('error', true).text(decodeURIComponent(url.param('error')));
    }
    $('#login input[name=name]').focus();
});