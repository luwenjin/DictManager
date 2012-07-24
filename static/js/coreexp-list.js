$(document).ready(function () {
    $('.answer').on('click', 'a', on_click_tag_link);
    $('td.en').on('click', 'a', on_click_close_button);
});

function on_click_tag_link(e) {
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

function on_click_close_button(e) {
    var el = $(e.currentTarget);
    var id = el.attr('data-id');
    var current_tag = el.attr('data-tag');

    var url = '/coreexp/tag';
    var params = {'_id': id, 'action': 'replace'};
    if (current_tag != 'closed')
    {
        params['tag'] = 'closed';
    }
    else
    {
        params['tag'] = null;
    }

    el.attr('disabled', true);
    $.post(url, params, function(data)
    {
        if (data.status == 'ok'){
            el.attr('data-tag', params['tag']);
            if (params['tag']){
                el.text('已关闭')
            } else {
                el.text('开放中')
            }

        } else {
            alert(data.message);
        }
        el.removeAttr('disabled')
    });


}


