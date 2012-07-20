$(document).ready(function(){
    bind_tokens_events();
});

function bind_tokens_events() {
    $('#add_foreign_link').on('click', on_add_foreign_link_click);
    $('ul.chinese').on('focus', 'input[name]', on_chinese_input_focus);

    $('#resource_tabs').on('click', on_resource_tabs_click);
//    $('#resource_tabs a[data-target=#freq_ngram_pane]').on('shown', on_freq_ngram_pane_shown);
//    $('#resource_tabs a[data-target=#freq_20k_pane]').on('shown', on_freq_20k_pane_shown);

    $('#freq_ngram_pane #lemmas_input').on('keyup', on_lemmas_input_keyup);
    $('#freq_ngram_pane table').on('change', 'input[type=checkbox]', on_freq_result_toggle);
    $('#freq_ngram_pane #freq_sum').on('click', on_freq_sum_click);

    $('#freq_20k_pane #word_input').on('keyup', on_word_input_keyup);
    $('#freq_20k_pane table').on('click', '.freq a',  on_20k_freq_click);

    $("#courses").on('focus', 'input[name=course]', on_course_input_focus);

}

// handlers =========================
function on_add_foreign_link_click(event) {
    var html = $('#_foreign_input').html();
    $('#foreign ul').append(html);
}

function on_chinese_input_focus(event) {
    var ul = $('ul.chinese');
    var current_li = $(event.target).parent();
    var li_list = $('ul.chinese li');

    if ( li_list.length > 0 && li_list.eq(li_list.length-1).is(current_li) ) {
        var li_html = $('#_chinese_li').html();
        ul.append( li_html );
    }
}



function on_resource_tabs_click(event) {
    $(event.target).tab('show');
}

function on_lemmas_input_keyup(event) {
    var table = $("#freq_ngram_pane table");

    if (event.keyCode == 13) {
        var input = $('#lemmas_input');
        input.attr('disabled', true);
        $('tbody tr', table).remove();

        $.get('/tokens/list_ngram_freq', {'lemmas': input.val()}, function(data) {
            input.attr('disabled', false);
            var view = {
                'freq_list': data
            };
            var template = $('#_freq_ngram_table_tr').html();
            var html = Mustache.render(template, view);
            $('tbody', table).html(html);
        });
    }
}

function on_freq_result_toggle(event) {
    var freq_sum = 0;
    $('#freq_ngram_pane table input[type=checkbox]:checked').each(function(i, node) {
        var freq_td = $(node).parent().parent().children('.freq');

        console.log(freq_td);
        freq_sum += parseInt(freq_td.html());
    });
    $('#freq_sum').text(freq_sum);
}

function on_freq_sum_click(event) {
    var freq = $('#freq_sum').text();
    $('#freq_ngram_input').val(freq).focus().select();
}

function on_freq_ngram_pane_shown(event) {
    var foreign = $('input[name=foreign]').val();
    $('#lemmas_input').val(foreign).focus().select();
}

function on_freq_20k_pane_shown(event) {
    var input = $('#word_input');
    if ( !input.val() ) {
        input.val($('#foreign input[name=foreign.text]').eq(0).val());
        do_search_freq_20k();
    }
}

function on_word_input_keyup(event) {
    if (event.keyCode == 13) {
        do_search_freq_20k();
    }
}

function do_search_freq_20k() {
    var table = $("#freq_20k_pane table");
    var input = $('#word_input');
    input.attr('disabled', true);
    $('tbody tr', table).remove();

    var word = input.val();
    $.get('/tokens/list_20k_freq', {'word': word}, function(data) {
        input.attr('disabled', false);
        var template = $('#_freq_20k_table_tr').html();
        var html = Mustache.render(template, {freq_list: data});
        $('tbody', table).html(html);

        $('tbody tr', table).each(function(idx, item){
            var $tr = $(item);
            var $word_td = $('td.word', $tr);
            if ( $word_td.text() == word ) {
                $word_td.html('<b>'+word+'</b>')
            }
        });
    });
}


function on_20k_freq_click(event) {
    var count = $(event.target).text();
    $('#freq_20k_input').val(count);
}

function on_course_input_focus(event) {
    var current_input = $(event.target);
    var input_list = $('#courses input[name=course]');
    var html = $('#_course_input').html();
    if ( input_list.length > 0 && input_list.eq(input_list.length-1).is(current_input) ) {
        current_input.after(html);
    }
}