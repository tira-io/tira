$('#runs [data-toggle="confirm-software-delete"]').confirmation({onConfirm:function(event, el){
//  $(el).closest('form').submit();
// since jQuery .submit() does not trigger onSubmit event which is just bad design
  var form = $(el).closest('form')[0];
  var button = form.ownerDocument.createElement('input');
  button.style.display = 'none';
  button.type = 'submit';
  form.appendChild(button).click();
  form.removeChild(button);
}});
