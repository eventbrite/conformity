$(document).ready(function() {
    var output_div = $('#auto-toc-for-auto-doc-container');
    if (output_div) {
        var max_depth = 100;
        if (output_div.attr('data:max-depth')) {
            var max_depth_attr = parseInt(output_div.attr('data:max-depth'));
            if (max_depth_attr) {
                max_depth = max_depth_attr;
            }
        }

        var make_toc = function(parent_search, parent_output, depth) {
            var parent_ul = document.createElement('ul');
            parent_ul = $(parent_ul);
            if (depth === 0) {
                parent_ul.attr('class', 'simple');
            }
            var add = false;

            parent_search.children('dl').each(function(i, element) {
                element = $(element);
                var cls = element.attr('class');
                if (cls === 'module' || cls === 'class' || cls === 'function' || cls === 'method') {
                    add = true;
                    var id = element.find('dt').attr('id');

                    var li = document.createElement('li');
                    li = $(li);
                    li.append('<a class="reference internal" href="#' + id + '">' + cls + ' ' + id + '</a>');
                    parent_ul.append(li);

                    if (cls === 'class' && depth < max_depth) {
                        make_toc(element.find('dd'), li, depth + 1);
                    }
                }
            });

            if (add) {
                parent_output.append(parent_ul);
            }
        };

        make_toc($('div.section'), output_div, 1);
    }
});
