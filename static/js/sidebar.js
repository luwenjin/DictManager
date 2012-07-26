function init_sidebar_components() {
    var url = new URL(location.href);
    $("#course_select").val(url.param('course'));
    $('#flaw_select').val(url.param('flaw'));
    $('#editor_select').val(url.param('editor'));
    $('#search_word').val(decodeURIComponent(url.param('search_word')));
}


function on_course_change(event) {
    var course = $('#course_select').val(),
        url = URL(location.href);

    url.param('course', course);
    location.href = url.toString();
}


function on_flaw_change(event) {
    var flaw = $('#flaw_select').val(),
        url = URL(location.href);

    url.param('flaw', flaw);
    location.href = url.toString();
}


function on_editor_change(event) {
    var editor = $('#editor_select').val(),
        url = URL(location.href);

    if (editor === 'all editors') {
        editor = '';
    }
    url.param('editor', editor);
    location.href = url.toString();
}


function on_search_word_keyup(event) {
    var url = URL(location.href),
        word = $("#search_word").val();

    if (event.keyCode === 13) {
        location.href = url.param('search_word', word).toString();
    }
}


function bind_sidebar_events() {
    $('#course_select').on('change', on_course_change);
    $('#flaw_select').on('change', on_flaw_change);
    $('#editor_select').on('change', on_editor_change);
    $('#search_word').on('keyup', on_search_word_keyup);
}


$(document).ready(function () {
    init_sidebar_components();
    bind_sidebar_events();
});