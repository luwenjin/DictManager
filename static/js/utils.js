function change_param(key, val) {
    var url = URL(location.href);
    url.param(key, val);
    location.href = url.toString();
}

function change_page(n) {
    change_param('page', n);
}

function change_path(path) {
    var url = URL(location.href);
    url.path(path);
    location.href = url.toString();
}