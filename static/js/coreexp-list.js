$(document).ready(function () {
    $('.answer').on('click', 'a', on_click_tag_link);
});

function on_click_tag_link(e) {
    var el = $(e.currentTarget);
    var option = el.attr('data-option');
    var tag = el.attr('data-tag');
    var id = el.attr('data-id')

    var url = '/coreexp/option/tag'
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


