

function on_click_option_tag_link(e) {
    var $el = $(e.currentTarget),
        option = $el.attr('data-option'),
        tag = $el.attr('data-tag'),
        id = $el.attr('data-id'),
        url = '/votes/ce/option/tag';

    $.post(url, {'_id': id, 'option': option, 'tag': tag}, function (data) {
        if (data.status === 'ok') {
            $('a', $el.parent()).removeClass('tagged');
            $('.label', $el.parents('li')).removeClass('bad');
            $('.label', $el.parents('li')).removeClass('best');

            if (option) {
                $('a', $el.parent()).removeClass('tagged');
                $el.addClass('tagged');
                $('.label', $el.parents('li')).addClass(tag);
            }
        } else {
            alert(data.message);
        }
    });
}

function on_click_ce_tag_label(e) {
    var $el = $(e.currentTarget),
        id = $el.attr('data-id'),
        tag = $el.attr('data-tag'),
        url = '/votes/ce/tag',
        params = {'_id': id, 'tag': tag};

    if ($el.hasClass('label-success')) {
        params.action = 'del';
    } else {
        params.action = 'add';
    }

    $.post(url, params, function (data) {
        if (data.status === 'ok') {
            if (params.action === 'del') {
                $el.removeClass('label-success');
            } else {
                $el.addClass('label-success');
            }
        } else {
            alert(data.message);
        }
    });
}

function init_nav_link_class() {
    var url = new URL(location.href),
        tags = url.param('tags');

    if (!tags) {
        tags = 'all';
    }

    $('ul.nav a[data-tags]').parent().removeClass('active');

    $('ul.nav a[data-tags]').each(function (idx, el) {
        var $el = $(el),
            data = $el.data('tags');
        if (data === tags) {
            $el.parent().addClass('active');
        }

    });
}

function on_click_nav_link(e) {
    var $a = $(e.target),
        tags = $a.data('tags');

    change_param('tags', tags);
}

$(document).ready(function () {
    init_nav_link_class();

    $('.nav a[data-tags]').click(on_click_nav_link);
    $('.answer').on('click', 'a', on_click_option_tag_link);
    $('td.en').on('click', 'span.label', on_click_ce_tag_label);
    $('a[rel=tooltip]').popover();
});


