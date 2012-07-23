$(document).ready(function () {

    // good-bad-box
    $('#good-button').on('click', on_click_option_button);

    $('#bad-button').on('click', function (e)
    {
        $('#vote-box').show();
        $('#good-bad-box').hide();
    });

    // vote-box
    $('#vote-box').on('click', '.option.btn', on_click_option_button);

    $('input.option').on('keypress', on_keypress_option_input);

    $('#skip-button').on('click', function(e)
    {
        submit({'skip': true});
    });

    $('#submit-button').on('click', submit_option_input);

    $('#cancel-button').on('click', function (e)
    {
        $('#good-bad-box').show();
        $('#vote-box').hide();
    });


});

function submit(params, callback) {
    var url = '/coreexp/save';
    params['_id'] = $('#_id').val();

    if (!callback) {
        callback = function (data) {
            if (data.status == 'ok') {
                location.href = data['next_url'];
            } else {
                unfreeze();
                alert('提交失败');
            }
        }
    }

    freeze();
    $.post(url, params, callback);
}

function freeze()
{
    $('#good-bad-box .btn, #vote-box .btn, #vote-box input')
        .attr('disabled', true);
}

function unfreeze()
{
    $('#good-bad-box .btn, #vote-box .btn, #vote-box input')
        .removeAttr('disabled')
}

function on_click_option_button(e)
{
    var el = $(e.currentTarget);
    var option = el.attr('data-option');
    submit({'option': option});
}

function on_keypress_option_input(e)
{
    if (e.keyCode == 13)
    {
        submit_option_input();
    }
}

function submit_option_input()
{
    var input_el = $('input.option');
    var option = input_el.val();
    if ( option )
    {
        submit({'option': option});
    }
    else
    {
        alert('还没输入解释呢');
        input_el.focus();
    }

}



