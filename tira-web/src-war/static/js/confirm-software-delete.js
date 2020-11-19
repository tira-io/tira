$('#softwares [data-toggle="confirm-software-delete"]').confirmation({onConfirm:function(event, el){
  form = $(el).closest('form');
  form.attr('action', function(i, val){
    return val + 'delete/';
  });
  form = form[0];
  button = form.ownerDocument.createElement('input');
  button.style.display = 'none';
  button.type = 'submit';
  form.appendChild(button).click();
  form.removeChild(button);
}});
