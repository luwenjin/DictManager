$(document).ready(function(){
    init_sidebar_components();
    bind_sidebar_events();
});

function init_sidebar_components() {
    var url = new URL(location.href);
    $("#course_select").val( url.param('course') );
    $('#flaw_select').val( url.param('flaw') );
    $('#editor_select').val( url.param('editor') );
    $('#search_word').val( url.param('search_word') );
}

function bind_sidebar_events() {
    $('#course_select').on('change', on_course_change);
    $('#flaw_select').on('change', on_flaw_change);
    $('#editor_select').on('change', on_editor_change);
    $('#search_word').on('keyup', on_search_word_keyup);
}

function on_course_change(event) {
    var course = $('#course_select').val();
    var url = URL(location.href);
    url.param('course', course);
    location.href = url.toString();
}

function on_flaw_change(event) {
    var flaw = $('#flaw_select').val();
    var url = URL(location.href);
    url.param('flaw', flaw);
    location.href = url.toString();
}

function on_editor_change( event ) {
    var editor = $('#editor_select').val();
    if ( editor == 'all editors' ) {
        editor = '';
    }
    var url = URL(location.href);
    url.param('editor', editor);
    location.href = url.toString();
}

function on_search_word_keyup(event) {
    if ( event.keyCode == 13 ) {
        var url = URL(location.href);
        var word = $("#search_word").val();

        location.href = url.param('search_word', word).toString();
    }
}