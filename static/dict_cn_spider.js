// 英文
var foreign = $("#word-key").html();

// 分段
var foreign_seg = $("#word-key").attr('seg');

// 音标
var phonetic = $('span.yinbiao').eq(0).text();

// 多种变形
var transforms_a = $("span.w-change a");
var transforms = {};
transforms_a.each(function(i,a){
    var desc = $(a).attr('desc');
    var spell = $(a).text();
    transforms[desc] = spell;
});

var exp_nodes = $('#exp-block li, #exp-block div.exp');
// 含意列表
var meanings = [];
// 例句们
var sentences = {};
var meaning = null;
exp_nodes.each(function(i, node){
    if ( node.tagName == 'LI' ) {
        meaning = $('strong', node).text();
        meanings.push(meaning);
        sentences[meaning] = []
    }
    if ( node.tagName == 'DIV' ) {
        var en_html = $('.one-en', node).html();
        var cn = $('.one-ch', node).html();
        sentences[meaning].push({
            en_html: en_html,
            cn: cn
        });
    }
});
console.log(meanings);
console.log(sentences);
