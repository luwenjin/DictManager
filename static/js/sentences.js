$(document).ready(function(){
    bind_sentences_events();
});

var token_id = $('#sentences_form input[name=token_id]').val();

function bind_sentences_events() {
    $('#sentences_form table a.btn.all').on('click', on_all_btn_click);
    $('#sentences_form table a.btn.course').on('click', on_course_btn_click);
}

// commmon functions
function update_btn_class(btn, ban) {
    if ( ban ) {
        btn.toggleClass('btn-success', false);
    } else {
        btn.toggleClass('btn-success', true);
    }

}


// handlers =========================
function on_all_btn_click(event) {
    var btn = $(event.target);
    var course = 'ALL';
    var ban = 0;
    if ( btn.hasClass('btn-success') ) {
        ban = 1;
    }
    var sentence_id = $('input[name=sentence_id]', btn.parent().parent()).val();
    console.log( token_id, sentence_id, course, ban);

    var btns = $('.btn', btn.parent().parent());
    btns.attr('disabled', true);
    $.post('/sentences', {token_id: token_id, sentence_id: sentence_id, course: course, ban:ban}, function(data){
        console.log(data);
        if ( data.status == 'ok' ) {
            update_btn_class(btns, data.ban);
        }
        btns.attr("disabled", false);
    });
}

function on_course_btn_click(event) {
    var btn = $(event.target);
    var course = btn.text();
    var ban = 0;
    if ( btn.hasClass('btn-success') ) {
        ban = 1;
    }
    var sentence_id = $('input[name=sentence_id]', btn.parent()).val();
    console.log( token_id, sentence_id, course, ban);
    btn.attr('disabled', true);
    $.post('/sentences', {token_id: token_id, sentence_id: sentence_id, course: course, ban:ban}, function(data){
        console.log(data);
        if ( data.status == 'ok' ) {
            update_btn_class(btn, data.ban);
        }
        btn.attr("disabled", false);
    });
}

