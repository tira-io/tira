$(".tira-world-publish form, .tira-user-blinding form").submit(function(e) {
  e.preventDefault();
  var url = $(this).attr('action');
  $.ajax({
    // Uncomment the following to send cross-domain cookies:
    //xhrFields: {withCredentials: true},
    url: url,
    type: 'POST',
    context: $(this).parent(),
    cache: false
  }).done(function () {
    var visible = $(this).find("form:visible");
    var hidden = $(this).find("form:hidden");
    visible.hide();
    hidden.css("display", "inline");
  }).fail(function (error, statusMessage) {
    errorPopover(this, 'right', error.statusText);
  });
});
