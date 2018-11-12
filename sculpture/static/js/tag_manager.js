/**
 * Tag management, integrated via AJAX calls with a backend.
 *
 * Based on bootstrap-tagmanager by Max Favilli
 * http://welldonethings.com/tags/manager
 *
 * Options that must be set in the call to tagsManager():
 *
 *   addURL: URL to call when adding a tag, taking the tag name as
 *           POST data
 *
 *   baseTagURL: base URL for linking to a tag; the tag id is appended
 *               (with trailing slash)
 *
 *   removeURL: URL to call when removing a tag, taking the tag name
 *              as POST data
 *
 *   typeaheadSource: array of tag names for typeahead
 *
 **/

function getCookie (name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

(function ($) {

    $.fn.tagsManager = function (options, tagToManipulate) {
        var tagManagerOptions = {
            blinkColor1: "#FFFF9C",
            blinkColor2: "#CDE69C",
            prefilled: null,
            preventSubmitOnEnter: true,
            tagClass: '',
            tagCloseIcon: 'x',
            typeaheadSource: null
        };
        $.extend(tagManagerOptions, options);
        var obj = this;
        var objName = obj.attr('name').replace(/[^\w]/g, '_');
        var queuedTag = "";
        var csrftoken = getCookie('csrftoken');
        $.ajaxSetup({
            crossDomain: false,
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });

        var addTag = function (tag) {
            if (!tag || tag.length <= 0) return;
            var tlis = obj.data("tlis");
            var tlid = obj.data("tlid");
            var alreadyInList = false;
            var index = $.inArray(tag, tlis);
            if (-1 != index) {
                alreadyInList = true;
            }
            if (alreadyInList) {
                // Flash the existing tag.
                $("#" + getTagElementId(tlid[index])).stop()
                    .animate({backgroundColor: tagManagerOptions.blinkColor1},
                             100)
                    .animate({backgroundColor: tagManagerOptions.blinkColor2},
                             100)
                    .animate({backgroundColor: tagManagerOptions.blinkColor1},
                             100)
                    .animate({backgroundColor: tagManagerOptions.blinkColor2},
                             100)
                    .animate({backgroundColor: tagManagerOptions.blinkColor1},
                             100)
                    .animate({backgroundColor: tagManagerOptions.blinkColor2},
                             100);
            } else {
                $.post(tagManagerOptions.addURL, {tag: tag}, addTagHTML);
                obj.val("");
            }
        };

        var addTagHTML = function (data) {
            // data is an array of the tag's name and id.
            var tag = data.tag;
            var id = data.id;
            if (!tag || !id) return;
            obj.data("tlis").push(tag);
            obj.data("tlid").push(id);
            var elementId = objName + "_" + id;
            var removeId = objName + "_Remove_" + id;
            var tagURL = tagManagerOptions.baseTagURL + id + "/";
            $('<span>', {id: getTagElementId(id)}).addClass('myTag').append(
                $('<a>', {
                    href: tagURL,
                    text: tag
                }),
                $("<span>&nbsp;&nbsp;</span>"),
                $('<a>', {
                    href: "#",
                    id: removeId,
                    text: tagManagerOptions.tagCloseIcon,
                    title: "Remove"
                }).addClass("myTagRemover").click(function () {
                    return removeTag(id);
                })
            ).insertBefore(obj);
        };

        var getTagElementId = function (tagId) {
            return objName + "_" + tagId;
        };

        var removeTag = function (tagId) {
            $.post(tagManagerOptions.removeURL, {tag_id: tagId}, removeTagHTML);
            return false;
        };

        var removeTagHTML = function (data) {
            var tagId = data.id;
            if (!tagId) return;
            var tlis = obj.data("tlis");
            var tlid = obj.data("tlid");
            var index = $.inArray(tagId, tlid);
            if (-1 != index) {
                $("#" + getTagElementId(tagId)).remove();
                tlis.splice(index, 1);
                tlid.splice(index, 1);
            }
        };

        var setupTypeahead = function () {
            if (tagManagerOptions.typeaheadSource != null) {
                obj.typeahead({source: tagManagerOptions.typeaheadSource});
            }
        };

        var trimTag = function (tag) {
            return $.trim(tag);
        };

        this.each(function () {
            obj.data("tlis", new Array());
            obj.data("tlid", new Array());

            if (tagManagerOptions.typeaheadSource) {
                setupTypeahead();
            }

            obj.change(function (e) {
                e.cancelBubble = true;
                e.returnValue = false;
                e.stopPropagation();
                e.preventDefault();

                var ao = $(".typeahead:visible");
                if (ao[0] != undefined) {
                    var user_input = $(this).data('typeahead').$menu.find(
                        '.active').attr('data-value');
                    user_input = trimTag(user_input);
                    if (queuedTag == obj.val() && queuedTag == user_input) {
                        queuedTag = "";
                        obj.val(queuedTag);
                    } else {
                        addTag(user_input);
                        queuedTag = user_input;
                    }
                } else {
                    var tag = trimTag($(this).val());
                    addTag(tag);
                }
                $(this).focus();
            });

            $.each(tagManagerOptions.prefilled, function (key, data) {
                addTagHTML(data);
            });
        });
    };

})(jQuery);