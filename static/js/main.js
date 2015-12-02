!function(global, $, undefined) {
    'use strict';

    var fetchPreview = function(form) {
        var previewURL = form.find(".preview-url").val();
        window.location.hash = "url=" + previewURL;

        form.removeClass("has-error").removeClass("has-success");
        $.getJSON( "/get_preview", {url: previewURL}, function(json) {
            form.find(".result").text(json.preview);
            form.addClass("has-success");
        }).fail(function(jqxhr, textStatus, error) {
            var errorText;
            if (error)
                errorText = jqxhr.responseJSON.message;
            else
                errorText = "Failed to connect to Advocate (server down?)";
            form.find(".error").text(errorText);
            form.addClass("has-error");
        });
    };

    var handlePreviewFormSubmit = function(evt) {
        fetchPreview($(evt.target));
        evt.preventDefault();
        return true;
    };

    $(function () {
        $(".preview-form").on("submit", handlePreviewFormSubmit);

        var mainPreview = $("#main-preview");
        var hash = window.location.hash.substring(1);
        var url;
        if(hash.indexOf("url=") === 0) {
            url = hash.substring("url=".length);
        } else {
            url = "http://www.example.com/";
        }
        mainPreview.find(".preview-url").val(url);
        fetchPreview(mainPreview);
    });
}(window, jQuery, undefined);
