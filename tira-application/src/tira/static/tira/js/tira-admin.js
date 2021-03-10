
function reloadData() {
    $('#tira-admin-reload-data-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
    $.ajax({
        type:"GET",
        url: "/tira/admin/reload-data",
        data:{},
        success: function( data )
        {
            $('#tira-admin-reload-data-icon').html(' <i class="fas fa-check"></i>')
        }
    })
}

function submitCreateVmForm(){
    $('#tira-admin-create-vm-icon').html(' <div uk-spinner="ratio: 0.5"></div>')
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
            document.getElementById("tira-admin-vm-create-form").reset();
            $('#tira-admin-create-vm-icon').html();
            $('#create-vm-form-error').text(data['create_vm_form_error']);
            $('#create-vm-form-results').text(data)
        }
    })
}

function addTiraAdminHandlers() {
    $('#tira-admin-reload-data').click(function() {reloadData()})
    $('#tira-admin-vm-create-form').submit(function(e) {
        e.preventDefault();
        submitCreateVmForm()
    })
}

