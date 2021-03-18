
function reloadData() {
    $('#reload-website-data-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"GET",
        url: "/tira/admin/reload-data",
        data:{},
        success: function( data )
        {
            $('#reload-website-data-icon').html(' <i class="fas fa-check"></i>')
        }
    })
}

function submitCreateVmForm(){
    $('#create-vm-form-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"POST",
        url: "/tira/admin/create-vm",
        data:{
            bulk_create:$('#id_bulk_create').val(),
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            action: 'post'
        },
        success: function( data )
        {
            document.getElementById("create-vm-from").reset();
            $('#create-vm-from-icon').html('');
            $('#create-vm-form-error').text(data['create_vm_form_error']);
            $('#create-vm-form-results').text(data)
        }
    })
}

function addTiraAdminHandlers() {
    $('#reload-website-data').click(function() {reloadData()})
    $('#create-vm-from').submit(function(e) {
        e.preventDefault();
        submitCreateVmForm()
    })
}

