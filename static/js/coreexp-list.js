$(document).ready(function () {
    $('.answer').on('click', 'a', on_click_option_tag_link);
    $('td.en').on('click', 'span.label', on_click_ce_tag_label);
});

function on_click_option_tag_link(e) {
    var el = $(e.currentTarget);
    var option = el.attr('data-option');
    var tag = el.attr('data-tag');
    var id = el.attr('data-id')

    var url = '/coreexp/option/tag';
    $.post(url, {'_id': id, 'option': option, 'tag': tag}, function(data){
        if (data.status == 'ok'){
            $('a', el.parent()).removeClass('tagged');
            $('.label', el.parents('li')).removeClass('bad');
            $('.label', el.parents('li')).removeClass('best');

            if (option) {
                $('a', el.parent()).removeClass('tagged');
                el.addClass('tagged');
                $('.label', el.parents('li')).addClass(tag);
            }
        } else {
            alert(data.message);
        }
    });
}

function on_click_ce_tag_label(e) {
    var el = $(e.currentTarget);
    var id = el.attr('data-id');
    var tag = el.attr('data-tag');

    var url = '/coreexp/tag';
    var params = {'_id': id, 'tag': tag};
    if ( el.hasClass('label-success')) {
        params['action'] = 'del';
    } else {
        params['action'] = 'add';
    }

    $.post(url, params, function(data)
    {
        if (data.status == 'ok'){
            if (params['action'] == 'del'){
                el.removeClass('label-success');
            } else {
                el.addClass('label-success');
            }
        } else {
            alert(data.message);
        }
    });


}


