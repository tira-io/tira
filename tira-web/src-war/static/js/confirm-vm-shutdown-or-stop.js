function submitClosestForm(el) {
  var form = $(el).closest('form')[0];
  button = form.ownerDocument.createElement('input');
  button.style.display = 'none';
  button.type = 'submit';
  form.appendChild(button).click();
  form.removeChild(button);
}
$('[data-toggle="confirm-vm-shutdown"]').confirmation({onConfirm:function(event, el){submitClosestForm(el);}});
$('[data-toggle="confirm-vm-stop"]').confirmation({onConfirm:function(event, el){submitClosestForm(el);}});
