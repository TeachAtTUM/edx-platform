(function ($) {
    'use strict';

    $.fn.extend({
        allLoaded: function (fn) {
            // Adapted from http://stackoverflow.com/a/35777807/592820
            var $elems = this;
            var waiting = this.length;

            var handler = function () {
                --waiting;
                if (!waiting) {
                    fn.call(window);
                }
                this.unbind(handler);
            };

            return $elems.load(handler);
        }
    });

    $(function () {
        var $iframeContainer = $('#iframeContainer'),
            $iframes = $iframeContainer.find('iframe'),
            redirectUrl = $iframeContainer.data('redirect-url');

        if ($iframes.length === 0) {
            window.location = redirectUrl;
        }

        $iframes.allLoaded(function () {
            window.location = redirectUrl;
        });
    });
})(jQuery);
