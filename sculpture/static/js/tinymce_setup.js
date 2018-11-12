function CustomFileBrowser(field_name, url, type, win) {
    tinyMCE.activeEditor.windowManager.open({
        file: window.__filebrowser_url + '?pop=2&type=' + type,
        width: 820,  // Your dimensions may differ - toy around with them!
        height: 500,
        resizable: "yes",
        scrollbars: "yes",
        inline: "yes",  // This parameter only has an effect if you use the inlinepopups plugin!
        close_previous: "no"
    }, {
        window: win,
        input: field_name,
        editor_id: tinyMCE.selectedInstance.editorId
    });
    return false;
}

if (typeof tinyMCE != 'undefined') {

    tinyMCE.init({

        // main settings
        mode : "specific_textareas",
        editor_selector : "mceEditor",
        theme: "advanced",
        language: "en",
        dialog_type: "window",
        editor_deselector : "mceNoEditor",

        // general settings
        width: '700',
        //height: '350',
        indentation : '10px',
        fix_list_elements : true,
        relative_urls: false,
        remove_script_host : true,
        accessibility_warnings : false,
        object_resizing: false,
        entity_encoding: "raw",
        forced_root_block: "p",
        remove_trailing_nbsp: true,

        // callbackss
        file_browser_callback: "CustomFileBrowser",

        // theme_advanced
        theme_advanced_toolbar_location: "top",
        theme_advanced_toolbar_align: "left",
        theme_advanced_statusbar_location: "bottom",
        theme_advanced_buttons1: "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,|,link,unlink,|,code,",
        theme_advanced_buttons2: "formatselect, styleselect,|, forecolor, backcolor,|,bullist,numlist,table,|,image,media,|,undo,redo,",
        theme_advanced_buttons3: "",
        theme_advanced_path: false,
        theme_advanced_blockformats: "p,h1,h2,h3,h4,pre",
        theme_advanced_styles: "[all] clearfix=clearfix;[p] small=small;[img] Image left-aligned=img_left;[img] Image left-aligned (nospace)=img_left_nospacetop;[img] Image right-aligned=img_right;[img] Image right-aligned (nospace)=img_right_nospacetop;[img] Image Block=img_block;[img] Image Block (nospace)=img_block_nospacetop;[div] column span-2=column span-2;[div] column span-4=column span-4;[div] column span-8=column span-8",
        theme_advanced_resizing : true,
        theme_advanced_resize_horizontal : true,
        theme_advanced_resizing_use_cookie : true,
        theme_advanced_styles: "Image left-aligned=img_left;Image left-aligned (nospace)=img_left_nospacetop;Image right-aligned=img_right;Image right-aligned (nospace)=img_right_nospacetop;Image Block=img_block",
        advlink_styles: "intern=internal;extern=external",

        // plugins
        plugins: "inlinepopups,tabfocus,searchreplace,fullscreen,advimage,advlink,paste,media,table",
        advimage_update_dimensions_onchange: true,

        // remove MS Word's inline styles when copying and pasting.
        paste_remove_spans: true,
        paste_auto_cleanup_on_paste : true,
        paste_remove_styles: true,
        paste_remove_styles_if_webkit: true,
        paste_strip_class_attributes: true,
		
		valid_elements : "@[id|class|style|title|dir<ltr?rtl|lang|xml::lang],"
		    + "a[rel|rev|charset|hreflang|tabindex|accesskey|type|"
		    + "name|href|target|title|class],strong/b,em/i,strike,u,"
		    + "#p[style],-ol[type|compact],-ul[type|compact],-li,br,img[longdesc|usemap|"
		    + "src|border|alt=|title|hspace|vspace|width|height|align],-sub,-sup,"
		    + "-blockquote,-table[border=0|cellspacing|cellpadding|width|frame|rules|"
		    + "height|align|summary|bgcolor|background|bordercolor],-tr[rowspan|width|"
		    + "height|align|valign|bgcolor|background|bordercolor],tbody,thead,tfoot,"
		    + "#td[colspan|rowspan|width|height|align|valign|bgcolor|background|bordercolor"
		    + "|scope],#th[colspan|rowspan|width|height|align|valign|scope],caption,-div,"
		    + "-span,-code,-pre,address,-header,-h1,-h2,-h3,-h4,-h5,-h6,hr[size|noshade],-font[face"
		    + "|size|color],dd,dl,dt,cite,abbr,acronym,del[datetime|cite],ins[datetime|cite],"
		    + "object[classid|width|height|codebase|*],param[name|value|_value],embed[type|width"
		    + "|height|src|*],map[name],area[shape|coords|href|alt|target],bdo,"
		    + "button,col[align|char|charoff|span|valign|width],colgroup[align|char|charoff|span|"
		    + "valign|width],dfn,fieldset,form[action|accept|accept-charset|enctype|method],"
		    + "input[accept|alt|checked|disabled|maxlength|name|readonly|size|src|type|value],"
		    + "kbd,label[for],legend,noscript,optgroup[label|disabled],option[disabled|label|selected|value],"
		    + "q[cite],samp,select[disabled|multiple|name|size],small,"
		    + "textarea[cols|rows|disabled|name|readonly],tt,var,big",

	});

}
